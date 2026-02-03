# run_codeql_python.py
# ================================
# Python-only CodeQL pipeline
# Input: python_pr_df
# ================================

import os
import shutil
import subprocess
import pandas as pd
import traceback

# ========= CONFIG =========
CODEQL_BIN = "/Users/guanhao/codeql-home/codeql/codeql"
BASE_REPORT_DIR = "codeql-reports"

PYTHON_CLI_LANG = "python"
PYTHON_QUERY_SUITE = "python-security-extended.qls"
PYTHON_BUILD_MODE = "none"


# ========= helpers =========
def api_to_clone_url(api_url: str) -> str:
    return api_url.replace(
        "https://api.github.com/repos/",
        "https://github.com/"
    )


def repo_slug_from_url(repo_url: str) -> str:
    parts = repo_url.rstrip("/").split("/")
    return f"{parts[-2]}_{parts[-1]}"


# ========= core: run CodeQL for ONE PR =========
def run_python_codeql_for_pr(
    repo_url: str,
    merge_sha: str,
    pr_id: str,
    report_dir: str,
):
    source_dir = f"_tmp_source_{pr_id}"
    db_dir = f"_tmp_db_{pr_id}"

    try:
        # ---- checkout merge commit ----
        os.makedirs(source_dir, exist_ok=True)

        subprocess.run(
            f"git init && "
            f"git remote add origin {repo_url} && "
            f"git fetch --depth 1 origin {merge_sha} && "
            f"git checkout FETCH_HEAD",
            shell=True,
            cwd=source_dir,
            check=True,
            capture_output=True,
        )

        db_dir_abs = os.path.abspath(db_dir)

        print(f"    🏗️  Creating Python DB")

        subprocess.run(
            f"{CODEQL_BIN} database create {db_dir_abs} "
            f"--source-root=. "
            f"--language={PYTHON_CLI_LANG} "
            f"--build-mode={PYTHON_BUILD_MODE}",
            shell=True,
            cwd=source_dir,
            check=True,
        )

        output_path = os.path.join(
            report_dir,
            "python_security_report.sarif"
        )

        print(f"    🔍 Analyzing Python")

        subprocess.run(
            f"{CODEQL_BIN} database analyze "
            f"{db_dir_abs} "
            f"{PYTHON_QUERY_SUITE} "
            f"--format=sarif-latest "
            f"--output={os.path.abspath(output_path)}",
            shell=True,
            check=True,
        )

        print(f"    ✅ Saved: {output_path}")

        return True

    except Exception as e:
        print(f"    ⚠️  Failed PR ({pr_id})")
        print(f"       Reason: {e}")
        return False

    finally:
        if os.path.exists(source_dir):
            shutil.rmtree(source_dir)
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir)


# ========= MAIN =========
def main(python_pr_df: pd.DataFrame):
    os.makedirs(BASE_REPORT_DIR, exist_ok=True)

    # group by repo_url
    grouped = python_pr_df.groupby("repo_url")

    for repo_url, df_repo in grouped:
        print("\n" + "=" * 60)
        print(f"📦 Repo: {repo_url}")

        clone_url = api_to_clone_url(repo_url)
        repo_slug = repo_slug_from_url(clone_url)
        repo_report_dir = os.path.join(BASE_REPORT_DIR, repo_slug)
        os.makedirs(repo_report_dir, exist_ok=True)

        done_marker = os.path.join(repo_report_dir, "_PYTHON_DONE")
        if os.path.exists(done_marker):
            print("⏭️  Skipped (already done)")
            continue

        # 🔑 关键：按 merged_at 排序（越早 merge，PR_1 越早）
        df_repo = df_repo.sort_values("merged_at")

        all_ok = True

        # 🔑 enumerate 生成 PR 顺序
        for pr_order, (_, row) in enumerate(df_repo.iterrows(), start=1):
            merge_sha = row["merge_commit_sha"]
            html_url = row["html_url"]

            pr_id = f"PR_{pr_order}"

            print(f"\n  🐍 {pr_id}")
            print(f"     {html_url}")
            print(f"     merged_at: {row['merged_at']}")

            pr_report_dir = os.path.join(repo_report_dir, pr_id)
            os.makedirs(pr_report_dir, exist_ok=True)

            ok = run_python_codeql_for_pr(
                repo_url=clone_url,
                merge_sha=merge_sha,
                pr_id=pr_id,
                report_dir=pr_report_dir,
            )

            if not ok:
                all_ok = False

        # ---- mark repo done ----
        if all_ok:
            with open(done_marker, "w") as f:
                f.write("ok\n")
            print(f"\n✅ Repo completed: {repo_slug}")
        else:
            print(f"\n⚠️  Repo partially failed: {repo_slug}")


# ========= ENTRY =========
if __name__ == "__main__":
    # 👇 你在外面先准备好 python_pr_df
    # 比如：
    # python_pr_df = pd.read_csv("python_prs.csv")

    python_pr_df = pd.read_parquet('python_pr.parquet')

    main(python_pr_df)