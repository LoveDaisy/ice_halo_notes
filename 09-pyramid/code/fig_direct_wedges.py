# 产出 ../img/direct_wedges.png（图 2「二十个面两两配对得到的直接楔」）：一条楔角数轴（0°–160°），锥晶二十个面两两配对得到的
# 全部 16 种楔角都落在轴上——
#   99.5° 可透射上限（`2·arcsin(1/n)` 现场算）以左的 9 种：轴上九个刻度点，轴上方一排标签（楔角 + 晕半径）用引线连到真实位置
#     （52.4°–63.8° 五个楔挤在 11.4° 里，标签只能扇开摆）；按面对类型着色：六棱柱已有的三组（底↔底 / 柱↔柱 / 底↔柱）灰色，
#     锥晶新增的柱↔锥 / 锥↔锥 / 底↔锥三组各一色；
#   轴下方挂四个三维小晶体（返工 R1）：60°（六棱柱已有，锚点）、28.0°（柱↔锥）、56.0°（锥↔锥）、62.0°（底↔锥），每组一个代表——
#     晶体整体用淡线框，构成楔的两个面深色实心，一条光线从一个面进、另一个面出（`halo_notes.draw.solve_raypath` 按面序列反解）；
#     其余五个只留刻度与标签（九个全画会挤爆）；
#   上限以右的 7 种：灰底区里的叉号（光在第二个面全反射出不去），99.8° 只差 0.3° 被卡掉，单独点名。
# 排版（返工 R2 作者选定 B 版）：灰区只占轴上方、略穿过轴，下半整条宽度留给四个小晶体（放大、间距放宽）。
# 楔角与面对类型从 `lumice_integral.geometry.Pyramid` 的面法向现场两两配对算出（楔角 = arccos(−n_a·n_b)），与
# `enumerate_signatures.KNOWN_WEDGES` 互相核对；代表光路读 `data/signature_table.md` 主表「最短代表」列，不手抄正文表格。
# 读者要看出：九个楔从哪些面对来、哪三组是锥晶新增的、上限卡掉了谁。
from __future__ import annotations

import itertools
import math
import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

import _ch9_fig as F
import enumerate_signatures as ES
from halo_notes.draw import PRESETS, Camera, draw_raypath, frame, render_crystal, solve_raypath
from lumice_integral.geometry import Pyramid
from lumice_integral.geometry.core import N_ICE

NAME = "direct_wedges"
WIDTH, HEIGHT, DPI = 2400, 1400, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}
A_MAX = 2 * math.degrees(math.asin(1 / N_ICE))     # 可透射楔角上限（99.5°）
X_RANGE = (-4.0, 160.0)
Y_RANGE = (-0.68, 0.5)

KIND_NAME = {"BB": "底面 ↔ 底面", "PP": "柱面 ↔ 柱面", "BP": "底面 ↔ 柱面",
             "PY": "柱面 ↔ 锥面", "YY": "锥面 ↔ 锥面", "BY": "底面 ↔ 锥面"}
PRISM_KINDS = ("BB", "PP", "BP")                    # 六棱柱已有（灰）
NEW_KINDS = ("PY", "YY", "BY")                      # 锥晶新增（着色）
KIND_COLOR = {"BB": PAL["slate"], "PP": PAL["slate"], "BP": PAL["slate"],
              "PY": PAL["face_4"], "YY": PAL["face_3"], "BY": PAL["face_8"]}


def face_kind(n: int) -> str:
    return "B" if n in (1, 2) else ("P" if 3 <= n <= 8 else "Y")


def pair_wedges(p: Pyramid | None = None) -> dict[float, set[str]]:
    """全部面对的楔角（0.1° 取整）→ 出现过的面对类型集合（"BB"/"PY"/…，字母排序）。"""
    p = p or Pyramid()
    out: dict[float, set[str]] = defaultdict(set)
    for fa, fb in itertools.combinations(p.faces, 2):
        c = -float(np.dot(p.normal(fa), p.normal(fb)))
        A = round(math.degrees(math.acos(max(-1.0, min(1.0, c)))), 1)
        out[A].add("".join(sorted(face_kind(fa.number) + face_kind(fb.number), key="BPY".index)))
    return dict(out)


def transmittable(wedges: dict[float, set[str]]) -> list[float]:
    return sorted(A for A in wedges if A < A_MAX)


def wedge_kind(A: float, kinds: set[str]) -> str:
    """一个楔角的着色类型：0° 三种面对都有（平行面），归「底面 ↔ 底面」（正文表格的典型构成）；其余每个楔角只有一种面对类型。"""
    if A == 0.0:
        return "BB"
    (k,) = kinds
    return k


def representatives() -> dict[float, str]:
    """`signature_table.md` 主表：楔角 → 最短代表光路。"""
    path = F.DATA / "signature_table.md"
    text = path.read_text()
    if "## 主表" not in text:
        raise ValueError(f"{path} 缺少「## 主表」小节（代表光路从那里读），表格式变了？")
    main = text.split("## 主表")[1].split("\n## ")[0]
    out = {}
    for line in main.splitlines():
        m = re.match(r"\| ([\d.]+)° \|.*?\| `([\d-]+)` \|", line)
        if m:
            out[float(m.group(1))] = m.group(2)
    return out


def radius_text(A: float) -> str:
    return "太阳原像" if A == 0 else f"{ES.min_deviation_deg(A):.0f}° 晕"


CRYSTAL_WEDGES = (28.0, 56.0, 60.0, 62.0)          # 挂三维小晶体的四个楔（每组一个代表；60° 是六棱柱已有的锚点）
PRESET = PRESETS["ice_filled"]
VIEW_TILT = 0.75


def wedge_faces(A: float) -> tuple[int, int]:
    """楔 A 的代表面对（主表最短代表的首末面）。"""
    faces = [int(x) for x in representatives()[A].split("-")]
    return faces[0], faces[-1]


def crystal_camera(p: Pyramid, faces: tuple[int, int]) -> Camera:
    """视线 = 两面法向的角平分方向往楔棱方向 ê = n_a × n_b 偏过去（两面都仍朝向观察者，因为 ê ⊥ n_a、n_b），
    既看得见两个面的面积、又看得出两面夹成的楔口。"""
    na, nb = (np.asarray(p.normal(p.face(f)), float) for f in faces)
    bis = (na + nb) / np.linalg.norm(na + nb)
    e = np.cross(na, nb)
    e /= np.linalg.norm(e)
    if e[2] < 0 or (abs(e[2]) < 1e-9 and e[0] < 0):   # 两个 ê 里取朝上 / 朝 +x 的一个，视角稳定
        e = -e
    v = bis + VIEW_TILT * e
    v /= np.linalg.norm(v)
    az = math.degrees(math.atan2(v[1], v[0]))
    el = math.degrees(math.asin(max(-1.0, min(1.0, v[2]))))
    return Camera(azimuth=az, elevation=el, projection="orthographic")


def draw_crystal(ax, A: float, color: str) -> None:
    p = Pyramid()
    faces = wedge_faces(A)
    cam = crystal_camera(p, faces)
    path = solve_raypath(p, list(faces), tail=0.55, head=0.55)
    render_crystal(ax, p, camera=cam, preset=PRESET, ghost=True)
    for f in faces:
        ax.add_patch(Polygon(cam.project_xy(p.face_vertices(p.face(f))), closed=True, facecolor=color, edgecolor=color,
                             lw=1.0, alpha=0.88, zorder=12))
    draw_raypath(ax, path, p, camera=cam, preset=PRESET)
    xlim, ylim = frame(cam, [p.vertices], 1, 1, margin=0.08)
    span = max(xlim[1] - xlim[0], ylim[1] - ylim[0]) / 2
    cx, cy = sum(xlim) / 2, sum(ylim) / 2
    ax.set_xlim(cx - span, cx + span)
    ax.set_ylim(cy - span, cy + span)
    ax.set_aspect("equal")
    ax.set_axis_off()


def build() -> plt.Figure:
    wedges = pair_wedges()
    ok = transmittable(wedges)
    assert tuple(ok) == ES.KNOWN_WEDGES, ok
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    box = (0.03, 0.08, 0.94, 0.9)
    ax = fig.add_axes(box)
    ax.set_xlim(*X_RANGE)
    ax.set_ylim(*Y_RANGE)
    ax.set_axis_off()
    ink, soft = PAL["ink_soft"], PAL["slate"]
    # 数轴
    ax.plot([0, X_RANGE[1]], [0, 0], color=ink, lw=1.2, zorder=2)
    for t in range(0, 161, 20):
        ax.plot([t, t], [0, -0.02], color=ink, lw=1.0)
        ax.text(t, -0.045, F.deg(t), ha="center", va="top", fontsize=10, color=soft, **FONT)
    ax.text(X_RANGE[1], -0.12, "楔角", ha="right", va="top", fontsize=11, color=ink, **FONT)
    # 不可透射区
    shade_bottom = -0.03                                # 灰区只占轴上方，略穿过轴，下半留给小晶体
    ax.fill_between([A_MAX, X_RANGE[1]], shade_bottom, Y_RANGE[1], color=PAL["medium"], alpha=0.35, lw=0, zorder=0)
    ax.plot([A_MAX, A_MAX], [shade_bottom, Y_RANGE[1] - 0.02], color=ink, lw=1.2, ls=(0, (5, 3)), zorder=3)
    ax.text(A_MAX + 1.5, Y_RANGE[1] - 0.06, f"可透射上限 {A_MAX:.1f}°", ha="left", va="center", fontsize=12, color=ink, **FONT)
    ax.text(A_MAX + 1.5, Y_RANGE[1] - 0.13, "楔角再大，光在第二个面全反射，出不去", ha="left", va="center", fontsize=10.5, color=ink,
            **FONT)
    blocked = sorted(A for A in wedges if A >= A_MAX)
    for A in blocked:
        ax.plot(A, 0, marker="x", ms=8, mew=1.8, color=KIND_COLOR[next(iter(wedges[A]))] if A != 120.0 else soft, zorder=4)
        if A == blocked[0]:
            continue
        ax.text(A, 0.04, F.deg(A, 1 if A % 1 else 0), ha="center", va="bottom", fontsize=9.5, color=soft, rotation=90, **FONT)
    near = blocked[0]
    ax.annotate(f"{F.deg(near, 1)}（{KIND_NAME[next(iter(wedges[near]))]}）\n只差 {near - A_MAX:.1f}° 被卡掉",
                xy=(near, 0.015), xytext=(near + 6, 0.29), fontsize=10, color=ink, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=ink, lw=0.8), **FONT)
    # 九个可透射楔：刻度点 + 扇开的标签（楔角 + 晕半径）
    label_x = np.linspace(3, A_MAX - 7, len(ok))
    label_y = 0.22
    for A, lx in zip(ok, label_x):
        kind = wedge_kind(A, wedges[A])
        color = KIND_COLOR[kind]
        ax.text(lx, label_y + 0.075, F.deg(A, 1 if A % 1 else 0), ha="center", va="bottom", fontsize=13, fontweight="bold",
                color=color, **FONT)
        ax.text(lx, label_y + 0.065, radius_text(A), ha="center", va="top", fontsize=10.5, color=color, **FONT)
        ax.plot([lx, A], [label_y - 0.005, 0.012], color=color, lw=1.0, zorder=3)
        ax.plot(A, 0, marker="o", ms=6.5, color=color, zorder=6, mec="white", mew=0.8)
    # 四个三维小晶体（轴下方）+ 引线
    slot_x = np.linspace(14, 142, len(CRYSTAL_WEDGES))
    size, cy = 0.44, -0.38                              # 小晶体方框边长（数据 y 单位）与中心高度
    for A, sx in zip(CRYSTAL_WEDGES, slot_x):
        kind = wedge_kind(A, wedges[A])
        color = KIND_COLOR[kind] if kind in NEW_KINDS else PAL["ink_soft"]
        # 数据坐标 → figure 坐标（方框在显示上是正方形：宽度按像素比例换算）
        h_fig = size / (Y_RANGE[1] - Y_RANGE[0]) * box[3]
        w_fig = h_fig * HEIGHT / WIDTH
        x_fig = box[0] + (sx - X_RANGE[0]) / (X_RANGE[1] - X_RANGE[0]) * box[2]
        y_fig = box[1] + (cy - Y_RANGE[0]) / (Y_RANGE[1] - Y_RANGE[0]) * box[3]
        cax = fig.add_axes([x_fig - w_fig / 2, y_fig - h_fig / 2, w_fig, h_fig])
        draw_crystal(cax, A, color)
        ax.plot([A, sx], [-0.012, cy + size / 2], color=color, lw=1.0, ls=(0, (3, 2)), zorder=3)
        fa, fb = wedge_faces(A)
        ax.text(sx, cy - size / 2 - 0.005, f"{F.deg(A, 1)}　{KIND_NAME[kind]}\n面 {fa} 与面 {fb}", ha="center", va="top",
                fontsize=10, color=color, linespacing=1.35, **FONT)
    # 图例
    x = 0.06
    for k in PRISM_KINDS[:1] + NEW_KINDS:
        label = "六棱柱已有（底↔底 / 柱↔柱 / 底↔柱）" if k == "BB" else f"锥晶新增：{KIND_NAME[k]}"
        fig.text(x, 0.03, "■ " + label, ha="left", va="center", fontsize=11, color=KIND_COLOR[k], **FONT)
        x += 0.25 if k == "BB" else 0.19
    return fig


def main() -> None:
    fig = build()
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
