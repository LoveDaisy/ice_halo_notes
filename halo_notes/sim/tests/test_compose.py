"""compose.py 单测：合成的小尺寸纯色图验证尺寸 / 拼接宽度 / inset 光路面序列，不断言像素级画面。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from halo_notes.draw import face_sequence
from halo_notes.sim import compose


def _solid(tmp_path: Path, name: str, size, color) -> Path:
    p = tmp_path / name
    Image.new("RGB", size, color).save(p)
    return p


def test_pixel_canvas_exact_size(tmp_path):
    fig, ax = compose.pixel_canvas(320, 200, "black")
    compose.add_text(ax, (160, 100), "天顶", size_px=30)
    compose.add_dot(ax, (10, 10), radius_px=4, color="red")
    compose.add_arrow(ax, (50, 50), (100, 100))
    compose.add_box(ax, (20, 20, 40, 60))
    compose.add_circle(ax, (160, 100), 50)
    compose.add_leader(ax, (30, 30), (80, 10), "上切弧", text_end=(120, 10))
    out = compose.save_canvas(fig, tmp_path / "c.png")
    assert Image.open(out).size == (320, 200)


def test_paste_image_lands_in_box(tmp_path):
    red = _solid(tmp_path, "r.png", (10, 10), (255, 0, 0))
    fig, ax = compose.pixel_canvas(100, 50, "black")
    compose.paste_image(ax, red, (60, 10, 30, 30))
    img = np.asarray(compose.render_canvas(fig))
    assert img[25, 75].tolist() == [255, 0, 0]  # 框内
    assert img[25, 20].tolist() == [0, 0, 0]    # 框外仍是背景


def test_compose_bands_width_is_sum(tmp_path):
    bands = [_solid(tmp_path, f"b{i}.png", (25, 80), (i * 60, i * 60, i * 60)) for i in range(4)]
    out = compose.compose_bands(bands, ["a", "b", "c", "d"], gap=6, title_height=20)
    assert out.size == (25 * 4 + 6 * 3, 80 + 20)
    with pytest.raises(ValueError):
        compose.compose_bands(bands, ["a"])


def test_crop_and_invert(tmp_path):
    p = _solid(tmp_path, "w.png", (40, 20), (255, 255, 255))
    assert compose.crop(p, (5, 5, 10, 8)).size == (10, 8)
    assert np.asarray(compose.invert(p)).max() == 0


def test_crystal_inset_solves_declared_path(tmp_path):
    fig, ax = compose.pixel_canvas(400, 300, "black")
    path = compose.add_crystal_inset(fig, (200, 100, 180, 180), (400, 300), raypath=[1, 3], height_ratio=0.5)
    assert face_sequence(path) == [1, 3]
    out = compose.save_canvas(fig, tmp_path / "inset.png")
    assert Image.open(out).size == (400, 300)
