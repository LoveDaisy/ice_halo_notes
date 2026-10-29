# 图 3 径向剖切候选：两母圆的交点绕轴生成共享圈 → ../img/tori_section.png。
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

import fig_intersecting_tori as F

P = F.P
S = F.S
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
    origins, directions = F.T.camera_rays(F.project(points)[:, :2], F.CAMERA)
    depth = np.linalg.norm(points - origins, axis=1)
    # 轮廓附近表面距离误差会放大成深度误差；曲线单独用更紧的命中精度。
    nearest = np.minimum(F.trace(origins, directions, F.LOWITZ, cutter, tolerance=1e-8, max_steps=12000),
                         F.trace(origins, directions, F.COLUMN, cutter, tolerance=1e-8, max_steps=12000))
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
        color = outline(kind)
        for phi in cut_angles(kind, variant):
            points = F.surface(kind, phi, angles)
            plot_line(ax, points, line_visibility(points, cutter), color=color, lw=1.2)
    # 集合中的交圈仍然完整；揭面处用虚线补全，绝不透画背面。
    for sign in (-1, 1):
        points = circle_points(sign)
        visible = line_visibility(points, cutter)
        removed = (cutter(F.LOWITZ, points) > 1e-8) & (cutter(F.COLUMN, points) > 1e-8)
        plot_line(ax, points, visible & removed, color=S.family['parry'],
                  lw=1.5, linestyle=(0, (4, 3)))
        plot_line(ax, points, visible & ~removed, color=S.family['parry'], lw=1.5)
    ax.set(xlim=(-3.8, 3.8), ylim=(-2.3, 2.3), aspect='equal')
    ax.axis('off')


def outline(kind):
    return S.surfaces['lowitz' if kind == F.LOWITZ else 'column'].outline


def draw_section(ax):
    ink = S.ink
    angle = np.linspace(-np.pi, np.pi, 801)
    # 两个母圆都用实线，靠各自环面的轮廓色与直接标签区分；虚线只留给「被切去部分的交圈」。
    for kind in (F.LOWITZ, F.COLUMN):
        r = F.MAJOR[kind] + F.MINOR * np.cos(angle)
        z = F.MINOR * np.sin(angle)
        ax.plot(r, z, '-', color=outline(kind), lw=1.5)
    for sign, text in ((1, '另一原始圈\n经晶体对称对应 Parry'), (-1, 'Parry 原始圈')):
        ax.scatter([F.CROSS_R], [sign * F.CROSS_Z], s=42,
                   color=S.family['parry'], edgecolor=S.paper, lw=0.8, zorder=4)
        ax.annotate(text, (F.CROSS_R, sign * F.CROSS_Z),
                    xytext=(F.CROSS_R, sign * 1.42), ha='center', va='center',
                    color=ink, fontsize=12, linespacing=1.4,
                    arrowprops=dict(arrowstyle='-', color=ink, lw=0.7, shrinkB=4))
    ax.text(F.MAJOR[F.COLUMN] - 0.42, 0, '柱晶', ha='center', va='center', color=ink, fontsize=12)
    ax.text(F.MAJOR[F.LOWITZ] + 0.55, 0, 'Lowitz', ha='center', va='center', color=ink, fontsize=12)
    ax.set(xlim=(0.55, 3.65), ylim=(-1.75, 1.75), aspect='equal')
    ax.axis('off')
    ax.text(0.5, -0.04, '径向剖面', transform=ax.transAxes, ha='center', va='top',
            color=ink, fontsize=12)


def main(out=None, variant=DEFAULT_VARIANT, width=1601):
    P.apply_style()
    ink = S.ink
    fig = plt.figure(figsize=(12.8, 5.3))
    ax = fig.add_axes([0.0, 0.1, 0.75, 0.9])
    draw_scene(ax, variant, width)
    ax.set_ylim(-2.05, 2.05)
    section = fig.add_axes([0.765, 0.2, 0.215, 0.74])
    draw_section(section)
    handles = [Line2D([], [], color=S.family['plate'], lw=2.4, label='片晶圈（Lowitz 上）'),
               Line2D([], [], color=S.family['parry'], lw=2.4, label='Parry 族的两条交圈'),
               Line2D([], [], color=S.family['parry'], lw=1.8, ls=(0, (4, 3)), label='交圈被切去的一段')]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.39, 0.005),
               ncol=3, frameon=False, fontsize=12, labelcolor=ink, handlelength=2.2,
               columnspacing=2.2)
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
