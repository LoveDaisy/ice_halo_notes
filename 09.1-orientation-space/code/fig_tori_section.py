# 图 3 径向剖切候选：两母圆的交点绕轴生成共享圈 → ../img/tori_section.png。
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

import fig_intersecting_tori as F

P = F.P
# 前侧扇区揭面；母圆、姿态映射及相机均沿用上一版。
DEFAULT_VARIANT = 'staggered'
CUTS = {
    'aligned': ((-65, 40), (-65, 40)),
    'staggered': ((-75, 55), (-55, 35)),
}


def cut_angles(kind, variant):
    return F.AZ + np.radians(CUTS[variant][kind])


def cutter_for(variant):
    def cutter(kind, xyz):
        start, end = cut_angles(kind, variant)
        left = np.array([-np.sin(start), np.cos(start), 0])
        right = np.array([np.sin(end), -np.cos(end), 0])
        # 两个过轴平面的有向距离：扇区内为正，不造出实体封口。
        return np.minimum(xyz @ left, xyz @ right)
    return cutter


def circle_points(sign, count=1601):
    phi = np.linspace(-np.pi, np.pi, count)
    return F.surface(F.LOWITZ, phi, sign * F.CROSS_ANGLE[F.LOWITZ])


def line_visibility(points, cutter):
    depth = 8 - F.project(points)[:, 2]
    origins = points + depth[:, None] * F.EYE
    # 轮廓附近表面距离误差会放大成深度误差；曲线单独用更紧的命中精度。
    nearest = np.minimum(F.trace(origins, F.LOWITZ, cutter, tolerance=1e-8, max_steps=12000),
                         F.trace(origins, F.COLUMN, cutter, tolerance=1e-8, max_steps=12000))
    return depth <= nearest + 0.002


def plot_line(ax, points, mask, **kwargs):
    xy = F.project(points)[:, :2].copy()
    xy[~mask] = np.nan
    ax.plot(xy[:, 0], xy[:, 1], **kwargs)


def draw_scene(ax, variant, width):
    cutter = cutter_for(variant)
    image, _, _ = F.surface_pixels(width, cutter)
    ax.imshow(image, origin='lower', extent=F.EXTENT, interpolation='lanczos')
    # 剖切边是原曲面上的母圆，不添加填充圆盘；只画可见弧。
    angles = np.linspace(-np.pi, np.pi, 1201)
    for kind in (F.LOWITZ, F.COLUMN):
        color = P.PAL['ice_edge'] if kind == F.LOWITZ else P.PAL['ink_soft']
        for phi in cut_angles(kind, variant):
            points = F.surface(kind, phi, angles)
            plot_line(ax, points, line_visibility(points, cutter), color=color, lw=1.2)
    # 集合中的交圈仍然完整；揭面处用虚线补全，绝不透画背面。
    for sign in (-1, 1):
        points = circle_points(sign)
        visible = line_visibility(points, cutter)
        removed = (cutter(F.LOWITZ, points) > 1e-8) & (cutter(F.COLUMN, points) > 1e-8)
        plot_line(ax, points, visible & removed, color=P.PAL['face_5'],
                  lw=1.5, linestyle=(0, (4, 3)))
        plot_line(ax, points, visible & ~removed, color=P.PAL['face_5'], lw=1.5)
    ax.set(xlim=(-3.8, 3.8), ylim=(-2.3, 2.3), aspect='equal')
    ax.axis('off')


def draw_section(ax):
    ink = P.PAL['ink_soft']
    angle = np.linspace(-np.pi, np.pi, 801)
    for kind, style in ((F.LOWITZ, '-'), (F.COLUMN, '--')):
        r = F.MAJOR[kind] + F.MINOR * np.cos(angle)
        z = F.MINOR * np.sin(angle)
        color = P.PAL['ice_edge'] if kind == F.LOWITZ else P.PAL['ink_soft']
        ax.plot(r, z, style, color=color, lw=1.4)
    for sign, text in ((1, '另一交圈'), (-1, 'Parry 圈')):
        ax.scatter([F.CROSS_R], [sign * F.CROSS_Z], s=34,
                   color=P.PAL['face_5'], edgecolor='white', lw=0.7, zorder=4)
        ax.annotate(text, (F.CROSS_R, sign * F.CROSS_Z),
                    xytext=(F.CROSS_R, sign * 1.35), ha='center', va='center',
                    color=ink, fontsize=10,
                    arrowprops=dict(arrowstyle='-', color=P.PAL['ice_edge'], lw=0.7))
    ax.text(F.MAJOR[F.COLUMN] - 0.35, 0, '柱晶', ha='center', color=ink, fontsize=10)
    ax.text(F.MAJOR[F.LOWITZ] + 0.35, 0, 'Lowitz', ha='center', color=ink, fontsize=10)
    ax.set(xlim=(0.55, 3.65), ylim=(-1.65, 1.65), aspect='equal')
    ax.axis('off')
    ax.set_title('径向剖面 · 两个相交的母圆', color=ink, fontsize=10, pad=7)


def main(out=None, variant=DEFAULT_VARIANT, width=1601):
    P.apply_style()
    ink = P.PAL['ink_soft']
    fig = plt.figure(figsize=(12.8, 7.6))
    title = '沿径向剖开，看见两条交圈' if variant == 'aligned' else '外环多揭一段，内环少揭一段'
    fig.text(0.045, 0.935, title, fontsize=18, color=ink)
    fig.text(0.045, 0.885, '剖面上的两个交点，绕轴各走一圈；浅面是 Lowitz，深面是柱晶。',
             fontsize=11, color=ink)
    ax = fig.add_axes([0.02, 0.25, 0.72, 0.59])
    draw_scene(ax, variant, width)
    section = fig.add_axes([0.76, 0.36, 0.21, 0.36])
    draw_section(section)
    fig.text(0.865, 0.315, '剖面不填充：这里只是两张薄面。',
             ha='center', fontsize=9, color=ink)
    handles = [Line2D([], [], color=P.PAL['arc_roll'], lw=2, label='蓝线：片晶圈（Lowitz 上）'),
               Line2D([], [], color=P.PAL['face_5'], lw=2, label='橙线：两条共享圈'),
               Line2D([], [], color=P.PAL['face_5'], lw=1.5, ls='--', label='虚线：揭面处补全交圈')]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.205),
               ncol=3, frameon=False, fontsize=10, labelcolor=ink)
    fig.text(0.5, 0.155, '上圈 t = +90°；下圈 t = −90°（Parry）。片晶圈 t = 0° 与两圈都不相交。',
             ha='center', fontsize=10, color=ink)
    fig.text(0.5, 0.105, '完整 Lowitz 有两条原始交圈；roll 锁 0 的半环只有下圈；按 D₆ 对称认同后两圈同属 Parry 族。',
             ha='center', fontsize=9.5, color=ink)
    fig.text(0.5, 0.045, '集合关系示意 · 非整个 SO(3) 的三维欧氏嵌入；切口只揭面，未改变姿态族。背面线不透画。',
             ha='center', fontsize=9, color=ink)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/tori_section.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--variant', choices=CUTS, default=DEFAULT_VARIANT)
    parser.add_argument('--width', type=int, default=1601, help='表面采样宽度；探针可用 601')
    args = parser.parse_args()
    if (args.variant != DEFAULT_VARIANT or args.width != 1601) and args.output is None:
        parser.error('非默认候选或低分辨率探针须显式指定 --output')
    main(args.output, args.variant, args.width)
