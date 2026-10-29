# 9.1 概念图的画布、球面与晶体外观；几何/投影仍调用系列库。
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

from halo_notes.draw.geometry import HexPrism
from halo_notes.draw.projection import Camera
from halo_notes.draw.scene import finish, render_crystal
from halo_notes.draw.sphere import Sphere, graticule
from halo_notes.draw.style import PRESETS
from halo_notes.draw.style.candidate import crystal_preset, scheme
from fig_column_torus import P

S = scheme()
INK = S.ink
# 篇内语义色：太阳（ŝ 与晶体系里的 u）金色；非族的中性强调（轴角直径、采样点、密度曲线）墨色；
# 路线 A / B 等二元对照用墨实线 / 紫虚线。族色（柱晶蓝、片晶红、Parry 深蓝）只给族。
SUN = S.sun
NEUTRAL = S.pair['a']
PAIR = S.pair
PAIR_DASH = S.pair_dash
EDGE = S.sphere_edge
GUIDE = S.guide
CAMERA = Camera(azimuth=-55, elevation=24, distance=6)
SURFACE = S.surfaces['neutral'].base
PAPER = S.paper
CRYSTAL = crystal_preset()


def canvas(size=(11.8, 6.6)):
    P.apply_style()
    return plt.figure(figsize=size)


def globe(ax, camera=CAMERA):
    # 单位球的切线锥在原点像平面上的半径，与透视经纬网使用同一相机。
    radius = camera.distance / np.sqrt(camera.distance**2 - 1)
    ax.add_patch(Circle((0, 0), radius, facecolor=SURFACE, alpha=0.24,
                        edgecolor='none', zorder=0))
    graticule(ax, Sphere(), camera=camera, preset=PRESETS['default'],
              lat_step=30, lon_step=45)
    ax.add_patch(Circle((0, 0), radius, facecolor='none', edgecolor=EDGE, lw=1.0, zorder=5))
    finish(ax, (-1.5, 1.5), (-1.4, 1.4))


def arrow(ax, start, end, color=NEUTRAL, lw=1.6, **kwargs):
    return ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                       mutation_scale=13, shrinkA=0, shrinkB=0), **kwargs)


def crystal(ax, rotation, camera=CAMERA, height=1.5, face_numbers=(1, 3)):
    poly = HexPrism(a=0.65, h=height).transformed(rotation=rotation)
    render_crystal(ax, poly, camera=camera, preset=CRYSTAL, face_numbers=face_numbers)
    finish(ax, (-1.4, 1.4), (-1.4, 1.4))
    return poly


def save(fig, name, out=None):
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / f'img/{name}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


def cli(main):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
