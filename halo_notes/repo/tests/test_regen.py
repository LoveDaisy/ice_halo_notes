"""各章 code/regen.py：步骤表完整（code/ 下每个 .py 要么是步骤、要么显式列为 helper）、脚本存在、--dry-run 可运行。"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from halo_notes.repo import layout
from halo_notes.repo.regen import Chapter, select

ROOT = layout.REPO_ROOT
CHAPTERS = sorted(d for d in ROOT.iterdir() if d.is_dir() and layout.is_chapter_dir(d.name))
WITH_CODE = [d for d in CHAPTERS if (d / "code").is_dir()]


def load(chapter: Path) -> Chapter:
    spec = importlib.util.spec_from_file_location(f"regen_{chapter.name.replace('-', '_').replace('.', '_')}",
                                                  chapter / "code" / "regen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CH


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda d: d.name)
def test_every_chapter_has_readme_with_regen_section(chapter: Path):
    readme = chapter / "README.md"
    assert readme.is_file()
    assert "重生成" in readme.read_text(encoding="utf-8")


@pytest.mark.parametrize("chapter", WITH_CODE, ids=lambda d: d.name)
def test_steps_cover_every_script(chapter: Path):
    ch = load(chapter)
    assert ch.code_dir == chapter / "code"
    scripts = {s.script for s in ch.steps}
    for s in scripts | set(ch.helpers):
        assert (ch.code_dir / s).is_file(), s
    assert not scripts & set(ch.helpers)
    present = {p.name for p in ch.code_dir.glob("*.py")} - {"regen.py"}
    assert present == scripts | set(ch.helpers), "code/ 下有脚本没进步骤表也没列为 helper（或反之）"
    assert all(s.lumice or not s.script.startswith("sim_") for s in ch.steps)


def test_select_filters():
    ch = load(ROOT / "09-pyramid")
    assert [s.name for s in select(ch, ["fig_plate_arcs"], False, False)] == ["fig_plate_arcs"]
    assert not any(s.lumice for s in select(ch, None, True, False))
    assert "check_pyramid" not in {s.name for s in select(ch, None, False, False)}
    assert "check_pyramid" in {s.name for s in select(ch, None, False, True)}


@pytest.mark.parametrize("chapter", WITH_CODE, ids=lambda d: d.name)
def test_dry_run(chapter: Path):
    out = subprocess.run([sys.executable, str(chapter / "code" / "regen.py"), "--dry-run"], capture_output=True, text=True,
                         check=True).stdout
    assert "重生成步骤" in out and "本次会执行" in out
