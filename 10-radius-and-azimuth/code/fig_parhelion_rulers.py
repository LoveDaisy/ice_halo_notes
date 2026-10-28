# 图 5：幻日角距离与方位差的两把尺 → ../img/parhelion_rulers.png。
import argparse
from pathlib import Path

import numpy as np

import check_parhelion as C
from fig_plate_terrain import P, plt

COLORS = {'distance': P.PAL['arc_roll'], 'azimuth': P.PAL['face_5'],
          'ink': P.PAL['ink_soft'], 'guide': P.PAL['reference']}


def curve_data(heights=None):
    if heights is None:
        heights = np.r_[np.linspace(0, C.critical_height() - 0.001, 801),
                        C.critical_height(), 62., 65.]
    heights = np.asarray(heights, dtype=float)
    azimuth = np.full(heights.shape, np.nan)
    distance = np.full(heights.shape, np.nan)
    for index, h in np.ndenumerate(heights):
        _, delta = C.bravais(h)
        if h < C.critical_height() and delta is not None:
            azimuth[index] = delta
            distance[index] = C.spherical_distance(h, delta)
    return heights, distance, azimuth


def main(out=None):
    P.apply_style()
    ink = COLORS['ink']
    h, d, delta = curve_data()
    fig, ax = plt.subplots(figsize=(10.4, 6.6))
    fig.subplots_adjust(left=0.10, right=0.96, bottom=0.15, top=0.79)
    fig.text(0.06, 0.93, '同一点出发，两把尺子逐渐分开', fontsize=17, color=ink)
    fig.text(0.06, 0.875, '3–5 幻日的最近处 · 天球角距离与水平方位差共用同一个角度轴。', fontsize=11, color=ink)
    ax.plot(h, d, color=COLORS['distance'], lw=2, label='角距离 D（天球上）')
    ax.plot(h, delta, color=COLORS['azimuth'], lw=2, ls=(0, (5, 2)), label='方位差 Δφ（水平投影）')
    ax.axhline(22, color=COLORS['guide'], lw=0.9, zorder=0)
    ax.text(2, 24.7, '22° 参照', color=ink, fontsize=9.5)
    hc = C.critical_height()
    ax.axvspan(hc, 65, color=COLORS['guide'], alpha=0.3, zorder=0)
    ax.axvline(hc, color=ink, lw=0.8, ls=(0, (3, 3)))
    ax.text(hc-0.7, 121, f'临界 {hc:.2f}°', color=ink, ha='right', fontsize=10.5)
    ax.text(63.1, 65, '无可行光路', color=ink, ha='center', rotation=90, fontsize=10)
    _, dd, pp = curve_data([40.])
    for y, color, text, offset in [(dd[0], COLORS['distance'], f'D = {dd[0]:.2f}°', (28, 11)),
                                    (pp[0], COLORS['azimuth'], f'Δφ = {pp[0]:.2f}°', (18, 61))]:
        ax.scatter(40, y, s=46, color=color, edgecolor='white', lw=1.2, zorder=5)
        ax.annotate(text, xy=(40, y), xytext=offset, color=ink, fontsize=11,
                    arrowprops=dict(arrowstyle='-', color=color, lw=0.8))
    ax.text(52, 31, '角距离 D', color=ink, fontsize=11)
    ax.text(49, 83, '方位差 Δφ', color=ink, fontsize=11)
    ax.legend(loc='upper left', handlelength=3)
    ax.set(xlim=(0, 65), ylim=(0, 128), xlabel='太阳高度 h（°）', ylabel='角度（°）')
    ax.set_xticks(np.arange(0, 66, 10))
    ax.set_yticks(np.arange(0, 121, 20))
    ax.grid(axis='y', color=COLORS['guide'], lw=0.5, zorder=0)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/parhelion_rulers.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
