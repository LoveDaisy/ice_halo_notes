# 图 2b：Lowitz 参数环面上的片晶圈与摆动方向 → ../img/plate_lowitz.png。
from pathlib import Path
import argparse

import matplotlib.pyplot as plt
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


SWING_PHI = 0.0   # 摆动方向那条小圈的方位：与图 2a 同一位置，偏离正对镜头


def main(out=None):
    fig, ax = T.figure_axes()
    ink = T.TOKENS['ink']
    image, _ = T.surface_pixels(finish='lowitz', rings=[(0, T.TOKENS['plate'])],
                                meridian_color=T.TOKENS['motion'], meridian_phi=SWING_PHI)
    ax.imshow(image, origin='lower', extent=T.EXTENT, interpolation='lanczos')

    for phi, swing, text, target, color in (
        (-125, 0, '片晶圈 · t = 0°\n沿赤道转动方位 φ', (-3.9, 0.95), T.TOKENS['plate']),
        (SWING_PHI, 40, '摆角 t\n绕长对角线摆动', (3.9, -1.0), T.TOKENS['motion']),
    ):
        point = parameter_point(phi, swing)
        ax.annotate(text, T.project(point)[:2], xytext=target, color=color,
                    fontsize=13, ha='right' if target[0] < 0 else 'left', va='center',
                    linespacing=1.5,
                    arrowprops=dict(arrowstyle='-', color=ink, lw=0.7, shrinkA=3,
                                    connectionstyle='angle,angleA=0,angleB=90,rad=5'))
    T.motion_arrow(ax, parameter_point(np.linspace(-120, -75, 30), 0), T.TOKENS['plate'])
    T.motion_arrow(ax, parameter_point(SWING_PHI, np.linspace(-25, 60, 40)), T.TOKENS['motion'])
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/plate_lowitz.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
