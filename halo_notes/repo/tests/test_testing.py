"""local_data 钩子的判定：只把「按划界规则不入 git 的文件缺失」认作可 skip。"""

from __future__ import annotations

from halo_notes.repo import layout
from halo_notes.repo.testing import local_only_path, skip_reason

ROOT = layout.REPO_ROOT


def fnf(rel: str) -> FileNotFoundError:
    return FileNotFoundError(2, "No such file or directory", str(ROOT / rel))


def test_raw_render_missing_is_local_only():
    assert local_only_path(fnf("08-wedge-times-fold/data/nope/img_01.png")) == "08-wedge-times-fold/data/nope/img_01.png"
    assert local_only_path(fnf("09-pyramid/data/zenith/nope.zip")) == "09-pyramid/data/zenith/nope.zip"
    assert local_only_path(fnf("07-reflection-group/img/unreferenced_nope.gif")) == "07-reflection-group/img/unreferenced_nope.gif"


def test_tracked_kinds_are_not_local_only():
    assert local_only_path(fnf("08-wedge-times-fold/data/nope.lumice.json")) is None      # 配置应入库
    assert local_only_path(fnf("08-wedge-times-fold/code/nope.py")) is None
    assert local_only_path(FileNotFoundError(2, "x", "/etc/nope.png")) is None             # 仓外
    assert local_only_path(ValueError("x")) is None


def test_chained_and_relative():
    try:
        try:
            raise fnf("09-pyramid/data/zenith/nope.zip")
        except FileNotFoundError as e:
            raise RuntimeError("wrap") from e
    except RuntimeError as e:
        assert local_only_path(e) == "09-pyramid/data/zenith/nope.zip"
    assert "09-pyramid/README.md" in skip_reason("09-pyramid/data/zenith/nope.zip")
