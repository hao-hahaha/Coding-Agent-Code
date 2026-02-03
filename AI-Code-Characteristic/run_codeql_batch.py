import os
import traceback
import argparse
import json

BASE_REPORT_DIR = "codeql-reports"
NUM_SHARDS = 10              # 总 shard 数
MAX_REPOS_PER_RUN = 5        # 每次最多跑几个 repo（可改）


parser = argparse.ArgumentParser()
parser.add_argument(
    "--shard-id",
    type=int,
    required=True,
    help="Shard ID for this worker (0 ~ NUM_SHARDS-1)"
)
parser.add_argument(
    "--max-repos",
    type=int,
    default=MAX_REPOS_PER_RUN,
    help="Max repos to process in this run"
)
args = parser.parse_args()

SHARD_ID = args.shard_id
MAX_REPOS_PER_RUN = args.max_repos

assert 0 <= SHARD_ID < NUM_SHARDS, "Invalid shard-id"

# =======================
# IMPORT YOUR FUNCTIONS
# =======================

with open("artifacts/repo_pr_records_clean.json", "r", encoding="utf-8") as f:
    repo_pr_records_clean = json.load(f)

def extract_repo_records(api_url, pr_list):

    repo_url = api_url.replace("https://api.github.com", "https://github.com")
    if "/repos/" in repo_url:
        repo_url = repo_url.replace("/repos/", "/")
        
    records = []
    for item in pr_list:
        print(item)
        records.append({
            'html_url': item['html_url'],
            'merge_commit_sha': item['merge_commit_sha'],
            'pr_order': item['pr_order_in_repo'],
            'language': item['language']
        })
    return repo_url, records

CODEQL_QUERY_SUITES = {
    "C/C++": "cpp-security-and-quality.qls",
    "C#": "csharp-security-and-quality.qls",
    "Java/Kotlin": "java-security-and-quality.qls",
    "JavaScript/TypeScript": "javascript-security-and-quality.qls",
    "Python": "python-security-and-quality.qls",
    "Ruby": "ruby-security-and-quality.qls",
    "Rust": "rust-security-and-quality.qls",
}

CODEQL_CLI_LANG_MAP = {
    "C/C++": "cpp",
    "C#": "csharp",
    "Java/Kotlin": "java",
    "JavaScript/TypeScript": "javascript",
    "Python": "python",
    "Ruby": "ruby",
    "Rust": "rust",
}

CODEQL_BUILD_MODE = {
    "C/C++": "none",
    "C#": "none",
    "Java/Kotlin": "none",
    "JavaScript/TypeScript": "none",
    "Python": "none",
    "Ruby": "none",
    "Rust": "none",
}

def select_build_mode(pr_languages: list[str]) -> str:
    for lang in pr_languages:
        if CODEQL_BUILD_MODE.get(lang) == "none":
            return "none"
    return "autobuild"


def run_scan_pipeline(repo_url, records):
    import subprocess
    import os
    import shutil

    CODEQL_BIN = "/Users/guanhao/codeql-home/codeql/codeql"
    BASE_REPORT_DIR = "codeql-reports"

    parts = repo_url.rstrip("/").split("/")
    repo_folder_name = f"{parts[-2]}_{parts[-1]}"

    for pr in records:
        sha = pr["merge_commit_sha"]
        pr_id = pr["pr_order"]
        pr_languages = pr.get("language", [])

        pr_langs = [
            l for l in pr_languages
            if l in CODEQL_CLI_LANG_MAP and l != "GitHub Actions"
        ]

        if not pr_langs:
            print(f"\n⏭️  [PR {pr_id}] Skipped (no CodeQL-supported languages)")
            continue

        print(f"\n🚀 [PR {pr_id}] SHA: {sha}")
        print(f"   🧠 PR languages (CodeQL): {pr_langs}")

        report_dir = os.path.join(
            BASE_REPORT_DIR, repo_folder_name, f"PR_{pr_id}"
        )
        os.makedirs(report_dir, exist_ok=True)

        source_dir = f"temp_source_pr_{pr_id}"
        os.makedirs(source_dir, exist_ok=True)

        try:
            # ===== checkout merge commit (once per PR) =====
            subprocess.run(
                f"git init && "
                f"git remote add origin {repo_url} && "
                f"git fetch --depth 1 origin {sha} && "
                f"git checkout FETCH_HEAD",
                shell=True,
                cwd=source_dir,
                check=True,
                capture_output=True,
            )

            # ===== language-level isolation =====
            for pr_lang in pr_langs:
                cli_lang = CODEQL_CLI_LANG_MAP[pr_lang]
                query_suite = CODEQL_QUERY_SUITES[pr_lang]

                db_dir = f"temp_db_pr_{pr_id}_{cli_lang}"
                db_dir_abs = os.path.abspath(db_dir)

                print(f"\n   🏗️  [{pr_lang}] Creating DB ({cli_lang})")

                build_mode = CODEQL_BUILD_MODE.get(pr_lang, "none")

                try:
                    # --- DB create ---
                    subprocess.run(
                        f"{CODEQL_BIN} database create {db_dir_abs} "
                        f"--source-root=. "
                        f"--language={cli_lang} "
                        f"--build-mode={build_mode}",
                        shell=True,
                        cwd=source_dir,
                        check=True,
                    )

                    output_path = os.path.join(
                        report_dir,
                        f"{cli_lang}_security_report.sarif"
                    )

                    print(f"   🔍 [{pr_lang}] Analyzing...")

                    # --- analyze ---
                    subprocess.run(
                        f"{CODEQL_BIN} database analyze "
                        f"{db_dir_abs} "
                        f"{query_suite} "
                        f"--format=sarif-latest "
                        f"--output={os.path.abspath(output_path)}",
                        shell=True,
                        check=True,
                    )

                    print(f"   ✅ [{pr_lang}] Report: {output_path}")

                except Exception as lang_err:
                    # ⚠️ language-level failure is tolerated
                    print(
                        f"   ⚠️  [{pr_lang}] Failed, skipped.\n"
                        f"       Reason: {lang_err}"
                    )

                finally:
                    # --- always clean DB dir ---
                    if os.path.exists(db_dir_abs):
                        shutil.rmtree(db_dir_abs)

        except Exception as pr_err:
            # ❌ only catastrophic PR-level failures land here
            print(f"   ❌ Error preparing PR {pr_id}: {pr_err}")

        finally:
            print("   🧹 Cleaning up source workspace...")
            if os.path.exists(source_dir):
                shutil.rmtree(source_dir)

    print(f"\n✨ All scans for {repo_folder_name} completed.")



# =======================
# MAIN LOOP
# =======================
os.makedirs(BASE_REPORT_DIR, exist_ok=True)

repo_items = list(repo_pr_records_clean.items())
total = len(repo_items)

done = 0
skipped = 0
failed = 0
processed = 0

print("=" * 70)
print(f"🚀 CodeQL Batch Runner")
print(f"   Shard        : {SHARD_ID} / {NUM_SHARDS}")
print(f"   Max repos    : {MAX_REPOS_PER_RUN}")
print(f"   Total repos  : {total}")
print("=" * 70)

for idx, (api_repo_url, pr_records) in enumerate(repo_items):

    # ---------- shard filter ----------
    if idx % NUM_SHARDS != SHARD_ID:
        continue

    # ---------- batch size limit ----------
    if processed >= MAX_REPOS_PER_RUN:
        print("\n🛑 Reached max repos for this run, stopping.")
        break

    # ---------- repo naming ----------
    repo_url, records = extract_repo_records(api_repo_url, pr_records)

    parts = repo_url.rstrip("/").split("/")
    repo_folder_name = f"{parts[-2]}_{parts[-1]}"
    repo_report_path = os.path.join(BASE_REPORT_DIR, repo_folder_name)
    done_marker = os.path.join(repo_report_path, "_DONE")

    print(f"\n📦 Processing repo: {repo_folder_name}")

    # ---------- skip completed ----------
    if os.path.exists(done_marker):
        print("⏭️  Skipped (already completed)")
        skipped += 1
        continue

    os.makedirs(repo_report_path, exist_ok=True)

    # ---------- run CodeQL ----------
    try:
        print("🚀 Running CodeQL...")
        run_scan_pipeline(repo_url, records)

        # mark done
        with open(done_marker, "w") as f:
            f.write("ok\n")

        print("✅ Completed")
        done += 1
        processed += 1

    except Exception as e:
        failed += 1
        print("❌ Failed")
        print("   Reason:", str(e))
        traceback.print_exc()

print("\n" + "=" * 70)
print("🎉 Batch finished")
print(f"✅ Completed repos : {done}")
print(f"⏭️  Skipped repos   : {skipped}")
print(f"❌ Failed repos    : {failed}")
print(f"📦 Total checked   : {processed}")
print("=" * 70)