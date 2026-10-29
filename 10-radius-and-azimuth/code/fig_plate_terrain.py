# 图 3c 候选：同一 3–5 地形上的片晶纬线与最低点 → ../img/plate_terrain.png。
from __future__ import annotations

import argparse
import importlib.util
from functools import lru_cache
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from halo_notes.draw.projection import Camera
from halo_notes.draw.style.candidate import scheme

import check_parhelion as C

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_ch8_plot", ROOT / "08-wedge-times-fold/code/_ch8_plot.py"
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
HEIGHTS = (0.0, 20.0, 40.0, C.critical_height(), 65.0)
VIEW_AZ, VIEW_EL = 310.0, 12.0
CAMERA = Camera(azimuth=VIEW_AZ, elevation=VIEW_EL,
                projection="perspective", distance=8.0)
LEVELS = (22, 25, 30, 40, 50)
S = scheme()
COLORS = {
    "ink": S.ink,
    "grid": S.guide,
    "latitude": S.family["plate"],
    "column": S.family["column"],
    "random": S.family["random"],
    "edge": S.sphere_edge,
    "surface": S.paper,
}


def distance_cmap():
    """地形色阶：单色相、明度单调，不叠加球面灯光；D 的数值与定义域不随外观变化。"""
    return LinearSegmentedColormap.from_list(f"distance_{S.terrain}", S.terrain_ramp)


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


def critical_contact():
    """正纬度闭包的唯一掠入/掠出点；不是 phi 的有限透射定义域点。"""
    normal = C.CRYSTAL.normal(C.CRYSTAL.face(C.PATH[0]))
    tangent = np.cross(normal, [0.0, 0.0, 1.0])
    tangent /= np.linalg.norm(tangent)
    h = np.radians(C.critical_height())
    return np.cos(h) * tangent + np.array([0.0, 0.0, np.sin(h)])


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


@lru_cache(maxsize=2)
def base_terrain(size=801):
    """四幅地形共用的只读底图；同一进程只计算一次，不允许叠层修改数值。"""
    arrays = terrain(size)
    for array in arrays:
        array.setflags(write=False)
    return arrays


def draw_base(ax):
    """3a–3d 的同一相机、光学域、数值色阶、经网与等值线。"""
    ink, guide = COLORS["ink"], COLORS["grid"]
    cmap = distance_cmap()
    norm = Normalize(21.0, 53.0)
    ax.set_aspect("equal")
    x, y, _, d = base_terrain()
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
        ax.clabel(contours, levels=[level], inline=True, fontsize=11,
                  fmt=lambda v: f"{v:g}°", manual=[position])
    outline = project(silhouette())
    ax.plot(outline[:, 0], outline[:, 1], color=COLORS["edge"], lw=0.8, zorder=4)
    return cmap, norm


# 数学下标与中文混排：整串放进 mathtext，中文段包在 \mathrm{} 里由 Hiragino 渲染。
MATH_RC = {"mathtext.fontset": "custom", "mathtext.rm": "Hiragino Sans GB",
           "mathtext.it": "Helvetica Neue:italic", "mathtext.bf": "Helvetica Neue:bold",
           "mathtext.sf": "Helvetica Neue"}


def apply_style():
    P.apply_style()
    plt.rcParams.update(MATH_RC)


def limb_point(latitude, side=1):
    """该纬线上透视可见、像平面最靠右（side=-1 为最靠左）的点：标签从这里水平写出，不用穿过地形的引线。"""
    u = C.unit_from(latitude, np.linspace(0, 360, 2881))
    xy = project(u)[:, :2]
    score = side * xy[:, 0]
    score[~sphere_visible(u)] = -np.inf
    return xy[np.argmax(score)]


def main(out=None):
    apply_style()
    ink = COLORS["ink"]
    accent = COLORS["latitude"]
    fig = plt.figure(figsize=(9.6, 6.6))
    ax = fig.add_axes([0.0, 0.12, 1.0, 0.86])
    cmap, norm = draw_base(ax)
    az = np.linspace(0, 360, 1441)
    for h in HEIGHTS:
        critical = h == C.critical_height()
        row = None if critical else latitude_minimum(h)
        line, = visible_curve(ax, C.unit_from(h, az), color=accent if row or critical else ink,
                              lw=1.8 if row or critical else 1.1,
                              ls=(0, (5, 2)) if critical else '-' if row else (0, (2, 3)), zorder=5)
        line.set_gid(f'latitude-{h:g}')
        if critical:
            xy = project(critical_contact())[:2]
            point = ax.scatter(*xy, s=65, facecolors=COLORS['surface'], edgecolors=ink,
                               linewidth=1.5, zorder=8)
            point.set_gid('critical-closure-contact')
            text = rf"$h = h_c \approx {h:.2f}°\mathrm{{\ \ 闭包相切，透射趋零}}$"
        elif row is None:
            text = f"h = {h:g}°  整圈在定义域外"
        else:
            u, value = row
            xy = project(u)[:2]
            ax.scatter(*xy, s=45, c=ink, edgecolor=COLORS["surface"],
                       linewidth=1.5, zorder=7)
            text = f"h = {h:.0f}°  最近 {value:.2f}°"
        if row is None and not critical:
            # 65° 纬圈很小、与临界纬线贴得近：标签放到左侧，免得两行挤在一起。
            x, y = limb_point(h, side=-1)
            ax.text(x - 0.05, y + 0.03, text, fontsize=13, color=ink, va="bottom", ha="right")
            continue
        x, y = limb_point(h)
        ax.text(x + 0.05, y, text, fontsize=13, color=accent, va="center")
    pole = project(np.array([0, 0, 1.0]))[:2]
    ax.text(pole[0] - 0.04, pole[1] + 0.055, "c 轴", color=ink, ha="right", fontsize=12)
    ax.text(-1.06, 0.45, "留白：\n无可行出射方向", ha="right", va="center", color=ink,
            fontsize=12, linespacing=1.5)
    ax.text(-1.0, -0.95, "u 球", color=ink, fontsize=14, ha="right")
    ax.set_xlim(-1.5, 2.3)
    ax.set_ylim(-1.08, 1.28)
    ax.axis("off")
    cax = fig.add_axes([0.2, 0.075, 0.36, 0.022])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation="horizontal", ticks=[22, 30, 40, 50])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=11, length=3, color=ink)
    cb.set_label("角距离 D（°）", fontsize=12, color=ink)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / "img/plate_terrain.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    main(args.output)
