"""各章「重生成入口」的共享执行器：章内 ``code/regen.py`` 只写一张显式有序的步骤表，本模块负责列出 / 执行。

步骤表是该章「怎么从 git 内容重新得到全部图与数据」的唯一权威；章 README 只写怎么调用，不复述步骤。
每步是章 ``code/`` 下的一个脚本 + 参数，按表中顺序执行（后面的步骤可能读前面步骤的产出）。

章内 ``code/regen.py`` 用法（``uv run python NN-slug/code/regen.py …``）：

- ``--dry-run``：只列步骤（是否需要 Lumice、粗估墙钟、说明），不执行
- ``--only NAME …``：只跑指定步骤（NAME = 脚本名去 ``.py``）
- ``--skip-lumice``：跳过需要 Lumice 的步骤（只重画纯几何 / 纯 numpy 的图）
- ``--with-optional``：连同默认不跑的步骤一起跑（``default=False``：核验脚本、极慢的渲染等）

需要 Lumice 的步骤用 ``halo_notes.sim.fetch`` 钉住的 release 版二进制（首次运行前 ``uv run python -m halo_notes.sim.fetch``）。
Lumice 是无固定 seed 的 MC：重渲不逐字节复现，图与数字在 MC 统计误差内一致；重渲会改写入库的 config / provenance / log
与派生的小文本（csv / numbers.json），``git diff`` 里看到的是这类变化。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Step:
    script: str                         # 章 code/ 下的脚本文件名
    args: Tuple[str, ...] = ()
    lumice: bool = False                # 需要 Lumice CLI
    minutes: float = 0.5                # 粗估墙钟（本机 M 系列，Metal / CPU 以 provenance 实测为准）
    note: str = ""
    default: bool = True                # 不带 --only / --with-optional 时是否执行

    @property
    def name(self) -> str:
        return Path(self.script).stem


@dataclass(frozen=True)
class Chapter:
    code_dir: Path
    steps: Tuple[Step, ...]
    not_regenerable: Tuple[Tuple[str, str], ...] = field(default=())   # (产物, 原因)
    helpers: Tuple[str, ...] = field(default=())                       # code/ 下不是步骤的 .py（共享模块 / 测试 / 工具），显式列出


def describe(ch: Chapter) -> List[str]:
    lines = [f"# {ch.code_dir.parent.name} 重生成步骤（按序）"]
    for i, s in enumerate(ch.steps, 1):
        flags = ("Lumice" if s.lumice else "纯 python") + ("" if s.default else "，默认不跑")
        arg = (" " + " ".join(s.args)) if s.args else ""
        lines.append(f"{i:2d}. {s.script}{arg}  [{flags}，约 {s.minutes:g} min]" + (f"  — {s.note}" if s.note else ""))
    total = sum(s.minutes for s in ch.steps if s.default)
    lines.append(f"# 默认步骤合计约 {total:g} min")
    for what, why in ch.not_regenerable:
        lines.append(f"# 不可重生成：{what} —— {why}")
    return lines


def select(ch: Chapter, only: Optional[Sequence[str]], skip_lumice: bool, with_optional: bool) -> List[Step]:
    names = {s.name for s in ch.steps}
    if only:
        unknown = sorted(set(only) - names)
        if unknown:
            raise SystemExit(f"未知步骤：{unknown}；可选：{sorted(names)}")
        steps = [s for s in ch.steps if s.name in set(only)]
    else:
        steps = [s for s in ch.steps if s.default or with_optional]
    if skip_lumice:
        steps = [s for s in steps if not s.lumice]
    return steps


def main(ch: Chapter, argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=f"{ch.code_dir.parent.name}：按序重生成本章的图与数据")
    ap.add_argument("--dry-run", action="store_true", help="只列步骤，不执行")
    ap.add_argument("--only", nargs="+", metavar="NAME", help="只跑这些步骤（脚本名去 .py）")
    ap.add_argument("--skip-lumice", action="store_true", help="跳过需要 Lumice 的步骤")
    ap.add_argument("--with-optional", action="store_true", help="连同默认不跑的步骤一起跑")
    a = ap.parse_args(argv)
    steps = select(ch, a.only, a.skip_lumice, a.with_optional)
    if a.dry_run:
        print("\n".join(describe(ch)))
        print("# 本次会执行：" + (", ".join(s.name for s in steps) or "（无）"))
        return 0
    for s in steps:
        cmd = [sys.executable, str(ch.code_dir / s.script), *s.args]
        print(f"==> {s.script} {' '.join(s.args)}", flush=True)
        t0 = time.time()
        subprocess.run(cmd, cwd=ch.code_dir, check=True)
        print(f"<== {s.name}：{time.time() - t0:.0f} s", flush=True)
    return 0
