"""量一个仓库的体量：提交数、LFS 唯一对象总量（按全部历史的 pointer 求和）、git 包大小、最大的普通 blob、抽样 md 的 --follow 历史。

用法：python measure.py <git 目录> [--rev main] [--follow PATH ...] [--gc] --out <json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from _common import layout


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE, check=True).stdout.decode("utf-8")


def measure(repo: Path, rev: str, follow: list[str], gc: bool) -> dict:
    if gc:
        subprocess.run(["git", "-C", str(repo), "gc", "-q", "--prune=now"], check=True)
    objs = {}
    for line in git(repo, "rev-list", "--objects", "--all").splitlines():
        sha, _, path = line.partition(" ")
        objs.setdefault(sha, path)
    check = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch-check"], input="".join(s + "\n" for s in objs).encode(),
                           stdout=subprocess.PIPE, check=True).stdout.decode().splitlines()
    blobs = {}
    for ln in check:
        sha, typ, size = ln.split()
        if typ == "blob":
            blobs[sha] = int(size)
    sizes = layout.blob_real_sizes(blobs, repo)
    lfs = {}
    plain = []
    for sha, (real, is_lfs) in sizes.items():
        if is_lfs:
            data = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha], stdout=subprocess.PIPE, check=True).stdout
            oid, size = layout.parse_lfs_pointer(data)
            lfs[oid] = size
        else:
            plain.append((real, objs[sha], sha))
    store = repo / "lfs" / "objects" if (repo / "lfs").is_dir() or not (repo / ".git").exists() else repo / ".git" / "lfs" / "objects"
    missing = sorted(o for o in lfs if not (store / o[:2] / o[2:4] / o).is_file())
    count = {k: v for k, v in (ln.split(": ") for ln in git(repo, "count-objects", "-v").splitlines())}
    out = {
        "rev": rev,
        "commits_rev": int(git(repo, "rev-list", "--count", rev)),
        "commits_all": int(git(repo, "rev-list", "--count", "--all")),
        "refs": git(repo, "for-each-ref", "--format=%(refname)").split(),
        "lfs_unique_objects": len(lfs),
        "lfs_total_mb": round(sum(lfs.values()) / 1e6, 2),
        "lfs_missing_local": missing,
        "plain_blob_total_mb": round(sum(s for s, _, _ in plain) / 1e6, 2),
        "git_pack_kib": int(count.get("size-pack", 0)) + int(count.get("size", 0)),
        "top_plain_blobs": [{"size": s, "path": p} for s, p, _ in sorted(plain, reverse=True)[:10]],
        "follow": {},
    }
    for f in follow:
        subjects = git(repo, "log", "--follow", "--format=%s", rev, "--", f).splitlines()
        out["follow"][f] = {"count": len(subjects), "subjects_sha1": hashlib.sha1("\n".join(subjects).encode()).hexdigest()[:12],
                            "subjects": subjects}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("--rev", default="main")
    ap.add_argument("--follow", nargs="*", default=[])
    ap.add_argument("--gc", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    m = measure(a.repo, a.rev, a.follow, a.gc)
    a.out.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{a.repo.name}: {m['commits_rev']} commits on {a.rev}, LFS {m['lfs_unique_objects']} 个 / {m['lfs_total_mb']} MB, "
          f"本地缺 {len(m['lfs_missing_local'])} 个，普通 blob {m['plain_blob_total_mb']} MB, pack {m['git_pack_kib']} KiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
