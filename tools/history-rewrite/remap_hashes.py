"""把文件里引用的旧 commit 哈希替换成 filter-repo 重写后的新哈希。

读 ``<新仓 git 目录>/filter-repo/commit-map``（``old new`` 两列，首行表头），扫描 ``--paths`` 下的文本文件
（默认 .md / .txt / .py / .json / .csv / .log），找出 7–40 位十六进制词：
- 只有在**旧仓**里能解析为 commit 的词才算「本仓 commit 哈希」（``git cat-file --batch-check``），sha256、Ice Halo / LI 仓的
  commit 号、数据里的随机十六进制串不会误伤；
- 映射到新哈希后按原长度截断替换；映射为全 0（提交因变空被裁剪）或不在 commit-map 里的，不替换、列入清单。

默认 dry-run，只打印报告；``--apply`` 才写回文件。报告同时写 ``--report``（json）。
用法：python remap_hashes.py --old <旧 mirror> --map <commit-map> --paths <文件或目录> ... [--apply] [--report out.json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

TOKEN = re.compile(r"(?<![0-9A-Za-z])[0-9a-f]{7,40}(?![0-9A-Za-z])")
EXTS = (".md", ".txt", ".py", ".json", ".csv", ".log")
ZERO = "0" * 40


def load_map(path: Path) -> dict[str, str]:
    out = {}
    for i, line in enumerate(path.read_text().splitlines()):
        parts = line.split()
        if i == 0 and parts[:2] == ["old", "new"]:
            continue
        if len(parts) == 2:
            out[parts[0]] = parts[1]
    return out


def resolve_commits(old: Path, tokens: set[str]) -> dict[str, str]:
    """token → 旧仓里的完整 commit sha（解析不到 / 不是 commit / 有歧义的不出现在结果里）。"""
    toks = sorted(tokens)
    if not toks:
        return {}
    out = subprocess.run(["git", "-C", str(old), "cat-file", "--batch-check=%(objectname) %(objecttype)"],
                         input="".join(t + "\n" for t in toks).encode(), stdout=subprocess.PIPE, check=True).stdout.decode()
    res = {}
    for tok, line in zip(toks, out.splitlines()):
        parts = line.split()
        if len(parts) == 2 and parts[1] == "commit":
            res[tok] = parts[0]
    return res


def iter_files(paths: list[Path]):
    for p in paths:
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix in EXTS and ".git" not in f.parts and ".venv" not in f.parts:
                    yield f


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--old", type=Path, required=True, help="重写前的仓库（mirror 备份）")
    ap.add_argument("--map", type=Path, required=True, help="filter-repo 生成的 commit-map")
    ap.add_argument("--paths", type=Path, nargs="+", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", type=Path)
    a = ap.parse_args(argv)
    cmap = load_map(a.map)
    files = list(iter_files(a.paths))
    texts = {f: f.read_text(encoding="utf-8", errors="surrogateescape") for f in files}
    tokens = {m.group(0) for t in texts.values() for m in TOKEN.finditer(t)}
    commits = resolve_commits(a.old, tokens)

    replaced = defaultdict(list)
    pruned = defaultdict(list)
    unmapped = defaultdict(list)
    for f, text in texts.items():
        def sub(m: re.Match) -> str:
            tok = m.group(0)
            full = commits.get(tok)
            if full is None:
                return tok
            new = cmap.get(full)
            if new is None:
                unmapped[str(f)].append(tok)
                return tok
            if new == ZERO:
                pruned[str(f)].append(tok)
                return tok
            replaced[str(f)].append(f"{tok}→{new[:len(tok)]}")
            return new[:len(tok)]

        new_text = TOKEN.sub(sub, text)
        if a.apply and new_text != text:
            f.write_text(new_text, encoding="utf-8", errors="surrogateescape")

    report = {
        "files_scanned": len(files),
        "hex_tokens": len(tokens),
        "tokens_resolving_to_old_commits": len(commits),
        "replaced": dict(replaced),
        "pruned_commits_not_replaced": dict(pruned),
        "not_in_commit_map": dict(unmapped),
        "applied": a.apply,
    }
    if a.report:
        a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_rep = sum(len(v) for v in replaced.values())
    print(f"扫描 {len(files)} 个文件、{len(tokens)} 个十六进制词，其中 {len(commits)} 个是旧仓 commit；"
          f"{'已替换' if a.apply else '将替换'} {n_rep} 处（{len(replaced)} 个文件），被裁剪 {sum(map(len, pruned.values()))} 处，"
          f"不在 commit-map（不可达 / 被删分支）{sum(map(len, unmapped.values()))} 处")
    for f, v in sorted(pruned.items()):
        print(f"  被裁剪（不替换）：{f}: {', '.join(sorted(set(v)))}")
    for f, v in sorted(unmapped.items()):
        print(f"  不在 commit-map（旧仓中已不可达或只在被删分支上，不替换）：{f}: {', '.join(sorted(set(v)))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
