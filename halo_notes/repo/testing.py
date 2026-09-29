"""测试侧的划界配套：显式声明「依赖只留本地的产物」的测试，在干净 checkout 上缺文件时 skip 而非失败。

用法：给测试加 ``@pytest.mark.local_data``（根 ``conftest.py`` 注册了钩子）。被标记的测试抛出 ``FileNotFoundError`` 时，
若缺的文件按 :func:`halo_notes.repo.layout.classify` 属于「不进 git」的一类（原始渲染、中间缓存、未被引用的图），则 skip
并写明缺哪个文件、去哪一章重生成；缺的是应入库的文件（代码、配置、被引用的图）照常失败。未标记的测试不受影响。
"""

from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Optional

from halo_notes.repo import layout

MARK = "local_data"


@functools.lru_cache(maxsize=1)
def _referenced() -> frozenset:
    refs, _ = layout.referenced_files(layout.worktree_view(layout.REPO_ROOT))
    return frozenset(refs)


def local_only_path(exc: BaseException) -> Optional[str]:
    """``exc`` 若是（或由）「只留本地的文件缺失」引起，返回该文件的仓内相对路径，否则 None。"""
    seen = set()
    e: Optional[BaseException] = exc
    while e is not None and id(e) not in seen:
        seen.add(id(e))
        if isinstance(e, FileNotFoundError) and e.filename:
            p = Path(os.fsdecode(e.filename))
            p = (p if p.is_absolute() else Path.cwd() / p).resolve()
            try:
                rel = p.relative_to(layout.REPO_ROOT.resolve()).as_posix()
            except ValueError:
                return None
            if layout.classify(rel, set(_referenced()))[0] == "ignore":
                return rel
            return None
        e = e.__cause__ or e.__context__
    return None


def skip_reason(rel: str) -> str:
    chapter = rel.split("/", 1)[0]
    where = f"{chapter}/README.md" if layout.is_chapter_dir(chapter) else "各章 README.md"
    return f"只留本地的产物缺失（{rel}，按划界规则不入 git）；按 {where} 重生成后再跑"
