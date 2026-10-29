# 图 3a/3b/3d：在图 3c 的同一个只读地形上添加姿态族图层。
import argparse
from pathlib import Path

import numpy as np

import fig_plate_terrain as T

COLUMN_HEIGHT = 70.0
BAND_HEIGHTS = (20.0, 45.0, COLUMN_HEIGHT)
TITLES = {
    'domain': ('一条光路，一张地形图', '3–5 光路 · 等值线上的光点离太阳一样远；留白处没有可行出射方向。'),
    'random': ('随机取向：整个球都可以到达', '可取方向不等于能够出光：整球可取，只有蓝色光学域有地形数值。'),
}
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


def band_overlay(ax, height, *, size=801, alpha=0.22):
    from matplotlib.colors import to_rgba

    _, _, u, _ = T.base_terrain(size)
    mask = accessible(u, 'column', height) & np.isfinite(u).all(axis=-1)
    rgba = np.zeros((*mask.shape, 4))
    rgba[mask] = to_rgba(T.COLORS['latitude'], alpha)
    radius = T.image_radius()
    artist = ax.imshow(rgba, origin='lower', extent=(-radius, radius, -radius, radius),
                       interpolation='nearest', zorder=4)
    artist.set_gid('column-accessible-band')
    az = np.linspace(0, 360, 1441)
    for latitude in (height - 90, 90 - height):
        line, = T.visible_curve(ax, T.C.unit_from(latitude, az),
                               color=T.COLORS['latitude'], lw=1.3, zorder=5)
        line.set_gid('column-band-boundary')
    return artist


def make_column_figure():
    T.P.apply_style()
    ink, edge, accent = T.COLORS['ink'], T.COLORS['edge'], T.COLORS['latitude']
    fig = T.plt.figure(figsize=(11.6, 8.2))
    fig.text(0.045, 0.94, '柱晶：太阳越高，可取带越窄', fontsize=18, color=ink)
    fig.text(0.045, 0.89, '赤道始终在带内，所以始终能够触及全局最低点。', fontsize=11.5, color=ink)
    ax = fig.add_axes([0.03, 0.21, 0.65, 0.62], label='column-terrain')
    cmap, norm = T.draw_base(ax)
    band_overlay(ax, COLUMN_HEIGHT)
    az = np.linspace(0, 360, 1441)
    T.visible_curve(ax, T.C.unit_from(0, az), color=accent, lw=1.5, zorder=6)
    u, value = T.latitude_minimum(0)
    xy = T.project(u)[:2]
    ax.scatter(*xy, s=50, c=ink, edgecolor=T.COLORS['surface'], linewidth=1.5, zorder=7)
    ax.annotate(f'全局最低点\nD = {value:.2f}°', xy=xy, xytext=(1.08, -0.28),
                fontsize=11, color=ink, va='center', linespacing=1.6,
                arrowprops=dict(arrowstyle='-', color=edge, lw=0.8))
    north = T.project(T.C.unit_from(90-COLUMN_HEIGHT, T.VIEW_AZ))[:2]
    ax.annotate('纬度 +20°', xy=north, xytext=(1.06, 0.57), fontsize=10.5, color=ink,
                arrowprops=dict(arrowstyle='-', color=edge, lw=0.8))
    south = T.project(T.C.unit_from(COLUMN_HEIGHT-90, T.VIEW_AZ))[:2]
    ax.annotate('纬度 −20°', xy=south, xytext=(1.06, -0.65), fontsize=10.5, color=ink,
                arrowprops=dict(arrowstyle='-', color=edge, lw=0.8))
    ax.text(-0.93, 1.11, f'h = {COLUMN_HEIGHT:g}°（已超过片晶临界高度）', fontsize=11, color=ink)
    ax.set(xlim=(-1.15, 1.92), ylim=(-1.09, 1.23), aspect='equal')
    ax.axis('off')
    for i, height in enumerate(BAND_HEIGHTS):
        small = fig.add_axes([0.75, 0.63 - i*0.205, 0.19, 0.185], label=f'band-{height:g}')
        radius = T.image_radius()
        small.add_patch(T.plt.Circle((0, 0), radius, facecolor=T.P.PAL['ice'],
                                    edgecolor=edge, lw=0.75, zorder=0))
        band_overlay(small, height, size=301, alpha=0.33)
        T.visible_curve(small, T.C.unit_from(0, az), color=edge, lw=0.7, ls='--', zorder=5)
        small.set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1), aspect='equal')
        small.axis('off')
        small.text(1.15, 0, f'h = {height:g}°\n±{90-height:g}°', fontsize=10.5,
                   color=ink, va='center', linespacing=1.8)
    fig.text(0.76, 0.84, '只看可取带', fontsize=11, color=ink)
    cax = fig.add_axes([0.13, 0.145, 0.33, 0.017])
    cb = fig.colorbar(T.plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation='horizontal', ticks=[22, 30, 40, 50])
    cb.outline.set_visible(False)
    cb.set_label('蓝色底图：角距离 D（°）', fontsize=10, color=ink)
    fig.text(0.59, 0.12, '橙色半透明层：柱晶可取方向\n|u_z| ≤ cos h；不是亮度，也不改变底图。',
             fontsize=10.5, color=ink, linespacing=1.7)
    fig.text(0.045, 0.05, '小图与大图使用同一透视相机；虚线为赤道。', fontsize=10, color=ink)
    return fig


def main(kind, out=None):
    if kind == 'column':
        fig = make_column_figure()
        save(fig, kind, out)
        return
    T.P.apply_style()
    ink, edge, accent = T.COLORS['ink'], T.COLORS['edge'], T.COLORS['latitude']
    fig = T.plt.figure(figsize=(10.4, 7.6))
    ax = fig.add_axes([0.045, 0.20, 0.92, 0.68])
    cmap, norm = T.draw_base(ax)
    az = np.linspace(0, 360, 1441)
    for h in (0, 30, 60):
        T.visible_curve(ax, T.C.unit_from(h, az), color=T.COLORS['grid'], lw=0.55, zorder=2)
    if kind == 'random':
        rim = T.project(T.silhouette())
        ax.plot(rim[:, 0], rim[:, 1], color=accent, lw=1.6, zorder=5)
        ax.annotate('整球可取', xy=(-0.82, 0.58), xytext=(-1.10, 0.82),
                    ha='right', color=ink, fontsize=11,
                    arrowprops=dict(arrowstyle='-', color=accent, lw=1.2))
    u, value = T.latitude_minimum(0)
    xy = T.project(u)[:2]
    ax.scatter(*xy, s=45, c=ink, edgecolor=T.COLORS['surface'], linewidth=1.5, zorder=7)
    ax.plot([xy[0]+0.025, 1.11, 1.19], [xy[1], -0.21, -0.21], color=edge, lw=0.7, zorder=6)
    suffix = {'domain': '赤道上的全局最低点', 'random': '随机取向可以到达', 'column': '带内最低点 = 全局最低点'}[kind]
    ax.text(1.23, -0.21, f'最近 {value:.2f}°\n{suffix}', color=ink, fontsize=11,
            va='center', linespacing=1.7)
    pole = T.project(np.array([0., 0., 1.]))[:2]
    ax.text(pole[0]-0.04, pole[1]+0.055, 'c 轴', color=ink, ha='right', fontsize=10)
    ax.text(-0.86, -0.35, 'u 球', color=ink, fontsize=15)
    if kind == 'domain':
        ax.text(-1.06, 0.67, '留白：\n无可行出射方向', ha='right', color=ink, fontsize=9.5)
    ax.set(xlim=(-1.47, 2.48), ylim=(-1.08, 1.28))
    ax.axis('off')
    title, subtitle = TITLES[kind]
    fig.text(0.055, 0.935, title, fontsize=16, color=ink)
    fig.text(0.055, 0.884, subtitle, fontsize=10.5, color=ink)
    cax = fig.add_axes([0.22, 0.115, 0.32, 0.018])
    cb = fig.colorbar(T.plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation='horizontal', ticks=[22, 30, 40, 50])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=9, length=3, color=ink)
    cb.set_label('地形数值 D：光点离太阳的角距离（°）', fontsize=10, color=ink)
    fig.text(0.67, 0.115, '着色表示角距离，不是亮度。', fontsize=9.5, color=ink)
    save(fig, kind, out)


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
