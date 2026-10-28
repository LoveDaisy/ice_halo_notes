# 图 3c 候选：同一 3–5 地形上的片晶纬线与最低点 → ../img/plate_terrain.png。
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from halo_notes.draw.projection import Camera

import check_parhelion as C

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_ch8_plot", ROOT / "08-wedge-times-fold/code/_ch8_plot.py"
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
HEIGHTS = (0.0, 20.0, 40.0, 60.0, 65.0)
VIEW_AZ, VIEW_EL = 310.0, 12.0
CAMERA = Camera(azimuth=VIEW_AZ, elevation=VIEW_EL,
                projection="perspective", distance=8.0)
LEVELS = (22, 25, 30, 40, 50)
COLORS = {
    "ink": P.PAL["ink_soft"],
    "grid": P.PAL["reference"],
    "latitude": P.PAL["face_5"],
    "edge": P.PAL["ice_edge"],
    "surface": P.PAL["background"],
}
# 每套都是单调明度标尺，不叠加球面灯光；D 的数值与定义域不随外观变化。
RAMPS = {
    "original": (P.PAL["ice"], P.PAL["face_4"], P.PAL["ink_soft"]),
    "chalk": ("#EFEDE7", "#AAA69B", "#5B5953"),
    "mineral": ("#E5EEEB", "#92B1A8", "#385E55"),
}


def distance_cmap(style="original"):
    return LinearSegmentedColormap.from_list(f"distance_{style}", RAMPS[style])


def project(u, camera=CAMERA):
    """保留输入形状，最后一维为 Camera 的 (x, y, depth)。"""
    points = np.asarray(u)
    xy, depth = camera.project(points.reshape(-1, 3))
    return np.column_stack([xy, depth]).reshape(points.shape)


def sphere_visible(u, camera=CAMERA):
    """单位球面法向为 u；透视可见域不是 depth >= 0 的半球。"""
    points = np.asarray(u)
    view = camera.view_vector(points.reshape(-1, 3)).reshape(points.shape)
    return np.sum(points * view, axis=-1) >= -1e-12


def sphere_hit(x, y, camera=CAMERA):
    """原点像平面的 (x,y) 发回同一个相机点，取射线与单位球的近交点。

    未命中返回 NaN；射线用 camera.position 作共同起点，而非逐像素平移起点。
    """
    x, y = np.broadcast_arrays(x, y)
    plane = x[..., None] * camera.right + y[..., None] * camera.cam_up
    ray = plane - camera.position
    ray /= np.linalg.norm(ray, axis=-1, keepdims=True)
    b = ray @ camera.position
    discriminant = b * b - (camera.position @ camera.position - 1)
    hit = (discriminant >= -1e-12) & (b < 0)
    distance = -b - np.sqrt(np.maximum(discriminant, 0))
    u = camera.position + distance[..., None] * ray
    return np.where(hit[..., None], u, np.nan)


def silhouette(camera=CAMERA):
    """相机到单位球的切线圈：u·camera.position = 1。"""
    angle = np.linspace(0, 2 * np.pi, 1441)
    depth = 1 / camera.distance
    ring = (np.cos(angle)[:, None] * camera.right
            + np.sin(angle)[:, None] * camera.cam_up)
    return depth * camera.view_dir + np.sqrt(1 - depth**2) * ring


def image_radius(camera=CAMERA):
    """切线圈在 Camera 原点像平面上的半径，不是单位圆。"""
    return camera.distance / np.sqrt(camera.distance**2 - 1)


def terrain(size=801, camera=CAMERA):
    """透视像素中心的真实 u、D 及定义域；仅方向光学，不声称有能量。"""
    radius = image_radius(camera)
    step = 2 * radius / size
    t = -radius + (np.arange(size) + 0.5) * step
    x, y = np.meshgrid(t, t)
    u = sphere_hit(x, y, camera)
    inside = np.isfinite(u).all(axis=-1)
    d = np.full(x.shape, np.nan)
    d[inside] = C.dp(u[inside])[0]
    return x, y, u, d


def latitude_minimum(h):
    az = np.arange(0, 360, C.THETA_STEP)
    d, _ = C.dp(C.unit_from(h, az))
    if not np.isfinite(d).any():
        return None
    k = int(np.nanargmin(d))
    a = C.golden_min(lambda a: C.dp(C.unit_from(h, a))[0][0],
                     az[k] - C.THETA_STEP, az[k] + C.THETA_STEP)
    u = C.unit_from(h, a)
    return u, float(C.dp(u)[0][0])


def visible_curve(ax, u, **kwargs):
    q = project(u)
    xy = np.where(sphere_visible(u)[:, None], q[:, :2], np.nan)
    return ax.plot(xy[:, 0], xy[:, 1], **kwargs)


def main(style="original", out=None):
    if style != "original" and out is None:
        raise ValueError("候选变体必须显式指定输出路径，不能覆盖原图")
    P.apply_style()
    ink, guide = COLORS["ink"], COLORS["grid"]
    accent = COLORS["latitude"]
    cmap = distance_cmap(style)
    norm = Normalize(21.0, 53.0)
    fig = plt.figure(figsize=(10.4, 7.6))
    ax = fig.add_axes([0.045, 0.20, 0.92, 0.68])
    ax.set_aspect("equal")
    x, y, _, d = terrain()
    radius = image_radius()
    ax.imshow(np.ma.masked_invalid(d), origin="lower",
              extent=(-radius, radius, -radius, radius),
              cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    az = np.linspace(0, 360, 1441)
    for longitude in np.arange(0, 360, 30):
        el = np.linspace(-90, 90, 721)
        visible_curve(ax, C.unit_from_grid(el, np.full_like(el, longitude)),
                      color=guide, lw=0.55, zorder=2)
    for h in (-60, -30):
        visible_curve(ax, C.unit_from(h, az), color=guide, lw=0.55, zorder=2)
    contours = ax.contour(x, y, np.ma.masked_invalid(d), levels=LEVELS,
                          colors=ink, linewidths=0.7, alpha=0.8, zorder=3)
    # 等值线标注放在未叠片晶纬线的南半球，避免与最低点争夺视线。
    for level, position in [(25, (0.2, -0.63)), (30, (-0.35, -0.68)), (40, (-0.52, -0.62))]:
        ax.clabel(contours, levels=[level], inline=True, fontsize=9,
                  fmt=lambda v: f"{v:g}°", manual=[position])
    outline = project(silhouette())
    ax.plot(outline[:, 0], outline[:, 1], color=COLORS["edge"], lw=0.8, zorder=4)
    targets = {-0.0: -0.21, 20.0: 0.14, 40.0: 0.49, 60.0: 0.84, 65.0: 1.12}
    for h in HEIGHTS:
        row = latitude_minimum(h)
        visible_curve(ax, C.unit_from(h, az), color=accent if row else ink,
                      lw=1.5 if row else 1.1, ls="-" if row else (0, (4, 3)), zorder=5)
        if row is None:
            xy = project(C.unit_from(h, VIEW_AZ))[:2]
            text = "h = 65°\n整圈已在定义域之外"
        else:
            u, value = row
            xy = project(u)[:2]
            ax.scatter(*xy, s=45, c=ink, edgecolor=COLORS["surface"],
                       linewidth=1.5, zorder=7)
            text = f"h = {h:.0f}°    最近 {value:.2f}°"
            if h == 0:
                text += "\n与全局最低点重合"
        target = targets[h]
        ax.plot([xy[0] + 0.025, 1.11, 1.19], [xy[1], target, target],
                color=COLORS["edge"], lw=0.7, zorder=6)
        ax.text(1.23, target, text, fontsize=11, color=ink, va="center", linespacing=1.6)
    pole = project(np.array([0, 0, 1.0]))[:2]
    ax.text(pole[0] - 0.04, pole[1] + 0.055, "c 轴", color=ink, ha="right", fontsize=10)
    ax.text(-1.06, 0.67, "留白：\n无可行出射方向", ha="right", va="center", color=ink, fontsize=9.5)
    ax.text(-0.86, -0.35, "u 球", color=ink, fontsize=15)
    ax.set_xlim(-1.47, 2.48)
    ax.set_ylim(-1.08, 1.28)
    ax.axis("off")
    fig.text(0.055, 0.935, "片晶：太阳越高，纬线上的最低点也越高", fontsize=16, color=ink)
    fig.text(0.055, 0.884, "同一条 3–5 光路 · 橙线是片晶可取的纬度圆，圆点是各纬线能到达的最近处。",
             fontsize=10.5, color=ink)
    cax = fig.add_axes([0.22, 0.115, 0.32, 0.018])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation="horizontal", ticks=[22, 30, 40, 50])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=9, length=3, color=ink)
    cb.set_label("地形数值 D：光点离太阳的角距离（°）", fontsize=10, color=ink)
    fig.text(0.67, 0.115, "着色表示角距离，不是亮度。", fontsize=9.5, color=ink)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / "img/plate_terrain.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", choices=RAMPS, default="original")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    main(args.style, args.output)
