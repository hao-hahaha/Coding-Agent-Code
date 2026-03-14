import json
import math
import subprocess
from pathlib import Path

import pandas as pd
from tqdm import tqdm


PARQUET_PATH = "../python_pr_with_base_sha_merge_commit_sha.parquet"

RESULTS_DIR = Path("bandit-results")
LOG_DIR = Path("bandit-logs")

RESULTS_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)



def already_done(row):
    """
    Skip PRs that already produced a summary.json
    """
    owner = row["owner"]
    repo = row["repo"]
    pr_number = int(row["pr_number"])

    summary_path = RESULTS_DIR / f"{owner}__{repo}" / f"pr_{pr_number}" / "summary.json"

    return summary_path.exists()


def run_one_pr(row):

    owner = row["owner"]
    repo = row["repo"]
    pr_number = int(row["pr_number"])
    base_sha = row["base_sha"]
    merge_commit_sha = row["merge_commit_sha"]

    cmd = [
        "python",
        "bandit-scan.py",
        owner,
        repo,
        str(pr_number),
        base_sha,
        merge_commit_sha,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15 min timeout
        )

        return {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "finished",
        }

    except subprocess.TimeoutExpired:

        return {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "returncode": -1,
            "stdout": "",
            "stderr": "TimeoutExpired",
            "status": "timeout",
        }


def main(part_id=None, num_parts=None):

    df = pd.read_parquet(PARQUET_PATH)

    # 清理数据
    df = df[
        df["owner"].notna()
        & df["repo"].notna()
        & df["pr_number"].notna()
        & df["base_sha"].notna()
        & df["merge_commit_sha"].notna()
    ].copy()

    df = df.head(20)

    df["pr_number"] = df["pr_number"].astype(int)

    # 分块运行
    if part_id is not None and num_parts is not None:

        chunk_size = math.ceil(len(df) / num_parts)

        start = part_id * chunk_size
        end = min((part_id + 1) * chunk_size, len(df))

        df = df.iloc[start:end].copy()

        print(f"Running part {part_id}/{num_parts - 1}")
        print(f"Rows {start} → {end - 1}")
        print(f"Total rows in this chunk: {len(df)}")

    log_file = LOG_DIR / f"bandit_batch_part_{part_id if part_id is not None else 'full'}.jsonl"

    skipped = 0
    executed = 0

    for _, row in tqdm(df.iterrows(), total=len(df)):

        if already_done(row):
            skipped += 1
            continue

        result = run_one_pr(row)

        executed += 1

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print("\nFinished batch")
    print("Executed:", executed)
    print("Skipped:", skipped)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--part-id", type=int, default=None)
    parser.add_argument("--num-parts", type=int, default=None)

    args = parser.parse_args()

    main(
        part_id=args.part_id,
        num_parts=args.num_parts
    )