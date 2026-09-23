# ch9 十一张正文插图（task-draw-ch9-figs）共用的画图侧工具，与仿真侧 `_ch9_sim.py` 分工：
#   - `_ch9_sim.py` 管「怎么渲染 / 怎么从渲染取数」（过滤器、曝光、径向剖面、峰判据），本文件**不改它、只 import 它**；
#   - 本文件管「怎么把数画成图」：曲线图外观（沿用 ch8 `_ch8_plot.py` 的一份实现，不复制）、族配色、天空图重投影 / 裁窗、
#     多曲线按能量加总、片晶弧计数判据。函数随各 fig 脚本按最小必要增量加入，不预设接口。
# 仿真参数（太阳高度、光线数、h/a……）不进图面，留在各脚本头注释与 provenance（ch8 惯例）。
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

CODE_DIR = Path(__file__).resolve().parent
CHAPTER = CODE_DIR.parent
IMG = CHAPTER / "img"
DATA = CHAPTER / "data"
CH8_CODE = CHAPTER.parent / "08-wedge-times-fold" / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


def _load_ch8_plot():
    """按文件路径加载 ch8 的 `_ch8_plot.py`（曲线图外观的唯一实现，ch9 直接复用）。不把 ch8 code/ 放进 sys.path：两章都有
    `enumerate_signatures.py` / `analyze_energy.py`，同名模块会互相遮蔽。"""
    spec = importlib.util.spec_from_file_location("_ch8_plot", CH8_CODE / "_ch8_plot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P8 = _load_ch8_plot()

PAL = P8.PAL
CHART_FONTS = P8.CHART_FONTS
apply_style = P8.apply_style
deg = P8.deg


def out_png(name: str) -> Path:
    """``img/<name>.png``（一图一脚本：脚本 ``fig_<name>.py`` → 本路径）。"""
    IMG.mkdir(parents=True, exist_ok=True)
    return IMG / f"{name}.png"


# PNG 元数据里 matplotlib 默认写入版本号 / 时间戳之类的 Software 字段：统一清空，几何 / 图表类产物才能逐字节复现
PNG_META = {"Software": None}


# ======================================================================================================
# 天空图：Lumice rectangular 像素语义 + 重投影成以某方向为中心的等距鱼眼（不重渲）
# ======================================================================================================
# **像素语义**：Lumice 渲染的一个像素存的是「辐亮度在该像素立体角上的积分」（Lumice 源码 `src/core/lens_proj_build.hpp:157`
# "A rendered pixel holds a radiance INTEGRATED over its own solid angle"）。rectangular 全天图的像素立体角 ∝ cos(lat)，所以
# 像素值 ∝ 辐亮度 × cos(lat)：同一张随机取向图上、与太阳同一夹角的一圈，靠近天顶 / 天底的像素暗到 1/10 以下（实测参考几何余量图
# θ ≈ 68°：lat 70–80° 与 40–70° 两段 L / cos(lat) 都是 0.0297，L 本身差 2.2 倍）。因此：
#   - 像素**能量** = 线性亮度 L 本身；像素**辐亮度** = L / cos(lat)；径向剖面的平均辐亮度 = ΣL / Σcos(lat)（`radiance_profile`）；
#   - `_ch9_sim.energy_map` 取的是 L·cos(lat)（多乘了一次 cos），它的剖面 / 能量份额带一个随 θ 缓变的偏置：局部峰 / 背景比几乎不变
#     （余量 124.6° 1.55 → 1.55、`13-15-26-28` 3.72 → 3.69），全天能量份额会变（余量 12.1% → 13.2%，MC 为 13.04%）。
#     `_ch9_sim` 与已入库 numbers.json 本任务不改（issue 硬边界），偏差回抛作者，见 progress。本文件的新图一律按正确语义取数与显示。

import numpy as np  # noqa: E402

from halo_notes.sim.projection import project_rectangular, rectangular_pixel_directions  # noqa: E402

SUPERSAMPLE = 3          # 每个输出像素 3×3 个子样本，在线性亮度里平均


def _srgb_decode(img: np.ndarray) -> np.ndarray:
    a = np.asarray(img, float) / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def _srgb_encode(lin: np.ndarray) -> np.ndarray:
    lin = np.clip(lin, 0.0, 1.0)
    a = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.round(a * 255.0).astype(np.uint8)


def rect_radiance(image: np.ndarray, render: dict) -> np.ndarray:
    """rectangular 图（8-bit sRGB）→ 每像素线性辐亮度 (H, W, 3)：先在每一行上做宽 ≈ 1/cos(lat) 像素的环绕方框平均（该行像素立体角
    越小、越多像素并成一个「赤道像素」大小的面元，8-bit 量化噪声不会被下一步的 1/cos 放大），再除以 cos(lat)。赤道附近宽度 = 1，原样不动。"""
    lin = _srgb_decode(image)
    H, W = lin.shape[:2]
    _, w = rectangular_pixel_directions(render)
    cos_lat = w[:, 0]
    out = np.empty_like(lin)
    for i in range(H):
        k = int(min(W, max(1, round(1.0 / cos_lat[i]))))
        row = lin[i]
        if k > 1:
            pad = np.concatenate([row[-(k // 2):], row, row[: k - k // 2 - 1]]) if k // 2 else np.concatenate([row, row[: k - 1]])
            cs = np.cumsum(np.vstack([np.zeros((1, 3)), pad]), axis=0)
            row = (cs[k:] - cs[:-k]) / k
        out[i] = row / cos_lat[i]
    return out


def radiance_profile(image: np.ndarray, render: dict, center_dir: np.ndarray, *, bin_deg: float = 0.25,
                     max_deg: float = 180.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """以 ``center_dir`` 为极点的径向剖面（正确像素语义）：``(桶中心, 平均辐亮度 ΣL/Σcos(lat), 桶能量 ΣL)``，L = 三通道线性亮度之和。
    与 `_ch9_sim.angular_radial_profile` 同一分桶，只是不再多乘一次 cos(lat)。"""
    lin = _srgb_decode(image).sum(axis=-1)
    dirs, w = rectangular_pixel_directions(render)
    c = np.asarray(center_dir, float)
    c = c / np.linalg.norm(c)
    theta = np.degrees(np.arccos(np.clip(dirs @ c, -1.0, 1.0)))
    edges = np.arange(0.0, max_deg + bin_deg, bin_deg)
    e_hist, _ = np.histogram(theta, bins=edges, weights=lin)
    w_hist, _ = np.histogram(theta, bins=edges, weights=w)
    rad = np.divide(e_hist, w_hist, out=np.zeros_like(e_hist), where=w_hist > 0)
    return (edges[:-1] + edges[1:]) / 2, rad, e_hist


def product_profile(name: str, variant: str, *, bin_deg: float = 0.25, center_dir: np.ndarray | None = None
                    ) -> tuple[np.ndarray, np.ndarray]:
    """一份已入库渲染（``data/<name>/<variant>/``）的径向剖面，按 intensity 归一——absolute 曝光下不同产出之间可直接比较 / 相加
    （`_ch9_sim` 文件头：像素值与光线数无关、与 intensity 线性）。中心默认太阳。返回 ``(桶中心, 平均辐亮度 / intensity)``。"""
    import _ch9_sim as S
    img, cfg = S.load_product(name, variant)
    render = cfg["render"][0]
    c, rad, _ = radiance_profile(img, render, S.sun_direction() if center_dir is None else center_dir, bin_deg=bin_deg)
    return c, rad / float(render["intensity_factor"])


def center_frame(center_dir: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(c, up, right)``：c = 中心方向；up = 天顶在垂直于 c 的平面上的投影（画面「上」）；right = c × up（面向 c、天顶朝上时的右手边）。"""
    c = np.asarray(center_dir, float)
    c = c / np.linalg.norm(c)
    z = np.array([0.0, 0.0, 1.0])
    up = z - (z @ c) * c
    if np.linalg.norm(up) < 1e-9:
        up = np.array([1.0, 0.0, 0.0]) - c[0] * c
    up /= np.linalg.norm(up)
    return c, up, np.cross(c, up)


def fisheye_directions(center_dir: np.ndarray, size_px: int, max_theta_deg: float, *, sub: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """等距鱼眼每个（子）像素的天空方向 (N, N, 3) 与「在圆内」掩码 (N, N)，N = size_px·sub。
    半径 r（像素）↔ 与中心方向的夹角 θ = r / (size_px/2) · max_theta（等距：半径直接读角度）；方位角以画面「上」= 天顶一侧起算。"""
    c, up, right = center_frame(center_dir)
    n = size_px * sub
    t = (np.arange(n) + 0.5) / sub - size_px / 2.0             # 像素中心相对圆心（输出像素单位）
    X, Y = np.meshgrid(t, -t)                                   # Y 朝上
    r = np.hypot(X, Y)
    theta = np.radians(r / (size_px / 2.0) * max_theta_deg)
    inside = theta <= np.radians(max_theta_deg)
    phi = np.arctan2(X, Y)                                      # 0 = 上、顺时针到右
    st = np.sin(theta)
    d = (np.cos(theta)[..., None] * c + (st * np.cos(phi))[..., None] * up + (st * np.sin(phi))[..., None] * right)
    return d, inside


def rect_to_fisheye(image: np.ndarray, render: dict, center_dir: np.ndarray, size_px: int, max_theta_deg: float, *,
                    background: tuple[int, int, int] = (0, 0, 0), sub: int = SUPERSAMPLE, gain: float = 1.0) -> np.ndarray:
    """rectangular 全天图（8-bit sRGB）→ 以 ``center_dir`` 为中心、半径 = ``max_theta_deg`` 的等距鱼眼 (size, size, 3) uint8。
    先按像素语义换成辐亮度（:func:`rect_radiance`，赤道处数值不变、所以曝光与原图一致），子样本在其上双线性插值，
    再 sub×sub 平均、编码回 sRGB；圆外填 ``background``。``gain``：显示增益（线性亮度乘数，只为看清暗成分，不进任何取数）。"""
    lin = rect_radiance(image, render) * gain
    H, W = lin.shape[:2]
    d, inside = fisheye_directions(center_dir, size_px, max_theta_deg, sub=sub)
    uv = project_rectangular(d.reshape(-1, 3), render)
    u = uv[:, 0] - 0.5                                          # 像素中心在 i + ½
    v = np.clip(uv[:, 1] - 0.5, 0.0, H - 1.0)
    j0 = np.floor(u).astype(int)
    i0 = np.clip(np.floor(v).astype(int), 0, H - 2)
    fu, fv = (u - j0)[:, None], (v - i0)[:, None]
    j0m, j1m = j0 % W, (j0 + 1) % W                            # 经度方向环绕
    val = ((1 - fu) * (1 - fv) * lin[i0, j0m] + fu * (1 - fv) * lin[i0, j1m]
           + (1 - fu) * fv * lin[i0 + 1, j0m] + fu * fv * lin[i0 + 1, j1m])
    n = size_px * sub
    val = val.reshape(n, n, 3) * inside[..., None]
    val = val.reshape(size_px, sub, size_px, sub, 3).mean(axis=(1, 3))
    cover = inside.reshape(size_px, sub, size_px, sub).mean(axis=(1, 3))
    bg = _srgb_decode(np.array(background, float))
    out = val + (1 - cover)[..., None] * bg                    # 圆周上的像素按覆盖比例混合背景
    return _srgb_encode(out)


# ======================================================================================================
# 剖面曲线（图 4 / 5 / 8 / 10 同一套视觉语言）
# ======================================================================================================

THETA_LABEL = "与太阳的夹角"
RADIANCE_LABEL = "平均亮度（任意单位）"
FAMILY_COLOR = {                     # 九族里正文点名的几族的固定配色（图 5 / 8 同色）
    28.0: PAL["ink_soft"], 52.4: PAL["face_3"], 56.0: PAL["face_5"], 60.0: PAL["face_4"],
    62.0: PAL["face_6"], 63.8: PAL["face_8"], 80.2: PAL["slate"], 90.0: PAL["cloud"],
}
SUM_COLOR = PAL["ink"]


def theta_axis(ax, lo: float, hi: float, step: float, *, label: bool = True) -> None:
    """横轴 = 与太阳的夹角（°），刻度每 ``step``；去上 / 右框、淡横向网格（外观由 apply_style 统一）。"""
    ax.set_xlim(lo, hi)
    ticks = np.arange(np.ceil(lo / step) * step, hi + 1e-9, step)
    ax.set_xticks(ticks)
    ax.set_xticklabels([deg(t) for t in ticks])
    ax.grid(axis="y", color=PAL["ink_faint"], lw=0.6, alpha=0.7)
    if label:
        ax.set_xlabel(THETA_LABEL)


def mark_radii(ax, radii, *, labels: dict | None = None, color: str = PAL["ink_faint"], y: float = 1.0) -> None:
    """经典晕半径的竖直参考线（淡灰细线；``labels`` 给出则在轴顶写小字）。"""
    for r in radii:
        ax.axvline(r, color=color, lw=0.8, zorder=0)
        if labels and r in labels:
            ax.text(r, y, labels[r], transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=8.5,
                    color=PAL["slate"])
