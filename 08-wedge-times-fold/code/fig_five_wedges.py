# 产出 ../img/five_wedges.png（图 2「五种楔角」）：六棱柱面法向两两组合只能给出 0° / 60° / 90° / 120° / 180° 五种楔角，一排五个楔形介质
# （ch3 图 3.1 的灰色楔子 + 参差断口），每个楔子里画一条光线：
#   0° 平行平板、60° 与 90° 楔——同一条光线折入折出（对称通过：介质内部光线垂直于角平分线，外侧角度由 Snell 算出，不手填）；
#   120° 楔——从入射面正入射，到出射面时入射角 60° 已超临界角 49.8°，全反射折回（reflect 由定律算出），标「全反射」；
#   180° ——两面重合成同一个平面，介质是半平面；示意一条进去绕半圈原路掉头的光线（虚线草图，不是追迹结果），标「物理上不可能」。
# 读者要看出：只有前三种楔能让光透射，后两种是几何上存在、光学上走不通的死角；22° 族与 46° 族分别对应 60° 与 90° 楔。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import PRESETS, draw_raypath_2d, finish, render_medium, trace, two_face_medium
from halo_notes.draw.geometry import unit
from halo_notes.draw.raypath import EventKind, N_ICE, RayEvent, RayPath2D, SegmentKind, reflect, refract
from halo_notes.draw.scene2d import annotate_2d, draw_arrowhead
from halo_notes.draw.schematic import ENTRY_FACE, EXIT_FACE, wedge_angle, wedge_apex
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS

OUT = Path(__file__).resolve().parent.parent / "img" / "five_wedges.png"
WIDTH, HEIGHT, DPI = 2400, 560, 200

PRESET = PRESETS["default"]
PATHS = {"wedge": [ENTRY_FACE, EXIT_FACE]}      # 追迹出来的光路都是「界面 1 折入、界面 2 折出 / 内反射」；180° 的掉头光线是草图不经追迹
WEDGES = (0.0, 60.0, 90.0, 120.0, 180.0)
CAPTIONS = {0.0: "平行族", 60.0: "22° 族", 90.0: "46° 族", 120.0: "全反射", 180.0: "物理上不可能"}
CRITICAL_DEG = float(np.degrees(np.arcsin(1.0 / N_ICE)))    # 49.76°
PITCH = 4.7            # 相邻楔子中心间距（世界单位）
TAIL, HEAD = 1.3, 1.2  # 光线在介质外画多长
DEPTH = 2.4            # 平板 / 60° 楔从顶点往下画多深；钝楔按张角收浅，免得横向铺太宽
DEPTHS = {0.0: 2.4, 60.0: 2.4, 90.0: 2.0, 120.0: 1.6, 180.0: 1.7}
TIR_INTERNAL_DEG = -15.0   # 120° 楔：介质内部光线方向（相对 +x；从入射面折入后能到达出射面的方向只有 (−30°, −10°) 一小段）
HALF_W = 1.35          # 平板 / 半平面的半宽
APEX_CUT = 0.3         # 楔顶截去的一小段
INSIDE = LineStyle("accent_cool", linewidth=1.6)
SKETCH = LineStyle("accent_warm", linewidth=1.6, linestyle="--")
FONTS = ("Helvetica Neue", *CJK_SANS)     # 数字 / ° 用拉丁字体（Hiragino 的 ° 是全角宽度），汉字回退到 Hiragino
CAPTION = TextStyle("ink", fontsize=17, family=FONTS)
CAPTION_SUB = TextStyle("ink_soft", fontsize=13, family=FONTS)


def wedge_medium(A: float, cx: float, top: float):
    """楔角 ``A`` 的楔子：顶点在 ``(cx, top)``，两条界面从顶点向下张开（左 = 入射面 1，右 = 出射面 2），
    下方用闭合边封住；``A = 0`` 时是竖直平板。"""
    depth = DEPTHS[A]
    if A == 0.0:
        a, b = np.array([cx - HALF_W, top]), np.array([cx - HALF_W, top - depth])
        c, d = np.array([cx + HALF_W, top - depth]), np.array([cx + HALF_W, top])
        return two_face_medium((a, b), (c, d))
    apex = np.array([cx, top])
    left = np.array([np.cos(np.radians(-90 - A / 2)), np.sin(np.radians(-90 - A / 2))])
    right = np.array([np.cos(np.radians(-90 + A / 2)), np.sin(np.radians(-90 + A / 2))])
    length = depth / np.cos(np.radians(A / 2))
    # 顶点处留一小段断口（两界面不真的交于一点，否则闭合边退化成零长），楔角仍由两界面几何算出
    return two_face_medium((apex + left * APEX_CUT, apex + left * length), (apex + right * length, apex + right * APEX_CUT))


def entry_for_internal(medium, d_in, s: float, *, n_ice: float = N_ICE) -> tuple[np.ndarray, np.ndarray]:
    """要让介质内部光线沿 ``d_in`` 走，外侧该从哪进：Snell 反推——切向分量乘 n，法向分量补足单位长。
    入射点取界面 1 上从顶端算起 ``s``（0–1）处。返回 (外部起点, 外部方向)。"""
    n1 = medium.normal(medium.face(ENTRY_FACE))
    d_in = unit(d_in)
    t = d_in - (d_in @ n1) * n1
    t_ext = n_ice * t
    assert np.linalg.norm(t_ext) < 1.0, "这个内部方向从外侧进不来（超临界角）"
    d_ext = unit(t_ext - np.sqrt(1.0 - t_ext @ t_ext) * n1)
    a, b = medium.face_vertices(medium.face(ENTRY_FACE))
    top_end, bottom_end = (a, b) if a[1] >= b[1] else (b, a)
    p = top_end + s * (bottom_end - top_end)
    return p - d_ext * TAIL, d_ext


def tir_path(medium, origin, direction, *, n_ice: float = N_ICE, inside_length: float = 0.75) -> tuple[RayPath2D, float]:
    """折入界面 1 → 到界面 2 处入射角超临界角 → 内反射，画到 ``inside_length`` 长为止。返回 (光路, 界面 2 处的入射角)。"""
    origin, d0 = np.asarray(origin, float), unit(direction)
    hit = medium.intersect_ray(origin, d0)
    assert hit is not None and hit[1].number == ENTRY_FACE, hit
    p_in = origin + d0 * hit[0]
    d_in = refract(d0, medium.normal(medium.face(ENTRY_FACE)), 1.0, n_ice)
    hit = medium.intersect_ray(p_in + d_in * 1e-9, d_in)
    assert hit is not None and hit[3].number == EXIT_FACE, hit
    p_out = p_in + d_in * (1e-9 + hit[2])
    n2 = medium.normal(medium.face(EXIT_FACE))
    incidence = float(np.degrees(np.arccos(np.clip(d_in @ n2, -1, 1))))
    assert incidence > CRITICAL_DEG, incidence
    d_back = reflect(d_in, -n2)
    path = RayPath2D(np.array([origin, p_in, p_out, p_out + d_back * inside_length]),
                     (SegmentKind.INCIDENT, SegmentKind.INTERNAL, SegmentKind.INTERNAL),
                     (RayEvent(1, ENTRY_FACE, EventKind.REFRACT_IN), RayEvent(2, EXIT_FACE, EventKind.REFLECT_INTERNAL)))
    return path, incidence


def main() -> None:
    fig = matplotlib.pyplot.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    ax = fig.add_axes([0, 0, 1, 1])
    top = 0.0
    for k, A in enumerate(WEDGES):
        cx = k * PITCH
        if A == 180.0:
            # 两面重合成同一平面：介质 = 平面下方的半平面（顶边就是那个「面」，其余三边是断口）
            a, b = np.array([cx - HALF_W, top - 0.3]), np.array([cx - HALF_W, top - DEPTHS[A]])
            c, d = np.array([cx + HALF_W, top - DEPTHS[A]]), np.array([cx + HALF_W, top - 0.3])
            medium = two_face_medium((a, d), (c, b))    # 界面 1 = 顶边；界面 2 = 底边（当断口画）
            render_medium(ax, medium, preset=PRESET, closure="jagged", amplitude=0.1)
            # 草图：一进一出、在介质里绕半圈掉头的光线（虚线；不是追迹结果）
            r = 0.5
            th = np.linspace(np.pi, 2 * np.pi, 40)
            arc = np.column_stack([cx + r * np.cos(th), (top - 0.3) + r * np.sin(th)])
            p_in, p_out = arc[0], arc[-1]
            leg = 0.9
            pts = np.vstack([p_in + np.array([0.0, leg]), arc, p_out + np.array([0.0, leg])])
            kw = PRESET.line_kwargs(SKETCH)
            ax.plot(pts[:, 0], pts[:, 1], zorder=8, **kw)
            draw_arrowhead(ax, p_in + np.array([0.0, 0.45]), np.array([0.0, -1.0]), length=PRESET.geom.arrow2d_length,
                           width=PRESET.geom.arrow2d_width, color=kw["color"], z=9)
            draw_arrowhead(ax, p_out + np.array([0.0, leg]), np.array([0.0, 1.0]), length=PRESET.geom.arrow2d_length,
                           width=PRESET.geom.arrow2d_width, color=kw["color"], z=9)
            annotate_2d(ax, "楔角 180°", (cx, top + 0.12), preset=PRESET, ha="center", va="center", semantic=CAPTION_SUB)
            annotate_2d(ax, "两面重合成同一平面", (cx, top - DEPTH - 0.55), preset=PRESET, ha="center", va="center", semantic=CAPTION_SUB)
        else:
            medium = wedge_medium(A, cx, top)
            assert np.isclose(wedge_angle(medium), A, atol=1e-9), (A, wedge_angle(medium))
            render_medium(ax, medium, preset=PRESET, closure="jagged", amplitude=0.1)
            if A == 120.0:
                phi = np.radians(TIR_INTERNAL_DEG)
                origin, d_ext = entry_for_internal(medium, [np.cos(phi), np.sin(phi)], 0.12)
                path, incidence = tir_path(medium, origin, d_ext)
                draw_raypath_2d(ax, path, preset=PRESET, semantic="ray2d", internal=INSIDE, arrows=[(0, 0.45), (2, 0.8)], markers=True)
                annotate_2d(ax, f"入射角 {incidence:.0f}° > 临界角 {CRITICAL_DEG:.1f}°", (cx, top - DEPTH - 0.55), preset=PRESET,
                            ha="center", va="center", semantic=CAPTION_SUB)
            else:
                if A == 0.0:
                    phi = np.radians(-20)   # 平板：斜着穿过去，看得出平移
                    origin, d_ext = entry_for_internal(medium, [np.cos(phi), np.sin(phi)], 0.3)
                else:
                    origin, d_ext = entry_for_internal(medium, [1.0, 0.0], 0.6)   # 对称通过：内部光线垂直于角平分线
                path = trace(medium, origin, d_ext, ["refract", "refract"], tail=TAIL, head=HEAD)
                assert [ev.face_number for ev in path.events] == [ENTRY_FACE, EXIT_FACE]
                draw_raypath_2d(ax, path, preset=PRESET, semantic="ray2d", internal=INSIDE, exit=LineStyle("accent_cool", linewidth=1.6),
                                arrows=[(0, 0.45), (2, 0.8)])
                if A:
                    apex = wedge_apex(medium)
                    annotate_2d(ax, f"楔角 {A:g}°", apex + np.array([0.0, 0.3]), preset=PRESET, ha="center", va="center", semantic=CAPTION_SUB)
                else:
                    annotate_2d(ax, "楔角 0°（平行）", (cx, top + 0.3), preset=PRESET, ha="center", va="center", semantic=CAPTION_SUB)
        if A == 120.0:
            apex = wedge_apex(medium)
            annotate_2d(ax, "楔角 120°", apex + np.array([0.0, 0.3]), preset=PRESET, ha="center", va="center", semantic=CAPTION_SUB)
        annotate_2d(ax, CAPTIONS[A], (cx, top - DEPTH - 1.05), preset=PRESET, ha="center", va="center", semantic=CAPTION)
    # 五个楔子的图题行统一对齐在最深楔子的下方

    span = PITCH * (len(WEDGES) - 1) + 2 * 2.4
    x0 = -2.4
    h = span * HEIGHT / WIDTH
    finish(ax, (x0, x0 + span), (top - DEPTH - 1.4, top - DEPTH - 1.4 + h))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
