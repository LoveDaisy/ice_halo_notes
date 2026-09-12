# 产出 ../img/ch3_wedge_path.jpg：楔角光路——上：六方柱截面里含两次内反射的光路（红折线）及其展开（两个点线幽灵
# 六边形 + 蓝色展开直线，与红折线共入射点）；下：展开后等价的楔形介质（两界面夹角 θ = 展开后入射边与出射边
# 的夹角），同一条光线折入折出。重制 3.1 旧图 img/legacy/ch3_wedge_path.jpg。
# 读者要看出：展开后的内部直线穿过一串幽灵；楔角 θ 由几何算出；上下两图是同一条光线（脚本里机械核验）。
# 面序列从旧图读出：截面按"平顶"放置（标准截面转 30°：3 右上、4 上、5 左上、6 左下、7 下、8 右下），
# 光线从左下射入左上边（5）、在右上边（3）与底边（7）各内反射一次、再从左上边（5）射出——5-3-7-5。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Corridor, CrossSection, draw_raypath_2d, draw_wedge_angle, finish,
                             render_medium, render_section, solve_raypath_2d, trace, two_face_medium,
                             unfolded_tail, wedge_angle, wedge_apex)
from halo_notes.draw.geometry import unit
from halo_notes.draw.schematic import ENTRY_FACE, EXIT_FACE
from halo_notes.draw.style import LineStyle

OUT = Path(__file__).resolve().parent.parent / "img" / "ch3_wedge_path.jpg"
WIDTH, HEIGHT, DPI = 2400, 2267, 200  # = 旧图分辨率；上栏 2400×1000、下栏 2400×1267

PATHS = {"5-3-7-5": [5, 3, 7, 5], "wedge": [ENTRY_FACE, EXIT_FACE]}
PRESET = PRESETS["default"]
UNFOLDED = LineStyle("accent_cool", linewidth=1.6, linestyle=":")   # 展开直线：蓝点线（旧图）
SPAN = 11.0   # 两栏共用比例尺：横向都是 11 个边长


def main() -> None:
    fig = matplotlib.pyplot.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    top = fig.add_axes([0, 1 - 1000 / HEIGHT, 1, 1000 / HEIGHT])
    bottom = fig.add_axes([0, 0, 1, 1 - 1000 / HEIGHT])
    tail, head = 1.9, 1.7

    # ---- 上：截面光路 + 展开 ----
    section = CrossSection(1.0).rotated(30)   # 平顶
    faces = PATHS["5-3-7-5"]
    entry = section.face(faces[0])
    v_left, v_upper = section.vertex_between(5, 6), section.vertex_between(4, 5)
    path = solve_raypath_2d(section, faces, prefer_point=v_left + 0.2 * (v_upper - v_left),
                            prefer_direction=[np.cos(np.deg2rad(15)), np.sin(np.deg2rad(15))],
                            tail=tail, head=head)
    corridor = Corridor(section, path)
    render_section(top, section, preset=PRESET)
    for ghost in corridor.ghosts:
        render_section(top, ghost, preset=PRESET, variant="ghost")
    draw_raypath_2d(top, path, preset=PRESET, semantic="ray2d", internal="ray_internal",
                    arrows=[(0, 0.4), (len(path.kinds) - 1, 0.85)], markers=True)
    straight = unfolded_tail(corridor.straight)
    draw_raypath_2d(top, straight, preset=PRESET, semantic=UNFOLDED,
                    arrows=[(len(straight.kinds) - 1, 0.85)], markers=True)
    x0 = -3.6
    finish(top, (x0, x0 + SPAN), (-1.9, -1.9 + SPAN * 1000 / WIDTH))

    # ---- 下：等价的楔形介质 ----
    # 两条界面 = 展开后的入射边（真实截面的 5）与出射边（最后一个幽灵的 5），楔角由它们的几何算出
    last = corridor.ghosts[-1]
    a, b = section.face_vertices(entry)
    c, d = last.face_vertices(last.face(faces[-1]))
    apex_guess = wedge_apex(two_face_medium((a, b), (c, d)))
    u, v = unit((a + b) / 2 - apex_guess), unit((c + d) / 2 - apex_guess)
    s_in = np.linalg.norm(corridor.straight.points[1] - apex_guess)
    s_out = np.linalg.norm(corridor.straight.points[-2] - apex_guess)
    s_top, s_bot = min(s_in, s_out) - 1.35, max(s_in, s_out) + 2.2
    wedge = two_face_medium((apex_guess + u * s_top, apex_guess + u * s_bot),
                            (apex_guess + v * s_bot, apex_guess + v * s_top))
    theta = wedge_angle(wedge)
    # 同一条光线：在楔形上追迹，入射点、出射方向都与展开直线一致
    wedge_path = trace(wedge, corridor.straight.points[0], corridor.straight.points[1] - corridor.straight.points[0],
                       ["refract", "refract"], tail=tail, head=head)
    assert np.allclose(wedge_path.points[1], corridor.straight.points[1], atol=1e-9)
    assert np.allclose(unit(wedge_path.points[-1] - wedge_path.points[-2]),
                       unit(corridor.straight.points[-1] - corridor.straight.points[-2]), atol=1e-9)
    assert np.isclose(theta, 60.0, atol=1e-9), theta   # 5-3-7-5 展开后首尾两面夹 60°

    render_medium(bottom, wedge, preset=PRESET, closure="jagged", amplitude=0.14)
    draw_wedge_angle(bottom, wedge, preset=PRESET, radius=s_top + 0.3, label_offset=0.38)
    # 入射红实线、内部蓝实线、出射蓝点线（旧图）
    draw_raypath_2d(bottom, wedge_path, preset=PRESET, semantic="ray2d",
                    internal=LineStyle("accent_cool", linewidth=1.6), exit=UNFOLDED,
                    arrows=[(0, 0.4), (2, 0.85)])
    cx = (wedge.vertices[:, 0].min() + wedge.vertices[:, 0].max()) / 2
    finish(bottom, (cx - SPAN / 2, cx + SPAN / 2),
           (wedge.vertices[:, 1].min() - 0.6, wedge.vertices[:, 1].min() - 0.6 + SPAN * (HEIGHT - 1000) / WIDTH))

    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor(), pil_kwargs={"quality": 95})
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
