# 图 3 候选：Parry 共享圈的局部邻域与 Lowitz 摆角索引 → ../img/parry_neighborhood.png。
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb

import check_orientation_space as C
import fig_column_torus as T

P = T.P
RADIUS = T.MAJOR
WIDTH = 0.46  # 局部 a、b 的弧度半宽，小于 π/2，不延伸至欧拉角退化的片晶圈。
COLUMN = P.PAL["arc_roll"]
PARRY = P.PAL["face_5"]


def local_attitude(phi, a, b):
    """度制局部坐标；a=b=0 是 Parry，a=0 是柱晶，b=0 是 Lowitz。"""
    return C.Rz(float(phi)) @ C.Ry(-90.0 + float(a)) @ C.Rz(float(b))


def lowitz_attitude(phi, t):
    return C.Rz(float(phi)) @ C.Ry(float(t))


def local_model(phi, a, b):
    """邻域的欧氏显示坐标；径向 a、竖向 b 只作参数轴，不是物理方向/距离。"""
    p, a, b = np.broadcast_arrays(np.radians(phi), np.radians(a), np.radians(b))
    return np.stack([(RADIUS + a) * np.cos(p), (RADIUS + a) * np.sin(p), b], axis=-1)


def neighborhood_pixels(width=1401):
    """解析求两张薄面的最近射线交点；不用半透明面排序伪装相交关系。"""
    height = int(width * 4.2 / 6)
    x, y = np.meshgrid(np.linspace(-3, 3, width), np.linspace(-2.1, 2.1, height))
    origins = (x[..., None] * T.RIGHT + y[..., None] * T.UP + 5 * T.EYE).reshape(-1, 3)
    # Lowitz：b=0 的平面环带。
    plane = origins[:, 2] / T.EYE[2]
    plane_xyz = origins - plane[:, None] * T.EYE
    radial = np.linalg.norm(plane_xyz[:, :2], axis=1)
    plane[np.abs(radial - RADIUS) > WIDTH] = np.inf
    # 柱晶：a=0 的圆筒带；两根都检验，以免漏掉从内部看到的背壁。
    aa = T.EYE[0]**2 + T.EYE[1]**2
    bb = -2 * (origins[:, :2] @ T.EYE[:2])
    cc = np.sum(origins[:, :2]**2, axis=1) - RADIUS**2
    discriminant = bb**2 - 4 * aa * cc
    roots = [(-bb + sign * np.sqrt(np.maximum(discriminant, 0))) / (2 * aa)
             for sign in (-1, 1)]
    for depth in roots:
        z = origins[:, 2] - depth * T.EYE[2]
        depth[(discriminant < 0) | (np.abs(z) > WIDTH) | (depth < 0)] = np.inf
    depths = np.stack([plane, *roots])
    kinds = depths.argmin(axis=0)
    nearest = depths.min(axis=0)
    hit = np.isfinite(nearest)
    xyz = origins[hit] - nearest[hit, None] * T.EYE
    kinds = kinds[hit]
    radial = np.linalg.norm(xyz[:, :2], axis=1)
    is_column = kinds != 0
    rgb = np.tile(to_rgb("#E7E3DB"), (len(xyz), 1))
    normals = np.column_stack([xyz[:, 0] / RADIUS, xyz[:, 1] / RADIUS, np.zeros(len(xyz))])
    light = np.array([-0.35, -0.45, 0.82])
    light /= np.linalg.norm(light)
    brightness = 0.88 + 0.12 * np.abs(normals @ light)
    rgb[is_column] = brightness[is_column, None] * np.array(to_rgb("#BED0E2"))
    # 共享圈两侧的窄色带同属 a=b=0 附近；宽度只服务可读性。
    circle_distance = np.where(is_column, np.abs(xyz[:, 2]), np.abs(radial - RADIUS))
    coverage = np.clip((0.018 - circle_distance) / 0.006, 0, 1)
    rgb = rgb * (1 - coverage[:, None]) + np.array(to_rgb(PARRY)) * coverage[:, None]
    image = np.ones((len(origins), 3))
    image[hit] = rgb
    return image.reshape(height, width, 3), xyz, is_column


def main():
    P.apply_style()
    ink = P.PAL["ink_soft"]
    fig = plt.figure(figsize=(10.4, 8.8))
    fig.text(0.055, 0.95, "Parry：两张姿态曲面的共同一圈", fontsize=16, color=ink)
    fig.text(0.055, 0.91, "只展开 Parry 附近的一小条邻域：两张二维面沿同一个圆相交。",
             fontsize=10.5, color=ink)
    ax = fig.add_axes([0.025, 0.40, 0.95, 0.47])
    image, _, _ = neighborhood_pixels()
    ax.imshow(image, origin="lower", extent=(-3, 3, -2.1, 2.1), interpolation="lanczos")
    ax.set_aspect("equal")

    def leader(phi, a, b, target, text, ha="left"):
        xy = T.project(local_model(phi, a, b))[:2]
        ax.annotate(text, xy=xy, xytext=target, ha=ha, va="center", color=ink,
                    fontsize=11, linespacing=1.6,
                    arrowprops=dict(arrowstyle="-", color=P.PAL["ice_edge"], lw=0.8,
                                    connectionstyle="angle,angleA=0,angleB=90,rad=4"))

    leader(12, 0, 20, (2.9, 1.2), "柱晶\n沿竖带改变自转角 b")
    leader(-15, 23, 0, (2.9, -0.8), "Lowitz\n沿平带改变摆角 a")
    leader(-140, 0, 0, (-2.9, 0.8), "Parry\na = b = 0", ha="right")
    phi = np.linspace(-145, -130, 20)
    q = T.project(local_model(phi, 0, 0))
    ax.annotate("", xy=q[-1, :2], xytext=q[-5, :2],
                arrowprops=dict(arrowstyle="-|>", color=PARRY, lw=1.8, mutation_scale=16))
    ax.set_xlim(-4.5, 5.0)
    ax.set_ylim(-1.85, 1.85)
    ax.axis("off")
    fig.text(0.5, 0.415, "沿共享圆走：改变方位 φ　｜　径向与竖向只是局部参数，不是晶体的运动方向",
             ha="center", fontsize=9, color=ink)

    # 参数索引不是另一幅空间投影；每个刻度代表整条 φ 圈。
    fig.text(0.055, 0.345, "片晶在哪一圈？另看 Lowitz 的完整摆角", fontsize=12, color=ink)
    fig.text(0.055, 0.307, "下方每个位置代表一整圈方位 φ；不是把这些姿态圈压成空间中的点。",
             fontsize=9.5, color=ink)
    strip = fig.add_axes([0.12, 0.125, 0.76, 0.14])
    strip.plot([-180, 180], [0, 0], color=P.PAL["reference"], lw=1.2)
    strip.plot([-180, 0], [0, 0], color="#C6C0B5", lw=8, solid_capstyle="butt", zorder=1)
    strip.text(-90, -0.78, "roll 锁 0 的半环：只交出 Parry 一圈", ha="center", color=ink, fontsize=10)
    for t, label, color, marker in (
        (-180, "翻转片晶", ink, "o"), (-90, "Parry", PARRY, "o"),
        (0, "片晶", COLUMN, "o"), (90, "另一交圈", PARRY, "D"), (180, "翻转片晶", ink, "o"),
    ):
        strip.scatter(t, 0, s=60, marker=marker, facecolor="white", edgecolor=color, linewidth=1.8, zorder=3)
        strip.text(t, 0.52, label, ha="center", va="center", fontsize=10, color=ink)
        strip.text(t, -0.34, f"{t:+g}°" if t else "0°", ha="center", va="center", fontsize=9, color=ink)
    strip.set_xlim(-198, 198)
    strip.set_ylim(-1.05, 0.8)
    strip.axis("off")
    fig.text(0.5, 0.075, "全摆幅 t ∈ [−180°, 180°]，两端接回；原始点集有两条交圈。",
             ha="center", fontsize=9.5, color=ink)
    fig.text(0.5, 0.04, "两条交圈在 D₆ 对称意义下属于同一 Parry 族；上图只画其中一条附近，不画全局嵌入。",
             ha="center", fontsize=9.5, color=ink)
    out = Path(__file__).resolve().parents[1] / "img/parry_neighborhood.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
