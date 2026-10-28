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
from fig_column_torus import P

INK = P.PAL['ink_soft']
BLUE = P.PAL['arc_roll']
ORANGE = P.PAL['face_5']
EDGE = P.PAL['ice_edge']
CAMERA = Camera(azimuth=-55, elevation=24, distance=6)
# 晶体外观交给系列 PRESETS；球面/二维标记只从既有 palette 取语义色。
SURFACE = P.PAL['ice']
PAPER = 'white'


def canvas(title, subtitle, size=(11.8, 6.6)):
    P.apply_style()
    fig = plt.figure(figsize=size)
    fig.text(0.045, 0.935, title, fontsize=17, color=INK)
    fig.text(0.045, 0.88, subtitle, fontsize=10.5, color=INK)
    return fig


def globe(ax, camera=CAMERA):
    # 单位球的切线锥在原点像平面上的半径，与透视经纬网使用同一相机。
    radius = camera.distance / np.sqrt(camera.distance**2 - 1)
    ax.add_patch(Circle((0, 0), radius, facecolor=SURFACE, alpha=0.24,
                        edgecolor='none', zorder=0))
    graticule(ax, Sphere(), camera=camera, preset=PRESETS['default'],
              lat_step=30, lon_step=45)
    ax.add_patch(Circle((0, 0), radius, facecolor='none', edgecolor=EDGE, lw=1.0, zorder=5))
    finish(ax, (-1.5, 1.5), (-1.4, 1.4))


def arrow(ax, start, end, color=BLUE, lw=1.6, **kwargs):
    return ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                       mutation_scale=13, shrinkA=0, shrinkB=0), **kwargs)


def crystal(ax, rotation, camera=CAMERA, height=1.5):
    poly = HexPrism(a=0.65, h=height).transformed(rotation=rotation)
    render_crystal(ax, poly, camera=camera, preset=PRESETS['ice_filled'],
                   face_numbers=[1, 3])
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
