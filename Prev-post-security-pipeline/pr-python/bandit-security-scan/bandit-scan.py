import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


TMP_DIR = Path("bandit-tmp")
RESULTS_DIR = Path("bandit-results")


def run_cmd(cmd: List[str], cwd: Path | None = None) -> Tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def download_zip(owner: str, repo: str, sha: str, out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/{owner}/{repo}/archive/{sha}.zip"
    r = requests.get(url, stream=True, timeout=60)
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
        raise RuntimeError(f"Expected exactly one extracted top-level folder in {extract_to}, got {len(subdirs)}")

    return subdirs[0]


def run_bandit(scan_dir: Path, output_json: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "bandit",
        "-r",
        ".",
        "-f",
        "json",
        "-o",
        str(output_json.resolve()),
        "--exit-zero",
        "-x",
        "tests,venv,.venv,build,dist,__pycache__"
    ]

    code, out, err = run_cmd(cmd, cwd=scan_dir)
    if code != 0:
        raise RuntimeError(f"Bandit failed\nSTDOUT:\n{out}\nSTDERR:\n{err}")


def load_bandit_results(json_path: Path) -> List[Dict[str, Any]]:
    if not json_path.exists():
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("results", [])


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/")


def issue_key(issue: Dict[str, Any]) -> Tuple:
    return (
        normalize_path(issue.get("filename", "")),
        issue.get("test_id", ""),
        issue.get("issue_text", ""),
    )


def diff_bandit_results(
    base_results: List[Dict[str, Any]],
    merged_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    base_keys = {issue_key(x) for x in base_results}
    introduced = [x for x in merged_results if issue_key(x) not in base_keys]
    return introduced


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def safe_delete(path: Path) -> None:
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def scan_pr(owner: str, repo: str, pr_number: int, base_sha: str, merge_commit_sha: str) -> Dict[str, Any]:
    work_dir = TMP_DIR / f"{owner}__{repo}__pr_{pr_number}"
    result_dir = RESULTS_DIR / f"{owner}__{repo}" / f"pr_{pr_number}"

    base_zip = work_dir / "base.zip"
    merged_zip = work_dir / "merged.zip"
    base_extract = work_dir / "base_extract"
    merged_extract = work_dir / "merged_extract"

    base_json = result_dir / "bandit_base.json"
    merged_json = result_dir / "bandit_merged.json"
    introduced_json = result_dir / "introduced_issues.json"
    summary_json = result_dir / "summary.json"

    safe_delete(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. 下载两个 zip
        download_zip(owner, repo, base_sha, base_zip)
        download_zip(owner, repo, merge_commit_sha, merged_zip)

        # 2. 解压
        base_dir = extract_zip(base_zip, base_extract)
        merged_dir = extract_zip(merged_zip, merged_extract)

        # 3. 分别跑 Bandit
        run_bandit(base_dir, base_json)
        run_bandit(merged_dir, merged_json)

        # 4. 读取结果
        base_results = load_bandit_results(base_json)
        merged_results = load_bandit_results(merged_json)

        # 5. diff
        introduced = diff_bandit_results(base_results, merged_results)
        save_json(introduced_json, introduced)

        summary = {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "base_sha": base_sha,
            "merge_commit_sha": merge_commit_sha,
            "base_findings": len(base_results),
            "merged_findings": len(merged_results),
            "introduced_findings": len(introduced),
            "introduced_issues_path": str(introduced_json),
            "status": "success",
        }
        save_json(summary_json, summary)
        return summary

    finally:
        safe_delete(work_dir)


def main():
    if len(sys.argv) != 6:
        print("Usage: python bandit-scan.py <owner> <repo> <pr_number> <base_sha> <merge_commit_sha>")
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