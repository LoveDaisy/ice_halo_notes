# 图 3a/3b/3d：在图 3c 的同一个只读地形上添加姿态族图层。
import argparse
from pathlib import Path

import numpy as np
from matplotlib import patheffects

import fig_plate_terrain as T

COLUMN_HEIGHT = 70.0
BAND_HEIGHTS = (20.0, 45.0, COLUMN_HEIGHT)
NAMES = {'domain': 'terrain_domain', 'random': 'random_terrain', 'column': 'column_terrain'}


def accessible(u, kind, height=COLUMN_HEIGHT):
    u = np.asarray(u)
    if kind == 'column':
        return np.abs(u[..., 2]) <= np.cos(np.radians(height)) + 1e-12
    if kind in ('domain', 'random'):
        return np.ones(u.shape[:-1], dtype=bool)
    raise ValueError(kind)


def scene_data(kind, size=801):
    x, y, u, d = T.base_terrain(size)
    return x, y, u, d, accessible(u, kind) & np.isfinite(u).all(axis=-1)


def band_layers(ax, height, *, size=801, small=False):
    """柱晶可取带：带外地形压淡、带内留白处淡染族色、族色边界线；不把族色叠在地形上。"""
    from matplotlib.colors import to_rgba

    _, _, u, d = T.base_terrain(size)
    on_sphere = np.isfinite(u).all(axis=-1)
    band = accessible(u, 'column', height) & on_sphere
    domain = np.isfinite(d)
    radius = T.image_radius()
    extent = (-radius, radius, -radius, radius)
    wash = np.zeros((*band.shape, 4))
    wash[domain & ~band] = to_rgba(T.COLORS['surface'], 0.72)
    ax.imshow(wash, origin='lower', extent=extent, interpolation='nearest',
              zorder=4).set_gid('column-outside-wash')
    tint = np.zeros((*band.shape, 4))
    tint[band & (~domain if not small else np.ones_like(band))] = to_rgba(T.COLORS['column'], 0.16)
    artist = ax.imshow(tint, origin='lower', extent=extent, interpolation='nearest', zorder=4)
    artist.set_gid('column-accessible-band')
    az = np.linspace(0, 360, 1441)
    for latitude in (height - 90, 90 - height):
        line, = T.visible_curve(ax, T.C.unit_from(latitude, az),
                               color=T.COLORS['column'], lw=1.2 if small else 1.8, zorder=5)
        line.set_gid('column-band-boundary')
    return band


def make_column_figure():
    T.apply_style()
    ink = T.COLORS['ink']
    fig = T.plt.figure(figsize=(9.6, 6.4))
    ax = fig.add_axes([0.0, 0.13, 0.68, 0.85], label='column-terrain')
    cmap, norm = T.draw_base(ax)
    band_layers(ax, COLUMN_HEIGHT)
    az = np.linspace(0, 360, 1441)
    T.visible_curve(ax, T.C.unit_from(0, az), color=ink, lw=0.9, ls=(0, (4, 3)), zorder=6)
    u, value = T.latitude_minimum(0)
    xy = T.project(u)[:2]
    ax.scatter(*xy, s=50, c=ink, edgecolor=T.COLORS['surface'], linewidth=1.5, zorder=7)
    halo = [patheffects.withStroke(linewidth=3, foreground=T.COLORS['surface'])]
    ax.text(xy[0], xy[1] + 0.15, f'全局最低点 {value:.2f}°', fontsize=13, color=ink,
            ha='center', va='bottom', path_effects=halo, zorder=8)
    for latitude, text in ((90 - COLUMN_HEIGHT, f'+{90 - COLUMN_HEIGHT:g}°'),
                           (COLUMN_HEIGHT - 90, f'−{90 - COLUMN_HEIGHT:g}°')):
        x, y = T.limb_point(latitude)
        ax.text(x + 0.05, y, text, fontsize=13, color=T.COLORS['column'], va='center')
    ax.text(-1.0, 1.12, f'太阳高度 {COLUMN_HEIGHT:g}°', fontsize=13, color=ink)
    ax.set(xlim=(-1.12, 1.75), ylim=(-1.1, 1.22), aspect='equal')
    ax.axis('off')
    for i, height in enumerate(BAND_HEIGHTS):
        small = fig.add_axes([0.665, 0.66 - i*0.285, 0.17, 0.255], label=f'band-{height:g}')
        radius = T.image_radius()
        small.add_patch(T.plt.Circle((0, 0), radius, facecolor=T.COLORS['surface'],
                                    edgecolor=T.COLORS['edge'], lw=0.8, zorder=0))
        band_layers(small, height, size=301, small=True)
        T.visible_curve(small, T.C.unit_from(0, az), color=ink, lw=0.6, ls=(0, (3, 2.5)), zorder=5)
        small.set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1), aspect='equal')
        small.axis('off')
        small.text(1.2, 0, f'{height:g}°', fontsize=13, color=ink, va='center')
    fig.text(0.75, 0.975, '太阳高度', fontsize=12, color=ink, ha='center', va='top')
    cax = fig.add_axes([0.12, 0.085, 0.38, 0.022])
    cb = fig.colorbar(T.plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation='horizontal', ticks=[22, 30, 40, 50])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=11, length=3, color=ink)
    cb.set_label('角距离 D（°）', fontsize=12, color=ink)
    fig.text(0.665, 0.075, r'$\mathrm{可取带\ }|u_z| \leq \cos h$', fontsize=13,
             color=T.COLORS['column'])
    return fig


def main(kind, out=None):
    if kind == 'column':
        fig = make_column_figure()
        save(fig, kind, out)
        return
    fig = make_sphere_figure(kind)
    save(fig, kind, out)


def make_sphere_figure(kind):
    """3a 只画地形本身；3b 在同一底图上用随机族色把整球（含留白处）圈为可取，并标出全局最低点。"""
    T.apply_style()
    ink = T.COLORS['ink']
    fig = T.plt.figure(figsize=(8.0, 6.6))
    ax = fig.add_axes([0.0, 0.12, 1.0, 0.86], label=f'{kind}-terrain')
    cmap, norm = T.draw_base(ax)
    halo = [patheffects.withStroke(linewidth=3, foreground=T.COLORS['surface'])]
    if kind == 'random':
        from matplotlib.colors import to_rgba
        _, _, u, d = T.base_terrain()
        radius = T.image_radius()
        tint = np.zeros((*d.shape, 4))
        tint[np.isfinite(u).all(axis=-1) & ~np.isfinite(d)] = to_rgba(T.COLORS['random'], 0.2)
        ax.imshow(tint, origin='lower', extent=(-radius, radius, -radius, radius),
                  interpolation='nearest', zorder=1).set_gid('random-accessible-sphere')
        rim = T.project(T.silhouette())
        ax.plot(rim[:, 0], rim[:, 1], color=T.COLORS['random'], lw=2.4,
                zorder=5)[0].set_gid('random-accessible-rim')
        u, value = T.latitude_minimum(0)
        xy = T.project(u)[:2]
        ax.scatter(*xy, s=50, c=ink, edgecolor=T.COLORS['surface'], linewidth=1.5, zorder=7)
        ax.text(xy[0], xy[1] + 0.17, f'全局最低点 {value:.2f}°', fontsize=13, color=ink,
                ha='center', va='bottom', path_effects=halo, zorder=8)
        blank = '整球可取\n浅灰处无出射方向'
    else:
        blank = '留白：\n无可行出射方向'
    pole = T.project(np.array([0., 0., 1.]))[:2]
    ax.text(pole[0] - 0.04, pole[1] + 0.055, 'c 轴', color=ink, ha='right', fontsize=12)
    ax.text(-1.06, 0.45, blank, ha='right', va='center', color=ink, fontsize=12, linespacing=1.5)
    ax.text(-1.0, -0.95, 'u 球', color=ink, fontsize=14, ha='right')
    ax.set(xlim=(-1.95, 1.2), ylim=(-1.08, 1.28))
    ax.axis('off')
    cax = fig.add_axes([0.3, 0.075, 0.44, 0.022])
    cb = fig.colorbar(T.plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation='horizontal', ticks=[22, 30, 40, 50])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=11, length=3, color=ink)
    cb.set_label('角距离 D（°）', fontsize=12, color=ink)
    return fig


def save(fig, kind, out):
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / f'img/{NAMES[kind]}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    T.plt.close(fig)
    print(out)


def cli(kind):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(kind, parser.parse_args().output)
