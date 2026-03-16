import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


TMP_DIR = Path("codeql-tmp")
RESULTS_DIR = Path("codeql-results")

# Python only for now
LANGUAGE = "python"
SARIF_FORMAT = "sarifv2.1.0"


def run_cmd(cmd: List[str], cwd: Path | None = None) -> Tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def download_zip(owner: str, repo: str, sha: str, out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{owner}/{repo}/archive/{sha}.zip"

    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()

    with open(out_zip, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def extract_zip(zip_path: Path, extract_to: Path) -> Path:
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)

    subdirs = [p for p in extract_to.iterdir() if p.is_dir()]
    if len(subdirs) != 1:
        raise RuntimeError(
            f"Expected exactly one extracted top-level folder in {extract_to}, got {len(subdirs)}"
        )
    return subdirs[0]


def safe_delete(path: Path) -> None:
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def create_codeql_db(scan_dir: Path, db_dir: Path) -> None:
    # db dir must not exist
    safe_delete(db_dir)
    db_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "codeql",
        "database",
        "create",
        str(db_dir),
        f"--language={LANGUAGE}",
        "--build-mode=none",
        f"--source-root={scan_dir.resolve()}",
        "--overwrite",
        "--threads=0",
    ]

    code, out, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(
            f"CodeQL database create failed for {scan_dir}\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        )


def analyze_codeql_db(db_dir: Path, output_sarif: Path) -> None:
    output_sarif.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "codeql",
        "database",
        "analyze",
        str(db_dir),
        f"--format={SARIF_FORMAT}",
        f"--output={output_sarif.resolve()}",
        "--threads=0",
        "--no-print-diagnostics-summary",
        "--no-print-metrics-summary",
        "--sarif-category=python",
    ]
    # No query spec: use the standard default queries for the language.

    code, out, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(
            f"CodeQL database analyze failed for {db_dir}\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        )


def load_sarif_results(sarif_path: Path) -> List[Dict[str, Any]]:
    if not sarif_path.exists():
        return []

    with open(sarif_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results: List[Dict[str, Any]] = []
    for run in data.get("runs", []):
        results.extend(run.get("results", []))
    return results


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/")


def result_key(result: Dict[str, Any]) -> Tuple:
    """
    Prefer partialFingerprints from SARIF.
    Fallback to a stable-ish tuple if fingerprints are missing.
    """
    partial_fps = result.get("partialFingerprints") or {}
    if partial_fps:
        return (
            "fingerprint",
            tuple(sorted((str(k), str(v)) for k, v in partial_fps.items())),
        )

    rule_id = result.get("ruleId", "")

    locations = result.get("locations") or []
    if locations:
        phys = (locations[0].get("physicalLocation") or {})
        artifact = phys.get("artifactLocation") or {}
        region = phys.get("region") or {}

        uri = normalize_path(artifact.get("uri", ""))
        start_line = region.get("startLine")
    else:
        uri = ""
        start_line = None

    message = result.get("message") or {}
    message_text = message.get("text", "")

    return ("fallback", rule_id, uri, start_line, message_text)


def diff_sarif_results(
    base_results: List[Dict[str, Any]],
    merged_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    base_keys = {result_key(r) for r in base_results}
    introduced = [r for r in merged_results if result_key(r) not in base_keys]
    return introduced


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def scan_pr(owner: str, repo: str, pr_number: int, base_sha: str, merge_commit_sha: str) -> Dict[str, Any]:
    work_dir = TMP_DIR / f"{owner}__{repo}__pr_{pr_number}"
    result_dir = RESULTS_DIR / f"{owner}__{repo}" / f"pr_{pr_number}"

    base_zip = work_dir / "base.zip"
    merged_zip = work_dir / "merged.zip"

    base_extract = work_dir / "base_extract"
    merged_extract = work_dir / "merged_extract"

    base_db = work_dir / "codeql_base_db"
    merged_db = work_dir / "codeql_merged_db"

    base_sarif = result_dir / "codeql_base.sarif"
    merged_sarif = result_dir / "codeql_merged.sarif"
    introduced_json = result_dir / "codeql_introduced_issues.json"
    summary_json = result_dir / "codeql_summary.json"

    safe_delete(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        download_zip(owner, repo, base_sha, base_zip)
        download_zip(owner, repo, merge_commit_sha, merged_zip)

        base_dir = extract_zip(base_zip, base_extract)
        merged_dir = extract_zip(merged_zip, merged_extract)

        create_codeql_db(base_dir, base_db)
        create_codeql_db(merged_dir, merged_db)

        analyze_codeql_db(base_db, base_sarif)
        analyze_codeql_db(merged_db, merged_sarif)

        base_results = load_sarif_results(base_sarif)
        merged_results = load_sarif_results(merged_sarif)

        introduced = diff_sarif_results(base_results, merged_results)
        save_json(introduced_json, introduced)

        summary = {
            "tool": "codeql",
            "language": LANGUAGE,
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "base_sha": base_sha,
            "merge_commit_sha": merge_commit_sha,
            "base_findings": len(base_results),
            "merged_findings": len(merged_results),
            "introduced_findings": len(introduced),
            "base_sarif": str(base_sarif),
            "merged_sarif": str(merged_sarif),
            "introduced_issues_path": str(introduced_json),
            "status": "success",
        }
        save_json(summary_json, summary)
        return summary

    finally:
        safe_delete(work_dir)


def main() -> None:
    if len(sys.argv) != 6:
        print(
            "Usage: python codeql-scan.py <owner> <repo> <pr_number> <base_sha> <merge_commit_sha>"
        )
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    pr_number = int(sys.argv[3])
    base_sha = sys.argv[4]
    merge_commit_sha = sys.argv[5]

    try:
        summary = scan_pr(owner, repo, pr_number, base_sha, merge_commit_sha)
        print(json.dumps(summary, indent=2))
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()