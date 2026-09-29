"""从某个 git 目录的 ``<rev>``（默认 main）树算出「要保留的插图」集合，供 filter_rules.py 使用。

产出（``--out`` 目录）：
- ``keep_paths.txt``：被 md 引用的路径 + ``UNREGENERABLE_INPUTS``（每行一个）
- ``keep_oids.txt``：上述路径在 ``<rev>`` 时刻的 LFS oid（sha256；非 LFS 文件取内容 sha256，与 LFS oid 同口径）
引用集合与 ``layout referenced`` 同一实现（git 树视图）；断链则报错退出。
用法：python build_keep_set.py <git 目录> --out <目录> [--rev main]
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from _common import layout


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("gitdir", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rev", default="main")
    a = ap.parse_args(argv)
    view = layout.tree_view(a.rev, a.gitdir)
    refs, errors = layout.referenced_files(view)
    if errors:
        for ref, err in errors:
            print(f"ERROR {ref.md}:{ref.line} → {ref.raw}（{err}）", file=sys.stderr)
        return 1
    keep = sorted(refs | set(layout.UNREGENERABLE_INPUTS))
    tree = layout.ls_tree(a.rev, a.gitdir)
    missing = [p for p in keep if p not in tree]
    if missing:
        print(f"ERROR {a.rev} 树里缺：{missing}", file=sys.stderr)
        return 1
    oids = []
    for p in keep:
        data = subprocess.run(["git", "-C", str(a.gitdir), "cat-file", "blob", tree[p][0]], stdout=subprocess.PIPE,
                              check=True).stdout
        ptr = layout.parse_lfs_pointer(data)
        oids.append(ptr[0] if ptr else hashlib.sha256(data).hexdigest())
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "keep_paths.txt").write_text("".join(p + "\n" for p in keep), encoding="utf-8")
    (a.out / "keep_oids.txt").write_text("".join(o + "\n" for o in sorted(set(oids))), encoding="utf-8")
    print(f"keep set @ {a.rev}：{len(keep)} 个路径，{len(set(oids))} 个 oid → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
