"""run.py 单测：用 fake 可执行 shell 脚本模拟 Lumice，验证参数拼装 / 落盘产物 / 失败路径。"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from halo_notes.sim import run
from halo_notes.sim import config as C

FAKE_OK = r"""#!/bin/sh
# 解析 -f -o --format，记录全部参数，往 -o 目录写一张哑图
out=.; fmt=jpg; cfg=
while [ $# -gt 0 ]; do
  case "$1" in
    -f) cfg="$2"; shift 2;;
    -o) out="$2"; shift 2;;
    --format) fmt="$2"; shift 2;;
    *) shift;;
  esac
done
echo "ARGS: $ARGS_ECHO"
test -f "$cfg" || { echo "no config" >&2; exit 2; }
printf 'PNG' > "$out/img_01.$fmt"
echo "Saved: $out/img_01.$fmt"
exit 0
"""

FAKE_FAIL = "#!/bin/sh\necho 'boom: bad config line 3' >&2\nexit 1\n"


def _script(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "fake-lumice"
    p.write_text(body)
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return p


def _cfg():
    plate = C.prism_crystal(1, 0.5, axis=C.plate_axis(1.0))
    sc = C.scene(C.sun(25), 1000, [C.entry(1)])
    return C.build_config([plate], [], sc, [C.render_unit(1, C.lens("fisheye_equal_area", fov=180), [10, 10])])


def test_render_writes_config_log_provenance(tmp_path):
    binary = _script(tmp_path, FAKE_OK)
    out = tmp_path / "out"
    res = run.render(_cfg(), out, fmt="png", workers=4, backend="cpu", bin=binary)
    assert (out / "config.json").exists() and (out / "lumice.log").exists() and (out / "provenance.json").exists()
    assert json.loads((out / "config.json").read_text()) == _cfg()
    assert [p.name for p in res.images] == ["img_01.png"]
    prov = json.loads((out / "provenance.json").read_text())
    for key in ("lumice_version", "lumice_bin_sha256", "config_sha256", "wall_clock_s", "platform", "workers", "backend", "cli_args"):
        assert key in prov, key
    assert prov["workers"] == 4 and prov["backend"] == "cpu" and prov["ray_num"] == 1000
    assert prov["cli_args"][:6] == ["-f", str(out / "config.json"), "-o", str(out), "--format", "png"]
    assert "--workers" in prov["cli_args"] and "4" in prov["cli_args"]
    assert prov["config_sha256"] == run.config_sha256(_cfg())
    assert res.wall_clock_s >= 0 and res.provenance == prov


def test_rerun_into_same_dir_clears_stale_images(tmp_path):
    binary = _script(tmp_path, FAKE_OK)
    out = tmp_path / "out"
    out.mkdir()
    (out / "img_07.png").write_bytes(b"stale")
    res = run.render(_cfg(), out, bin=binary)
    assert [p.name for p in res.images] == ["img_01.png"]
    assert not (out / "img_07.png").exists()


def test_render_failure_raises_with_log_tail(tmp_path):
    binary = _script(tmp_path, FAKE_FAIL)
    with pytest.raises(run.LumiceError, match="bad config line 3"):
        run.render(_cfg(), tmp_path / "out", bin=binary)
    assert (tmp_path / "out" / "lumice.log").exists()
    assert not (tmp_path / "out" / "provenance.json").exists()


def test_render_rejects_unknown_format(tmp_path):
    with pytest.raises(ValueError):
        run.render(_cfg(), tmp_path / "out", fmt="bmp", bin=_script(tmp_path, FAKE_OK))


def test_render_uses_ensure_lumice_by_default(tmp_path, monkeypatch):
    binary = _script(tmp_path, FAKE_OK)
    monkeypatch.setattr(run, "ensure_lumice", lambda: binary)
    res = run.render(_cfg(), tmp_path / "out", bin=None)
    assert res.provenance["lumice_bin"] == str(binary)


@pytest.mark.slow
def test_real_lumice_minimal_render(tmp_path):
    """真跑 release 版 Lumice：最小 config 出图、provenance 字段齐全（默认 `uv run pytest` 跳过，`-m slow` 才跑）。"""
    plate = C.prism_crystal(1, 0.5, axis=C.plate_axis(1.0))
    sc = C.scene(C.sun(25, spectrum=C.LEGACY_SPECTRUM), 200_000, [C.entry(1, filter=1)])
    cfg = C.build_config([plate], [C.raypath_filter(1, [1, 3])], sc, [C.render_unit(1, C.lens("fisheye_equal_area", fov=180), [200, 200], view={"elevation": 90})])
    res = run.render(cfg, tmp_path / "out", timeout=120)
    assert res.images and res.images[0].stat().st_size > 0
    assert res.provenance["lumice_version"] == "v4.5.1" and len(res.provenance["lumice_bin_sha256"]) == 64
