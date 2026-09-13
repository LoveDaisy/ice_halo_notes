# 产出 ../img/pose_to_sky.png（2 行 × 3 栏）与单行图 ../img/pose_to_sky_br.png / ../img/pose_to_sky_s.png：柱晶姿态平面 (ψ, θ)
# 与天空的对应（正文第 137–147 行）。上行 $M = br$（#3，光路 1-2-3-5-1）、下行 $M = s$（#2，光路 1-3-2）。
# 左栏：姿态平面，竖直线 ψ=ψ0 上三个样本 θ1<θ2<θ3（三色，两行左栏完全相同）；中栏：三枚柱晶（h/a=3）
# `transformed(column_attitude(ψ0, θi))`，同一入射方向（太阳方向的反向，Σ=10°，同 3.5），晶体内真实追迹的光路
# （`search_raypath`，入射方向固定、只搜入射点），入射红 / 出射蓝，面板边框 = 样本色；右栏：天空球（同 3.5 / 6.1 的经纬网格）
# + 太阳 / 反日点，上行淡画整条特里克尔弧（ch3 `_tricker_arc` 同源）、三个样本叠成一点（三色同心环），下行淡画弥散区
# （`sky_direction` 扫 (ψ,θ) 网格的像）、三个样本三个点；引线：左栏样本 → 中栏面板、中栏出射光末端 → 右栏天空点
# （`ConnectionPatch`，端点全是数据坐标）。读者要看出：同一入射光、三个绕 c 轴不同转角的晶体、三条不同的路 →
# 上行出射方向完全相同、落在天上同一点（θ 线压成一点）；下行出射方向各不相同、天上三个点。「压缩」是光路造成的事实。
# 几何参数（ψ0=35°、θ=39/49/59°、h/a=3、可行区间）来自 _pose_to_sky.py 顶注记录的 1° 扫描探针。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from _pose_to_sky import (BACKDROPS, CAMERA_3D, D_IN, IMG, PRESET, PSI0, ROW_DATA, ROWS, SUN, THETAS,  # noqa: F401
                          render_row)
from halo_notes.draw import face_sequence
from halo_notes.draw.geometry import unit

OUT = IMG / "pose_to_sky.png"
OUT_ROWS = {3: IMG / "pose_to_sky_br.png", 2: IMG / "pose_to_sky_s.png"}
WIDTH, ROW_HEIGHT, DPI = 3000, 1150, 200

PATHS = {f"#{n} {'-'.join(map(str, d.faces))} θ{k + 1}": list(d.faces) for n, d in ROW_DATA.items() for k in range(3)}

# 机械自检（test_figures 另有断言）：上行三条出射方向两两相同，下行两两相差 > 2°
_outs = {n: [unit(p.points[-1] - p.points[-2]) for p in d.paths] for n, d in ROW_DATA.items()}
assert all(np.linalg.norm(a - b) < 1e-9 for a in _outs[3] for b in _outs[3])
assert all(np.linalg.norm(a - b) > np.radians(2.0) for i, a in enumerate(_outs[2]) for b in _outs[2][i + 1:])
assert all(face_sequence(p) == list(d.faces) for d in ROW_DATA.values() for p in d.paths)


def save(numbers: tuple[int, ...], out: Path) -> None:
    height = ROW_HEIGHT * len(numbers)
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (height + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    h = 1.0 / len(numbers)
    for r, n in enumerate(numbers):
        render_row(fig, 1.0 - (r + 1) * h, h, n)
    fig.savefig(out, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"saved {out}")


def main() -> None:
    save((3, 2), OUT)
    for n, out in OUT_ROWS.items():
        save((n,), out)


if __name__ == "__main__":
    main()
