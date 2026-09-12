# 产出 ../img/tricker_arc_raypath_expand.jpg：3-1-5-7-4 与 1-2-3-5-1 两条特里克尔弧光路的反射展开——真实晶体 + 真实折线光路，
# 级联幽灵晶体（线框）+ 反射面 / 出射面高亮 + 展开后的直线光路（蓝点线）。上下两栏。
# 重制 3.2 旧图 img/legacy/tricker_arc_raypath_expand.jpg（光路与 ch2 2.2 同一组参数）。
# 读者要看出：每栏一条走廊，布局复现旧图（上：幽灵串向右上展开；下：向左上展开）；折线与直线共入射点（同一条光线）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, Corridor, HexPrism, draw_raypath, finish, frame,
                             render_corridor, rotation_from_frames, solve_raypath, unfolded_tail)
from halo_notes.draw.geometry import unit
from halo_notes.draw.style import DEFAULT_MAP, LineStyle

OUT = Path(__file__).resolve().parent.parent / "img" / "tricker_arc_raypath_expand.jpg"
WIDTH, HEIGHT, DPI = 2400, 2700, 200  # = 旧图分辨率；上下两栏各 2400×1350

PATHS = {"3-1-5-7-4": [3, 1, 5, 7, 4], "1-2-3-5-1": [1, 2, 3, 5, 1]}
CAMERA = Camera(azimuth=-60, elevation=28, distance=14)
PRESET = PRESETS["default"]
# 与 2.4 同：展开直线画成点线以示"虚"
UNFOLDED = PRESET.replace(style_map=DEFAULT_MAP.replace(
    ray_unfolded=LineStyle("accent_cool", linewidth=1.6, linestyle=":")))


def direction(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    a, e = np.deg2rad(azimuth_deg), np.deg2rad(elevation_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def panel(ax, faces, d: np.ndarray, offset, line_dir, c_axis, caption: str, caption_xy) -> None:
    """一栏：``faces`` 光路（偏好沿 ``d`` 打向入射面质心 + ``offset``），姿态由两对方向定死——
    展开直线（晶体内第一段）指向画面 ``line_dir``、晶体 c 轴指向画面 ``c_axis``（取其垂直于直线的分量）。"""
    geom = PRESET.geom
    prism = HexPrism(1.0, 2.0)
    path = solve_raypath(prism, faces, prefer_direction=d,
                         prefer_point=prism.centroid(prism.face(faces[0])) + np.asarray(offset, float),
                         tail=geom.incident_tail, head=geom.exit_head)
    r = rotation_from_frames(path.points[2] - path.points[1], [0, 0, 1], line_dir, c_axis)
    crystal, path = prism.transformed(r), path.transformed(r)
    corridor = Corridor(crystal, path)

    chain = render_corridor(ax, crystal, path, camera=CAMERA, preset=PRESET, ghost_crystal=False)
    draw_raypath(ax, path, crystal, camera=CAMERA, preset=PRESET)
    straight = corridor.straight
    # 正文的论点：首尾两面展开后平行，出射方向与入射方向相同（平行平板）——在这里机械核验
    assert np.allclose(unit(straight.points[-1] - straight.points[-2]),
                       unit(path.points[1] - path.points[0]), atol=1e-6)
    # 展开直线：入射段已随真实光路画过，只画从入射点起的直线（穿过各幽灵面处有点）与出射段
    draw_raypath(ax, unfolded_tail(straight), chain[-1], camera=CAMERA, preset=UNFOLDED,
                 semantic="ray_unfolded")
    finish(ax, *frame(CAMERA, [c.vertices for c in chain] + [path.points, straight.points],
                      WIDTH, HEIGHT // 2, margin=0.12))
    # 图注放在本栏的角上（取景由 frame() 动态决定，用 axes 坐标而不是 3D 锚点）
    ax.text(*caption_xy, caption, transform=ax.transAxes, ha="center", va="center",
            **PRESET.text_kwargs("annotation"))


def main() -> None:
    fig = matplotlib.pyplot.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    top, bottom = fig.add_axes([0, 0.5, 1, 0.5]), fig.add_axes([0, 0, 1, 0.5])

    # 上：3-1-5-7-4（参数与 ch2 2.2 左图相同）——展开直线指向画面右上，c 轴指向后方偏右（端面 2 朝观察者），
    # 幽灵串沿轴向右上展开（旧图布局）
    panel(top, PATHS["3-1-5-7-4"], direction(145, 30), (0, 0, 0.5),
          CAMERA.to_world(1.0, 0.55, 0.0), CAMERA.to_world(0.36, -0.66, -0.66),
          "光路 3-1-5-7-4 展开", (0.2, 0.9))
    # 下：1-2-3-5-1（参数与 2.2 右图相同）——展开直线指向画面左上，c 轴指向右下偏前（入射面 1 在右端），
    # 关于底面 2 镜像的幽灵沿轴向左延长，再关于 3、5 镜像错开：幽灵串向左上展开
    panel(bottom, PATHS["1-2-3-5-1"], direction(25, -40), (-0.5, -0.3, 0),
          CAMERA.to_world(-1.0, 0.45, 0.0), CAMERA.to_world(0.7, -0.35, 0.6),
          "光路 1-2-3-5-1 展开", (0.8, 0.9))

    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor(), pil_kwargs={"quality": 95})
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
