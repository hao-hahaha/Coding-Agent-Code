import os
import sys
import json
import time
import requests
import pandas as pd
from urllib.parse import urlparse
import base64

GITHUB_TOKEN = ""

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


MAX_TO_RUN = 400


def get_merge_commit_sha(pr_url):
    parts = urlparse(pr_url).path.strip("/").split("/")
    owner, repo, _, pr_number = parts

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    r = requests.get(api_url, headers=HEADERS)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.text}")

    data = r.json()
    return {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "merged": data.get("merged"),
        "merged_at": data.get("merged_at"),
        "merge_commit_sha": data.get("merge_commit_sha"),
    }

def get_files_changed_by_commit(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.text}")

    data = r.json()
    files = []
    for f in data.get("files", []):
        files.append({
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "changes": f["changes"],
        })
    return files

def get_file_at_commit(owner, repo, filepath, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filepath}"
    r = requests.get(url, headers=HEADERS, params={"ref": sha})

    if r.status_code != 200:
        return None  # removed / binary / too large / not accessible

    data = r.json()
    if isinstance(data, list):
        return None  # directory, not a file

    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return None


def load_processed_url_set(jsonl_path: str) -> set:
    """
    Return a set of html_url already present in jsonl (success or error).
    """
    processed = set()
    if not os.path.exists(jsonl_path):
        return processed

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                url = rec.get("html_url")
                if url:
                    processed.add(url)
            except json.JSONDecodeError:
                continue
    return processed


def main(shard_id: int):
    parquet_path = f"merged_pr_df_shard_{shard_id}.parquet"
    out_path = f"pr_full_data_shard_{shard_id}.jsonl"

    df = pd.read_parquet(parquet_path)
    all_urls = df["html_url"].tolist()

    processed_urls = load_processed_url_set(out_path)

    remaining_urls = [u for u in all_urls if u not in processed_urls]

    print(f"[shard {shard_id}] total urls in parquet: {len(all_urls)}")
    print(f"[shard {shard_id}] already in jsonl (skip): {len(processed_urls)}")
    print(f"[shard {shard_id}] remaining to run: {len(remaining_urls)}")

    if MAX_TO_RUN is not None:
        remaining_urls = remaining_urls[:MAX_TO_RUN]
        print(f"[shard {shard_id}] MAX_TO_RUN applied, will run: {len(remaining_urls)}")

    # append new results only
    with open(out_path, "a", encoding="utf-8") as f:
        for i, pr_url in enumerate(remaining_urls, start=1):
            print(f"[shard {shard_id}] [{i}/{len(remaining_urls)}] {pr_url}")

            record = {
                "html_url": pr_url,
                "error": None,
                "files": [],
            }

            try:
                pr_info = get_merge_commit_sha(pr_url)

                if not pr_info["merge_commit_sha"]:
                    raise RuntimeError("No merge_commit_sha")

                record.update(pr_info)

                files = get_files_changed_by_commit(
                    pr_info["owner"],
                    pr_info["repo"],
                    pr_info["merge_commit_sha"],
                )

                for fmeta in files:
                    file_entry = dict(fmeta)

                    if fmeta["status"] != "removed":
                        source_code = get_file_at_commit(
                            pr_info["owner"],
                            pr_info["repo"],
                            fmeta["filename"],
                            pr_info["merge_commit_sha"],
                        )
                    else:
                        source_code = None

                    file_entry["source_code"] = source_code
                    record["files"].append(file_entry)

            except Exception as e:
                record["error"] = str(e)

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

    print(f"[shard {shard_id}] DONE. Appended results to: {out_path}")

if __name__ == "__main__":
    SHARD_ID = 7
    main(SHARD_ID)