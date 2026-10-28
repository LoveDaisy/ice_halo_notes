# 图 3a/3b/3d：在图 3c 的同一个只读地形上添加姿态族图层。
import argparse
from pathlib import Path

import numpy as np

import fig_plate_terrain as T

COLUMN_HEIGHT = 20.0
TITLES = {
    'domain': ('一条光路，一张地形图', '3–5 光路 · 等值线上的光点离太阳一样远；留白处没有可行出射方向。'),
    'random': ('随机取向：整个球都可以到达', '可取方向不等于能够出光：整球可取，只有蓝色光学域有地形数值。'),
    'column': ('柱晶：太阳改变带宽，不会把赤道排除', '太阳高度 h = 20° · 橙色边界之间是柱晶可取的带，全局最低点仍在带内。'),
}
NAMES = {'domain': 'terrain_domain', 'random': 'random_terrain', 'column': 'column_terrain'}


def accessible(u, kind):
    u = np.asarray(u)
    if kind == 'column':
        return np.abs(u[..., 2]) <= np.cos(np.radians(COLUMN_HEIGHT)) + 1e-12
    if kind in ('domain', 'random'):
        return np.ones(u.shape[:-1], dtype=bool)
    raise ValueError(kind)


def scene_data(kind, size=801):
    x, y, u, d = T.base_terrain(size)
    return x, y, u, d, accessible(u, kind) & np.isfinite(u).all(axis=-1)


def main(kind, out=None):
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
    elif kind == 'column':
        width = 90 - COLUMN_HEIGHT
        for h in (-width, width):
            T.visible_curve(ax, T.C.unit_from(h, az), color=accent, lw=1.5, zorder=5)
        # 连接上下边界的经线只表示可取带，不改变底图的标量值。
        el = np.linspace(-width, width, 721)
        for a in (250, 310, 10):
            T.visible_curve(ax, T.C.unit_from_grid(el, np.full_like(el, a)),
                            color=accent, lw=0.8, ls=(0, (2, 3)), zorder=5)
        T.visible_curve(ax, T.C.unit_from(0, az), color=accent, lw=1.6, zorder=5)
        xy = T.project(T.C.unit_from(width, T.VIEW_AZ))[:2]
        ax.annotate('可取带的北界：70°', xy=xy, xytext=(1.22, 1.01),
                    color=ink, fontsize=10.5, va='center',
                    arrowprops=dict(arrowstyle='-', color=edge, lw=0.7))
        ax.text(1.22, 0.74, '南界：−70°\n赤道始终在带内', color=ink, fontsize=11, linespacing=1.7)
        ax.text(-1.1, 0.52, '橙虚线：\n带内的经线', ha='right', color=ink, fontsize=10)
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
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / f'img/{NAMES[kind]}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    T.plt.close(fig)
    print(out)


def cli(kind):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(kind, parser.parse_args().output)
