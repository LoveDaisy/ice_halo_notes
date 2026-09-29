"""按划界规则重写一个（mirror）仓库的全部历史：git-filter-repo 的库调用（不是 CLI）。

判定（逐个提交、逐个新增 / 修改的文件）：
- 路径按 ``layout.classify`` 判定，引用集合取 ``keep_paths.txt``（HEAD 时刻，见 build_keep_set.py），data 文本的大小阈值取**该提交当时的 blob 大小**；
- ``--mode oid``（默认）：媒体文件按内容 oid 判定——oid ∈ ``keep_oids.txt`` 就保留（与路径无关：改名前的旧路径也留，
  不增加 LFS 体量，旧提交的图链照常可看），否则丢弃（同一路径被反复覆盖的旧版本也丢掉）；
  ``--mode path``：只按路径保留（HEAD 引用路径的全部旧版本随路径留下），供作者对比两套数字；
- 不做「按大小一刀切」的兜底删除（演练实测它会删掉 classify 判为保留的 legacy .nb 脚本），改为报告：被保留的非 LFS blob
  > ``--report-bigger-than``（默认 1 MB）逐条列出，由作者过目。

被丢弃的是 file change（新增 / 修改），删除操作原样保留；某路径的修改被丢弃时，该路径在新历史里停留在更早被保留的版本
（「回落」），报告逐条列出。变空的提交由 filter-repo 自动裁剪。commit message 里的旧哈希由 filter-repo 默认改写。

用法（须用装了 git_filter_repo 的 python，rehearse.sh 会找）：
    python filter_rules.py <mirror 目录> --keep-dir <build_keep_set 产出> --mode oid|path --report <json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

from _common import layout

import git_filter_repo as fr


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("--keep-dir", type=Path, required=True)
    ap.add_argument("--mode", choices=("oid", "path"), default="oid")
    ap.add_argument("--report-bigger-than", type=int, default=1024 * 1024)
    ap.add_argument("--report", type=Path, required=True)
    a = ap.parse_args(argv)

    keep_paths = set(a.keep_dir.joinpath("keep_paths.txt").read_text(encoding="utf-8").split("\n")) - {""}
    keep_oids = set(a.keep_dir.joinpath("keep_oids.txt").read_text(encoding="utf-8").split()) - {""}
    exts = layout.media_exts_from_text(layout._git(a.repo, "show", "HEAD:.gitattributes").decode("utf-8"))

    blobs: dict[int, tuple[str | None, int, bool]] = {}      # mark → (oid, 真实大小, 是否 LFS pointer)
    stats = defaultdict(int)
    dropped = defaultdict(lambda: {"count": 0, "max_size": 0, "why": ""})
    large_kept: dict[str, int] = {}
    kept_large_text: dict[str, int] = {}
    kept_versions: dict[str, set] = defaultdict(set)
    fallbacks: list[dict] = []

    def blob_cb(blob, _meta):
        ptr = layout.parse_lfs_pointer(blob.data) if len(blob.data) <= 1024 else None
        if ptr:
            blobs[blob.id] = (ptr[0], ptr[1], True)
        else:
            blobs[blob.id] = (hashlib.sha256(blob.data).hexdigest(), len(blob.data), False)

    def commit_cb(commit, _meta):
        keep = []
        for fc in commit.file_changes:
            if fc.type != b"M":
                keep.append(fc)
                continue
            path = fc.filename.decode("utf-8", "surrogateescape")
            oid, size, is_ptr = blobs.get(fc.blob_id, (None, None, False))
            verdict, why = layout.classify(path, keep_paths, size, exts)
            if a.mode == "oid" and oid in keep_oids:
                verdict, why = "keep", "内容 oid 在 HEAD 保留集"
            elif a.mode == "oid" and path in keep_paths:
                verdict, why = "ignore", "HEAD 引用路径的旧版本（oid 不在 keep 集）"
            if verdict == "keep" and not is_ptr and size is not None and size > a.report_bigger_than:
                large_kept[path] = max(large_kept.get(path, 0), size)
            if verdict == "keep":
                keep.append(fc)
                stats["kept_changes"] += 1
                kept_versions[path].add(oid)
                if path.split("/")[1:2] == ["data"] and size and size > 256 * 1024:
                    kept_large_text[path] = max(kept_large_text.get(path, 0), size)
            else:
                stats["dropped_changes"] += 1
                d = dropped[path]
                d["count"] += 1
                d["max_size"] = max(d["max_size"], size or 0)
                d["why"] = why
                if kept_versions.get(path):
                    fallbacks.append({"path": path, "commit": commit.original_id.decode() if commit.original_id else None,
                                      "why": why})
        commit.file_changes = keep

    args = fr.FilteringOptions.parse_args(["--force", "--source", str(a.repo), "--target", str(a.repo)])
    fr.RepoFilter(args, blob_callback=blob_cb, commit_callback=commit_cb).run()

    report = {
        "mode": a.mode,
        "keep_paths": len(keep_paths),
        "keep_oids": len(keep_oids),
        "kept_changes": stats["kept_changes"],
        "dropped_changes": stats["dropped_changes"],
        "dropped_paths": len(dropped),
        "dropped_top": sorted(({"path": p, **v} for p, v in dropped.items()), key=lambda d: -d["max_size"])[:30],
        "large_kept_plain_blobs": sorted(large_kept.items(), key=lambda kv: -kv[1]),
        "kept_data_text_256k_1m": sorted(kept_large_text.items()),
        "fallbacks": fallbacks,
        "paths_with_multiple_kept_versions": sorted(p for p, v in kept_versions.items() if len(v) > 1),
    }
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[{a.mode}] kept {stats['kept_changes']} / dropped {stats['dropped_changes']} file changes "
          f"({len(dropped)} 个路径)；保留的非 LFS 大 blob {len(large_kept)} 个；"
          f"回落 {len(fallbacks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
