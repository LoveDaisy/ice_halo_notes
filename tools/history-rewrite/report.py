"""把 rehearse.sh 的 json 产物汇成一份 markdown 演练报告（stdout）。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--src", required=True)
    ap.add_argument("--rev", required=True)
    ap.add_argument("--sha", required=True)
    a = ap.parse_args(argv)
    allb, before = load(a.out / "before-all.json"), load(a.out / "before.json")
    after = {m: load(a.out / f"after-{m}.json") for m in ("oid", "path")}
    filt = {m: load(a.out / f"filter-{m}.json") for m in ("oid", "path")}
    date = subprocess.run(["date", "+%Y-%m-%d %H:%M"], stdout=subprocess.PIPE, text=True).stdout.strip()
    L = [f"# repo-slim 历史重写演练报告（{date}）", "",
         f"- 输入：本地主仓 `{a.src}` 的 mirror，保留 `{a.rev}` = `{a.sha[:10]}` 并重命名为 `main`；其余分支（含 `refs/remotes/*`）在重写前删除",
         f"- 保留集：{filt['oid']['keep_paths']} 个路径 / {filt['oid']['keep_oids']} 个 oid（`keep/keep_paths.txt`、`keep/keep_oids.txt`）",
         "- 真实仓 refs 演练前后 sha256 一致（rehearse.sh 末尾断言）", "",
         "## 体量对比", "",
         "| | 提交数（main） | 全部 refs 提交数 | LFS 对象 | LFS 总量 MB | 本地缺的 LFS 对象 | 普通 blob MB | git 包 KiB |",
         "|---|---|---|---|---|---|---|---|"]
    rows = [("mirror 全部 refs（重写前）", allb), ("只留 main（重写前，已 gc）", before),
            ("重写后：oid 精确保留（默认）", after["oid"]), ("重写后：仅按路径保留", after["path"])]
    for name, m in rows:
        L.append(f"| {name} | {m['commits_rev']} | {m['commits_all']} | {m['lfs_unique_objects']} | {m['lfs_total_mb']} | "
                 f"{len(m['lfs_missing_local'])} | {m['plain_blob_total_mb']} | {m['git_pack_kib']} |")
    L += ["", "## filter 统计", ""]
    for m in ("oid", "path"):
        f = filt[m]
        L += [f"### mode = {m}", "",
              f"- 保留 file change {f['kept_changes']}，丢弃 {f['dropped_changes']}（涉及 {f['dropped_paths']} 个路径）",
              f"- 被保留的非 LFS blob > 1 MB（不删，供作者过目）：{len(f['large_kept_plain_blobs'])} 个路径",
              f"- 回落（丢弃的修改落在一个更早版本被保留的路径上）：{len(f['fallbacks'])} 处",
              f"- 同一路径保留了多个版本：{len(f['paths_with_multiple_kept_versions'])} 个路径", ""]
        for p, sz in f["large_kept_plain_blobs"]:
            L.append(f"  - 保留的大 blob：`{p}` 最大 {sz / 1e6:.2f} MB")
        for fb in f["fallbacks"][:40]:
            L.append(f"  - 回落：`{fb['path']}` @ {fb['commit'][:10] if fb['commit'] else '?'}（{fb['why']}）")
        if len(f["fallbacks"]) > 40:
            L.append(f"  - …… 另 {len(f['fallbacks']) - 40} 处见 filter-{m}.json")
        if f["kept_data_text_256k_to_limit"]:
            L += ["", "  256 KB – 1 MB 之间被保留的历史 data 文本（供作者过目）："]
            L += [f"  - `{p}` {s} B" for p, s in f["kept_data_text_256k_to_limit"]]
        L.append("")
        L += ["  丢弃体量最大的路径（前 15）：", ""]
        L += [f"  - `{d['path']}` ×{d['count']}，最大 {d['max_size'] / 1e6:.2f} MB（{d['why']}）" for d in f["dropped_top"][:15]]
        L.append("")
    L += ["## `git log --follow` 抽查（重写前 main vs 重写后）", "", "| 文件 | 重写前 | oid 模式 | path 模式 | 标题序列一致 |", "|---|---|---|---|---|"]
    for p, b in before["follow"].items():
        ao, ap_ = after["oid"]["follow"][p], after["path"]["follow"][p]
        same = "✅" if b["subjects"] == ao["subjects"] == ap_["subjects"] else "❌"
        L.append(f"| `{p}` | {b['count']} | {ao['count']} | {ap_['count']} | {same} |")
    L += ["", "## 重写后（oid 模式）最大的普通 blob", ""]
    L += [f"- {x['size'] / 1e3:.0f} KB `{x['path']}`" for x in after["oid"]["top_plain_blobs"]]
    L.append("")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
