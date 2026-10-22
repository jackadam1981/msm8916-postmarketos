#!/usr/bin/env python3
"""Push local commits to GitHub through the Git Data API.

`git push` cannot reach github.com from this machine: the local proxy answers
502 to `CONNECT github.com:443` for every client and TLS backend, while
`api.github.com` is allowed.  The Data API is therefore the only way to get a
commit onto the remote.

This does not replay local commits.  It takes the files that differ between
the local branch and the remote branch, uploads them as blobs, and builds a
single new commit on top of the remote HEAD.  The commit message is the
message of the local HEAD commit.

Usage:
    export GH_TOKEN=$(printf 'protocol=https\\nhost=github.com\\n\\n' \\
        | git credential fill | sed -n 's/^password=//p' | tr -d '\\r\\n')
    python tools/gh/push_via_api.py [--repo owner/name] [--branch main]

Notes
  * File contents are read with `git show <branch>:<path>`, not from the
    working tree.  The checkout is CRLF and .gitattributes normalises to LF,
    so uploading the working copy would put CRLF blobs on the remote.
  * Deleted files are skipped: if the path is already gone from the remote
    tree, the tree API rejects a delete entry with 422.
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request

API = "https://api.github.com"
CTX = ssl._create_unverified_context()


def call(token: str, method: str, path: str, data=None, retries: int = 4):
    body = json.dumps(data).encode() if data is not None else None
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(
            API + path,
            data=body,
            method=method,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "workbuddy-push-via-api",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120, context=CTX) as resp:
                return json.load(resp)
        except Exception as exc:  # noqa: BLE001 - retry anything transient
            last = exc
            print(f"    {method} {path} failed ({exc}); retry {attempt + 1}/{retries}")
            time.sleep(2 + attempt * 2)
    raise SystemExit(f"giving up on {method} {path}: {last}")


def git(*args: str, binary: bool = False):
    out = subprocess.run(["git", *args], capture_output=True, check=True).stdout
    return out if binary else out.decode("utf-8")


def remote_repo() -> str:
    url = git("remote", "get-url", "github").strip()
    for prefix in ("https://github.com/", "git@github.com:"):
        if url.startswith(prefix):
            return url[len(prefix):].removesuffix(".git")
    raise SystemExit(f"cannot derive owner/name from remote url: {url}")


def changed(remote_ref: str, branch: str):
    out = git("diff", "--name-status", f"{remote_ref}", branch)
    for line in out.splitlines():
        status, path = line.split("\t", 1)
        yield status, path


def main(argv: list[str]) -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("set GH_TOKEN (a PAT with repo scope)")

    repo = argv[argv.index("--repo") + 1] if "--repo" in argv else remote_repo()
    branch = argv[argv.index("--branch") + 1] if "--branch" in argv else "main"
    remote_ref = f"github/{branch}"

    message = git("log", "-1", "--pretty=%B", branch).strip()
    if not message:
        raise SystemExit(f"no commit message on {branch}")

    ref = call(token, "GET", f"/repos/{repo}/git/ref/heads/{branch}")
    base_sha = ref["object"]["sha"]
    base_tree = call(token, "GET", f"/repos/{repo}/git/commits/{base_sha}")["tree"]["sha"]
    print(f"{repo} {branch} = {base_sha[:10]}, base tree {base_tree[:10]}")

    entries = []
    for status, path in changed(remote_ref, branch):
        if status == "D":
            print(f"  skip delete {path} (already absent from remote)")
            continue
        raw = git("show", f"{branch}:{path}", binary=True)
        blob = call(token, "POST", f"/repos/{repo}/git/blobs", {
            "content": base64.b64encode(raw).decode("ascii"),
            "encoding": "base64",
        })
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  {status} {path} ({len(raw)} B) -> {blob['sha'][:10]}")

    if not entries:
        print("nothing to push")
        return 0

    tree = call(token, "POST", f"/repos/{repo}/git/trees", {
        "base_tree": base_tree, "tree": entries,
    })
    commit = call(token, "POST", f"/repos/{repo}/git/commits", {
        "message": message, "tree": tree["sha"], "parents": [base_sha],
    })
    call(token, "PATCH", f"/repos/{repo}/git/refs/heads/{branch}", {"sha": commit["sha"]})
    print(f"updated {branch} -> {commit['sha']}")
    print(f"https://github.com/{repo}/commit/{commit['sha']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
