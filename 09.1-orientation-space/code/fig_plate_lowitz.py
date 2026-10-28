# 图 2b：同一参数环面上的片晶赤道与 Parry 族两条原始圈 → ../img/plate_lowitz.png。
from pathlib import Path
import argparse

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

import fig_column_torus as T
import fig_intersecting_tori as I


def attitude(phi, swing):
    """度制物理参数：Rz(phi) @ Ry(swing)，复用图 3 的唯一姿态实现。"""
    angle = I.display_angle(I.LOWITZ, np.radians(swing))
    return I.attitude(I.LOWITZ, np.radians(phi), angle)


def parameter_point(phi, swing):
    """度制 (方位 φ, 物理摆角 t) → 显示点；不是把物理角当母圆角。

    t=0 位于外赤道，t=±90 对应图 3 的上/下交圈，t=±180 位于内赤道。
    与图 3 Lowitz 环面的坐标、相机完全相同；仅不揭面。
    """
    return I.surface(I.LOWITZ, np.radians(phi),
                     I.display_angle(I.LOWITZ, np.radians(swing)))


def main(out=None):
    fig, ax = T.figure_axes('片晶是 Lowitz 环面上的一圈',
                            '锁住摆角 t = 0°，得到片晶；摆到 ±90°，分别落在上下两条原始交圈。')
    ink = T.TOKENS['ink']
    rings = [(0, T.TOKENS['plate'])] + [
        (sign * I.CROSS_ANGLE[I.LOWITZ], T.TOKENS['parry']) for sign in (-1, 1)]
    image, _ = T.surface_pixels(rings=rings, meridian_color=T.TOKENS['motion'],
                                meridian_phi=-55)
    ax.imshow(image, origin='lower', extent=T.EXTENT, interpolation='lanczos')
    # 完整实体遮住了下交圈；只将实际被挡的段画作明示的遮挡虚线。
    # 不是把正射可见性或整圈叠画伪装成透视可见的前表面。
    hidden = parameter_point(np.linspace(-180, 180, 1601), -90)
    xy = T.project(hidden)[:, :2]
    xy[T.line_visibility(hidden)] = np.nan
    ax.plot(xy[:, 0], xy[:, 1], color=T.TOKENS['parry'], lw=1.5, ls=(0, (4, 3)))

    for phi, swing, text, target in (
        (10, 90, '上圈 · t = +90°\n经晶体对称对应 Parry', (3.85, 1.5)),
        (-15, -90, '下圈 · t = −90°\nParry 原始姿态\n（被遮挡，以虚线示意）', (3.85, -1.4)),
        (-125, 0, '片晶圈 · t = 0°\n沿赤道转动方位 φ', (-3.85, 1.35)),
        (-55, 30, '摆角 t\n绕长对角线摆动', (-3.85, -1.3)),
    ):
        point = parameter_point(phi, swing)
        ax.annotate(text, T.project(point)[:2], xytext=target, color=ink,
                    fontsize=10.5, ha='right' if target[0] < 0 else 'left', va='center',
                    linespacing=1.6,
                    arrowprops=dict(arrowstyle='-', color=T.TOKENS['mesh'], lw=0.8))
    T.motion_arrow(ax, parameter_point(np.linspace(-105, -85, 12), 0), T.TOKENS['plate'])
    T.motion_arrow(ax, parameter_point(-55, np.linspace(25, 40, 12)), T.TOKENS['motion'])
    handles = [Line2D([], [], color=T.TOKENS['plate'], lw=2, label='片晶圈'),
               Line2D([], [], color=T.TOKENS['parry'], lw=2, label='Parry 族的两条交圈'),
               Line2D([], [], color=T.TOKENS['motion'], lw=2, label='固定方位下的摆动')]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.205),
               ncol=3, labelcolor=ink)
    fig.text(0.5, 0.135, '上下两圈是不同的原始姿态点集；按 D₆ 晶体对称认同后同属 Parry 族。',
             ha='center', color=ink, fontsize=10)
    fig.text(0.5, 0.085, '片晶圈取 c 轴朝上的分支；橙色虚线是被实体遮挡的下圈，不是表面上的另一道线。',
             ha='center', color=ink, fontsize=9.5)
    fig.text(0.5, 0.035, '全摆幅参数环面示意 · 与图 3 同向；不是轴角球中的嵌入，网格间距没有物理刻度',
             ha='center', color=ink, fontsize=9)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/plate_lowitz.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
