# 图 4b：欧拉角等间距相对 Haar 的密度在极点发散 → ../img/euler_density.png。
import numpy as np

import _orientation_fig as F


def relative_density(beta):
    return 2 / (np.pi * np.sin(np.radians(beta)))


def cap_ratio(delta):
    d = np.radians(delta)
    return (d/np.pi) / np.sin(d/2)**2


def main(out=None):
    fig = F.canvas(size=(10.8, 5.8))
    ax = fig.add_axes([0.1, 0.14, 0.86, 0.82])
    beta = np.linspace(0.15, 179.85, 2401)
    ax.plot(beta, relative_density(beta), color=F.NEUTRAL, lw=2.0)
    ax.axhline(1, color=F.EDGE, lw=0.8, linestyle='--')
    ax.text(118, 1.14, '相对密度 = 1', color=F.INK, fontsize=12)
    ax.scatter([90], [2/np.pi], color=F.NEUTRAL, s=40, edgecolor=F.PAPER, zorder=4)
    ax.annotate('赤道处 2/π', (90, 2/np.pi), (90, 2.1), ha='center', color=F.INK, fontsize=12,
                arrowprops=dict(arrowstyle='-', lw=0.8, color=F.EDGE))
    ax.text(90, 4.5, r'$\rho_{\mathrm{Euler}}/\rho_{\mathrm{Haar}}=\dfrac{2}{\pi\sin\beta}$',
            ha='center', color=F.INK, fontsize=20)
    for x, target, align in ((4, 15, 'left'), (176, 165, 'right')):
        F.arrow(ax, (x, 5.7), (x, 6.55), F.NEUTRAL)
        ax.text(target, 6.1, '趋于 ∞', color=F.INK, fontsize=13, ha=align)
    ax.set(xlim=(0, 180), ylim=(0, 7))
    ax.set_xlabel('c 轴天顶角 β', fontsize=13)
    ax.set_ylabel('相对 Haar 的密度', fontsize=13)
    ax.set_xticks([0, 45, 90, 135, 180], ['0°', '45°', '90°', '135°', '180°'])
    ax.set_yticks([0, 1, 2, 4, 6])
    ax.tick_params(labelsize=12)
    F.save(fig, 'euler_density', out)


if __name__ == '__main__':
    F.cli(main)
