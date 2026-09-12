# 产出 ../img/Slerp_factor_explanation.png：SLERP 系数的几何解释——单位圆上 p₀、p₁ 夹角 Ω，p 在弧上与 p₀ 夹角 θ，
# p = (sin(Ω−θ)·p₀ + sin θ·p₁)/sin Ω；p₁ 在 ⊥p₀ 方向的投影长 sin Ω，p 分解成 cos θ·p₀ + sin θ·⊥p₀（黄虚线）。
# 重画 5.2（旧图 img/legacy/Slerp_factor_explanation.png 取自 wiki，CC 图；本图是自己的版本，1050×743）。
# 读者要看出：p 是 p₀、⊥p₀ 的组合，系数由 sin 比值决定；θ 从 0 到 Ω 时 p 沿弧从 p₀ 走到 p₁。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc

OUT = Path(__file__).resolve().parent.parent / "img" / "Slerp_factor_explanation.png"
WIDTH, HEIGHT, DPI = 1050, 743, 150  # = 旧图分辨率
RED, YELLOW, BLUE = "#B5173E", "#F2B400", "#1F77C8"
P0_DEG, OMEGA_DEG, THETA_DEG = 40.0, 42.0, 22.0   # p₀ 方位角、Ω、θ（示意用取值）
FS = 34


def unit(deg: float) -> np.ndarray:
    return np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])


def arrow(ax, tip, color, lw=4.0):
    ax.annotate("", xy=tip, xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=28,
                                                            shrinkA=0, shrinkB=0))


def main() -> None:
    om, th = np.radians(OMEGA_DEG), np.radians(THETA_DEG)
    p0, p1 = unit(P0_DEG), unit(P0_DEG + OMEGA_DEG)
    perp = unit(P0_DEG + 90)                                        # ⊥p₀：p₀ 在弧的方向转 90°
    p = (np.sin(om - th) * p0 + np.sin(th) * p1) / np.sin(om)      # SLERP 公式
    # 机械核验：‖p‖=1、∠(p₀,p)=θ、p₁ 在 ⊥p₀ 上的投影 = sin Ω、p = cos θ p₀ + sin θ ⊥p₀
    assert np.isclose(np.linalg.norm(p), 1.0)
    assert np.isclose(np.degrees(np.arccos(np.clip(p0 @ p, -1, 1))), THETA_DEG)
    assert np.isclose(p1 @ perp, np.sin(om)) and np.isclose(p1 @ p0, np.cos(om))
    assert np.allclose(p, np.cos(th) * p0 + np.sin(th) * perp)

    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.056, 1.056)          # 圆心在画面下方，只露上半圆（旧图构图）
    ax.set_ylim(-0.166, 1.33)

    t = np.linspace(0, np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), color="black", lw=5, solid_capstyle="round", zorder=1)
    ax.plot(0, 0, "o", color="black", ms=16, zorder=5)
    # p₀→p₁ 的弧（红，压在圆上）
    ta = np.radians(np.linspace(P0_DEG, P0_DEG + OMEGA_DEG, 100))
    ax.plot(np.cos(ta), np.sin(ta), color=RED, lw=7, solid_capstyle="round", zorder=2)
    # sin Ω：⊥p₀ 方向上长 sin Ω 的红段（向外挪一点，免得被蓝箭头盖住）+ p₁ 到它端点的红点线
    off = -0.04 * p0
    foot = np.sin(om) * perp
    ax.plot([off[0], foot[0] + off[0]], [off[1], foot[1] + off[1]], color=RED, lw=7, solid_capstyle="butt", zorder=3)
    ax.plot([p1[0], foot[0]], [p1[1], foot[1]], color=RED, lw=5, ls=(0, (0.8, 1.2)), dash_capstyle="round", zorder=2)
    # p 的分解：到 cos θ p₀ 与 sin θ ⊥p₀ 的黄点线
    for foot_p in (np.cos(th) * p0, np.sin(th) * perp):
        ax.plot([p[0], foot_p[0]], [p[1], foot_p[1]], color=YELLOW, lw=5, ls=(0, (0.8, 1.2)), dash_capstyle="round",
                zorder=2)
    # 四个向量
    arrow(ax, perp, BLUE)
    arrow(ax, p0, RED)
    arrow(ax, p1, RED)
    arrow(ax, p, YELLOW)
    # 角度弧：Ω（红，半径 0.3）与 θ（黄，半径 0.48）；Ω 标在两弧之间、θ 标在 θ 弧外
    ax.add_patch(Arc((0, 0), 0.6, 0.6, theta1=P0_DEG, theta2=P0_DEG + OMEGA_DEG, color=RED, lw=4, zorder=4))
    ax.add_patch(Arc((0, 0), 0.96, 0.96, theta1=P0_DEG, theta2=P0_DEG + THETA_DEG, color=YELLOW, lw=4, zorder=4))
    # 文字
    ax.text(*(0.39 * unit(P0_DEG + THETA_DEG / 2)), "Ω", color=RED, fontsize=FS, ha="center", va="center")
    ax.text(*(0.62 * unit(P0_DEG + THETA_DEG / 2)), "θ", color=YELLOW, fontsize=FS, ha="center", va="center")
    ax.text(*(1.1 * p0 + [0.02, 0.02]), "p₀", color=RED, fontsize=FS, ha="left", va="bottom")
    ax.text(*(1.1 * p1 + [-0.02, 0.02]), "p₁", color=RED, fontsize=FS, ha="right", va="bottom")
    ax.text(*(1.1 * p + [0.0, 0.03]), "p", color=YELLOW, fontsize=FS, ha="center", va="bottom")
    ax.text(*(1.08 * perp + [-0.02, 0.0]), "⊥p₀", color=BLUE, fontsize=FS, ha="right", va="bottom")
    mid = np.sin(om) / 2 * perp - 0.16 * p0
    ax.text(mid[0], mid[1], "sin Ω", color=RED, fontsize=FS, ha="center", va="center", rotation=P0_DEG + 90 - 180,
            rotation_mode="anchor")
    fig.savefig(OUT, dpi=DPI, facecolor="white")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
