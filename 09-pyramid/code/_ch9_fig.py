# ch9 十一张正文插图（task-draw-ch9-figs）共用的画图侧工具，与仿真侧 `_ch9_sim.py` 分工：
#   - `_ch9_sim.py` 管「怎么渲染 / 怎么从渲染取数」（过滤器、曝光、径向剖面、峰判据），本文件**不改它、只 import 它**；
#   - 本文件管「怎么把数画成图」：曲线图外观（沿用 ch8 `_ch8_plot.py` 的一份实现，不复制）、族配色、天顶 dual fisheye 渲染的读取 / 裁窗 / 显示、
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
# 天空图：Lumice rectangular 像素语义（上一轮入库渲染的取数；返工 R1 的新图走下文「太阳放天顶」一节，不再从 rectangular 重投影）
# ======================================================================================================
# **像素语义**：Lumice 渲染的一个像素存的是「辐亮度在该像素立体角上的积分」（Lumice 源码 `src/core/lens_proj_build.hpp:157`
# "A rendered pixel holds a radiance INTEGRATED over its own solid angle"）。rectangular 全天图的像素立体角 ∝ cos(lat)，所以
# 像素值 ∝ 辐亮度 × cos(lat)：同一张随机取向图上、与太阳同一夹角的一圈，靠近天顶 / 天底的像素暗到 1/10 以下（实测参考几何余量图
# θ ≈ 68°：lat 70–80° 与 40–70° 两段 L / cos(lat) 都是 0.0297，L 本身差 2.2 倍）。因此：
#   - 像素**能量** = 线性亮度 L 本身；像素**辐亮度** = L / cos(lat)；径向剖面的平均辐亮度 = ΣL / Σcos(lat)（`radiance_profile`）；
#   - 像素能量 / 辐亮度口径的唯一实现在 `halo_notes.sim.energy`（`pixel_energy` / `pixel_radiance`）；`_ch9_sim.energy_map` 早先取的是
#     L·cos(lat)（多乘了一次 cos），已在 task-pixel-energy-semantics 修正并重算 numbers.json（余量 12.1% → 13.2%，MC 为 13.04%；
#     局部峰 / 背景比 124.6° 1.55 → 1.55、`13-15-26-28` 3.72 → 3.69）。

import numpy as np  # noqa: E402

from halo_notes.sim.energy import pixel_energy, pixel_radiance  # noqa: E402
from halo_notes.sim.projection import rectangular_pixel_directions  # noqa: E402

def _srgb_encode(lin: np.ndarray) -> np.ndarray:
    lin = np.clip(lin, 0.0, 1.0)
    a = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.round(a * 255.0).astype(np.uint8)


def linear_radiance(lin: np.ndarray, render: dict) -> np.ndarray:
    """rectangular 图的线性像素值 (H, W, C)（每像素 = 立体角积分能量）→ 每像素辐亮度：先在每一行上做宽 ≈ 1/cos(lat) 像素的环绕方框平均
    （该行像素立体角越小、越多像素并成一个「赤道像素」大小的面元，8-bit 量化 / MC 噪声不会被下一步的 1/cos 放大），再除以 cos(lat)。
    赤道附近宽度 = 1，原样不动。"""
    lin = np.asarray(lin, float)
    H, W = lin.shape[:2]
    _, w = rectangular_pixel_directions(render)
    cos_lat = w[:, 0]
    out = np.empty_like(lin)
    for i in range(H):
        k = int(min(W, max(1, round(1.0 / cos_lat[i]))))
        row = lin[i]
        if k > 1:
            pad = np.concatenate([row[-(k // 2):], row, row[: k - k // 2 - 1]], axis=0) if k // 2 else np.concatenate([row, row[: k - 1]], axis=0)
            cs = np.cumsum(np.concatenate([np.zeros((1,) + row.shape[1:]), pad], axis=0), axis=0)
            row = (cs[k:] - cs[:-k]) / k
        out[i] = pixel_radiance(row, cos_lat[i])
    return out


def radiance_profile(image: np.ndarray, render: dict, center_dir: np.ndarray, *, bin_deg: float = 0.25,
                     max_deg: float = 180.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """以 ``center_dir`` 为极点的径向剖面（正确像素语义）：``(桶中心, 平均辐亮度 ΣL/Σcos(lat), 桶能量 ΣL)``，L = 三通道线性亮度之和。
    与 `_ch9_sim.angular_radial_profile` 同一分桶，只是不再多乘一次 cos(lat)。"""
    lin = pixel_energy(image)
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


# ======================================================================================================
# 返工 R1：太阳放天顶 + 一景两渲（dual_fisheye_equidistant 显示 / dual_fisheye_equal_area 取数），Lumice `--format npy`
# ======================================================================================================
# 随机取向下天空只是「到太阳的角距离」θ 的函数，太阳位置任选：放天顶（altitude 90°）后 dual fisheye 的两个圆盘天然就是
# 「太阳半球 | 反日半球」——左盘圆心 = 太阳（θ = 0，盘沿 θ = 90°），右盘圆心 = 反日点（θ = 180°，盘沿 θ = 90°）。
# 同一份 config 挂两个 render unit（id 1 等距、id 2 等面积），同一批光线同时落进两张图，两者只差 `lens.type`。
# Lumice dual fisheye 的像素映射（v4.6.1 `src/core/shared/projection_shared.h` `ProjectExitToPixel` / `DualFisheyeToPixelXY`，overlap 默认 0）：
#   天空方向 s（= −出射方向），上半球 s_z ≥ 0 进左盘（圆心 (W/2 − r, H/2)），下半球进右盘（圆心 (W/2 + r, H/2)），r = min(W/2, H)/2；
#   盘内归一半径 ρ：等距 ρ = θ_pole / 90°，等面积 ρ = √2 · sin(θ_pole / 2)（θ_pole = 到该盘极点的角距离）。
# 像素语义（同 rectangular）：一个像素存的是辐亮度在该像素立体角上的积分。等面积盘每像素立体角恒为 2/r²（半球 2π sr 摊在 πr² 像素上），
# 所以剖面 = 同一 θ 桶的像素求和 / 像素数，不需要任何 Jacobian；等距盘的像素立体角 = (π/2)² sinθ_p / (θ_p r²)，显示前除掉它（→ 辐亮度）。
# npy 是未曝光的线性 XYZ 累加器（raw），除以 sidecar 的 `emitted_energy` 后跨场景、跨光线数可比——这就是「同一绝对亮度标尺」。
# 落盘形态：每景一个确定性 zip `data/<scene>.zip`（只留本地、不入 git；重生成见 ../README.md）：`equidistant.npy`（XYZ）+ `equal_area.npy`（只留 Y），float16，各自乘一个
# 标度（最亮像素 → 60000，标度记进 `meta.json`）；float16 相对量化误差 < 0.05%（暗到次正规数时量化步长 = 最亮像素的 1e-12）。
# 全天总能量在量化**之前**用 float32 原图各算一次记进 meta，两种投影的一致性闸（< 2%）既在渲染时硬断言，也由单测从 zip 复算。

import io  # noqa: E402
import json  # noqa: E402
import zipfile  # noqa: E402

ZENITH_SUN_ALT = 90.0
DUAL_RES = (2560, 1280)            # 每盘半径 640 px：等距 0.14°/px；等面积盘心 0.11°/px、盘沿 0.18°/px
DUAL_LENSES = ("dual_fisheye_equidistant", "dual_fisheye_equal_area")
ZENITH_RAY_NUM = 1_000_000_000
ZENITH_BACKEND = "metal"
F16_PEAK = 60000.0
ENERGY_CONSISTENCY_TOL = 0.02


def load_npy_render(res) -> tuple[list[np.ndarray], list[dict]]:
    """``halo_notes.sim.run.render(fmt="npy")`` 的结果 → 每个 render unit 的 ``(H, W, 3)`` XYZ 与 sidecar（``img_XX.json``）；
    npy 读进内存后删掉，由调用方打包。"""
    arrays, sidecars = [], []
    for npy in res.images:
        arrays.append(np.load(npy))
        npy.unlink()
        sidecars.append(json.loads(npy.with_suffix(".json").read_text()))
    return arrays, sidecars


def dual_config(crystal: dict, filters: list[dict], *, ray_num: int = ZENITH_RAY_NUM, max_hits: int = 4) -> dict:
    """太阳天顶、D65、``filters`` 非空时 entry 挂顶层过滤器（id = `_ch9_sim.FILTER_ID`）；两个 render unit：id 1 等距、id 2 等面积。"""
    import _ch9_sim as S
    from halo_notes.sim import config as C

    entry = C.entry(1, filter=S.FILTER_ID) if filters else C.entry(1)
    scene = C.scene(C.sun(ZENITH_SUN_ALT), ray_num, [entry], max_hits=max_hits)
    renders = [C.render_unit(i + 1, C.lens(t), list(DUAL_RES), visible="full", background=[0, 0, 0], ev_mode="absolute",
                             intensity_factor=1.0) for i, t in enumerate(DUAL_LENSES)]
    return C.build_config([crystal], filters, scene, renders)


def _f16(a: np.ndarray) -> tuple[np.ndarray, float]:
    s = F16_PEAK / float(a.max()) if a.max() > 0 else 1.0
    return (a.astype(np.float64) * s).astype(np.float16), s


def pack_dual(zip_path: Path, arrays: list[np.ndarray], sidecars: list[dict], extra: dict) -> dict:
    """确定性 zip：``equidistant.npy``（XYZ）、``equal_area.npy``（Y）、``meta.json``。返回 meta。
    量化前先算两种投影的全天总能量（Y / emitted_energy，float64 累加），相对偏差超 ENERGY_CONSISTENCY_TOL 直接报错。"""
    ed, ea = arrays
    em = [float(s["emitted_energy"]) for s in sidecars]
    e_ed, e_ea = float(ed[..., 1].sum(dtype=np.float64) / em[0]), float(ea[..., 1].sum(dtype=np.float64) / em[1])
    if abs(e_ed / e_ea - 1) >= ENERGY_CONSISTENCY_TOL:
        raise RuntimeError(f"{zip_path.name}: 两种投影全天总能量不一致 {e_ed} vs {e_ea}")
    q_ed, s_ed = _f16(ed)
    q_ea, s_ea = _f16(ea[..., 1])
    meta = {"lenses": list(DUAL_LENSES), "resolution": list(DUAL_RES), "emitted_energy": em,
            "f16_scale": {"equidistant": s_ed, "equal_area": s_ea},
            "total_energy_float32": {"equidistant": e_ed, "equal_area": e_ea}, "sidecars": sidecars, **extra}
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, payload in (("equidistant.npy", q_ed), ("equal_area.npy", q_ea), ("meta.json", None)):
            if payload is None:
                data = (json.dumps(meta, indent=2, ensure_ascii=False) + "\n").encode()
            else:
                buf = io.BytesIO()
                np.save(buf, payload)
                data = buf.getvalue()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    return meta


class DualScene:
    """一景天顶渲染（从 zip 读回）：``ed`` = 等距 XYZ、``ea`` = 等面积 Y，都已换回「每单位发射能量」的像素能量（float32）。"""

    def __init__(self, name: str, root: Path | None = None):
        path = (root or CHAPTER) / "data" / f"{name}.zip"
        if path.stat().st_size < 1024 and path.read_bytes().startswith(b"version https://git-lfs"):
            raise RuntimeError(f"{path} 是 LFS 指针，先 `git lfs pull`")
        with zipfile.ZipFile(path) as zf:
            self.meta = json.loads(zf.read("meta.json"))
            ed = np.load(io.BytesIO(zf.read("equidistant.npy")))
            ea = np.load(io.BytesIO(zf.read("equal_area.npy")))
        em = self.meta["emitted_energy"]
        sc = self.meta["f16_scale"]
        self.name = name
        self.ed = ed.astype(np.float32) / np.float32(sc["equidistant"] * em[0])
        self.ea = ea.astype(np.float32) / np.float32(sc["equal_area"] * em[1])

    def total_energy(self) -> dict[str, float]:
        """两种投影各自的全天总能量（Y / emitted_energy），从量化后的数组复算。"""
        return {"equidistant": float(self.ed[..., 1].sum(dtype=np.float64)), "equal_area": float(self.ea.sum(dtype=np.float64))}

    def profile(self, bin_deg: float = 0.25, max_deg: float = 180.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """``(桶中心 θ, 平均辐亮度, 桶能量)``：等面积盘，θ = 到太阳的角距离；辐亮度 = ΣY / (有效像素数 × 2/r²)（每单位发射能量每 sr）。"""
        return equal_area_profile(self.ea, bin_deg=bin_deg, max_deg=max_deg)


def _disc_geometry(W: int, H: int) -> tuple[float, float, float, float]:
    r = min(W // 2, H) / 2.0
    return r, W / 2.0 - r, W / 2.0 + r, H / 2.0


def dual_theta(W: int, H: int, lens: str) -> np.ndarray:
    """dual fisheye 每个像素中心到**太阳（天顶）**的角距离（度，H × W）；盘外 NaN。盘沿外半个像素内的像素（中心略出盘、但光线会落进来）
    归到盘沿（θ = 90°）。"""
    r, cxl, cxr, cy = _disc_geometry(W, H)
    ys, xs = np.mgrid[0:H, 0:W] + 0.5
    out = np.full((H, W), np.nan)
    for upper, cx in ((True, cxl), (False, cxr)):
        rn = np.hypot(xs - cx, ys - cy) / r
        m = (rn <= 1 + 1 / r) & ((xs < W / 2) if upper else (xs >= W / 2))
        rn = np.minimum(rn, 1.0)
        tp = 90.0 * rn if lens == "dual_fisheye_equidistant" else np.degrees(2 * np.arcsin(rn / np.sqrt(2)))
        out[m] = (tp if upper else 180.0 - tp)[m]
    return out


def disc_coverage(W: int, H: int) -> np.ndarray:
    """每个像素落在所属圆盘内的面积比例（盘沿一圈 0–1，近似为 r + ½ − 像素中心到圆心距离，截到 [0, 1]；盘内 1、盘外 0）。
    盘沿像素只有一部分立体角属于半球，按整像素计数会让 θ = 90° 那一桶的平均辐亮度凭空下陷。"""
    r, cxl, cxr, cy = _disc_geometry(W, H)
    ys, xs = np.mgrid[0:H, 0:W] + 0.5
    cx = np.where(xs < W / 2, cxl, cxr)
    return np.clip(r + 0.5 - np.hypot(xs - cx, ys - cy), 0.0, 1.0)


def equal_area_profile(Y: np.ndarray, *, bin_deg: float = 0.25, max_deg: float = 180.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    H, W = Y.shape
    r = _disc_geometry(W, H)[0]
    th = dual_theta(W, H, "dual_fisheye_equal_area")
    m = ~np.isnan(th)
    edges = np.arange(0.0, max_deg + bin_deg / 2, bin_deg)
    e, _ = np.histogram(th[m], bins=edges, weights=Y[m].astype(np.float64))
    n, _ = np.histogram(th[m], bins=edges, weights=disc_coverage(W, H)[m])     # 有效像素数（盘沿按面积比例计）
    rad = np.divide(e, n * (2.0 / r ** 2), out=np.zeros_like(e), where=n > 0)
    return (edges[:-1] + edges[1:]) / 2, rad, e


XYZ_TO_SRGB = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])


def disc_radiance(scene: DualScene, hemisphere: str, max_deg: float = 90.0) -> tuple[np.ndarray, np.ndarray]:
    """等距盘裁窗：``hemisphere`` = ``"sun"``（左盘，圆心太阳）/ ``"anti"``（右盘，圆心反日点）；返回 ``(辐亮度 XYZ (n, n, 3), 到盘心角距离 (n, n))``，
    n = 2·⌈max_deg/90 · r⌉，窗外 NaN。辐亮度 = 像素能量 / 像素立体角（等距：(π/2)² sinθ_p / (θ_p r²)），与 :meth:`DualScene.profile` 同一单位。"""
    H, W = scene.ed.shape[:2]
    r, cxl, cxr, cy = _disc_geometry(W, H)
    cx = cxl if hemisphere == "sun" else cxr
    half = int(np.ceil(max_deg / 90.0 * r))
    x0, y0 = int(round(cx)) - half, int(round(cy)) - half
    crop = scene.ed[y0:y0 + 2 * half, x0:x0 + 2 * half].astype(np.float64)
    ys, xs = np.mgrid[y0:y0 + 2 * half, x0:x0 + 2 * half] + 0.5
    tp = np.radians(90.0 * np.hypot(xs - cx, ys - cy) / r)
    rel = np.where(tp > 1e-9, np.sin(tp) / np.maximum(tp, 1e-9), 1.0)
    omega = (np.pi / 2) ** 2 * rel / r ** 2
    rad = crop / omega[..., None]
    deg_ = np.degrees(tp)
    rad[deg_ > max_deg] = np.nan
    return rad, np.where(deg_ <= max_deg, deg_, np.nan)


def tone(rad_xyz: np.ndarray, white: float, *, gain: float = 1.0, background: str | None = None) -> np.ndarray:
    """辐亮度 XYZ → 显示 sRGB (n, n, 3) float 0–1：线性曝光，Y = ``white / gain`` 处满白（削顶保色相按最大通道等比压回）；
    窗外（NaN）填 ``background``（默认页面底色）。同一 ``white`` 的两张图就是同一绝对亮度标尺。"""
    xyz = np.nan_to_num(rad_xyz)
    # 2-D reshape 再乘：numpy + Accelerate 对 (N, N, 3) @ (3, 3) 的批量 matmul 会 SIGSEGV（backlog 已记，projection.py 同一个坑）
    lin = (xyz.reshape(-1, 3) @ XYZ_TO_SRGB.T).reshape(xyz.shape) * (gain / white)
    lin = np.clip(lin, 0.0, None)
    mx = lin.max(axis=-1, keepdims=True)
    lin = np.where(mx > 1.0, lin / np.maximum(mx, 1e-30), lin)
    out = _srgb_encode(lin).astype(float) / 255.0
    bg = np.array([int((background or PAL["background"])[k:k + 2], 16) for k in (1, 3, 5)]) / 255.0
    out[np.isnan(rad_xyz[..., 0])] = bg
    return out


def show_disc(ax, rgb: np.ndarray, max_deg: float, *, rings: tuple[float, ...] = (), ring_labels: bool = True,
              label_angle_deg: float = -40.0, center: str | None = None, ring_color: str = "white") -> None:
    """把 :func:`tone` 的圆盘画进 ``ax``（坐标 = 到盘心的角距离，度；等距投影下半径线性），叠同心刻度圈。"""
    ax.imshow(rgb, extent=(-max_deg, max_deg, -max_deg, max_deg), interpolation="antialiased")
    t = np.linspace(0, 2 * np.pi, 361)
    a = np.radians(label_angle_deg)
    for rr in rings:
        ax.plot(rr * np.cos(t), rr * np.sin(t), color=ring_color, lw=0.5, alpha=0.35, ls=(0, (3, 3)))
        if ring_labels:
            ax.text(rr * np.cos(a), rr * np.sin(a), deg(rr), color=ring_color, alpha=0.7, fontsize=8, ha="left", va="top",
                    family=list(CHART_FONTS))
    if center:
        ax.text(0, max_deg * 0.03, center, ha="center", va="bottom", fontsize=8.5, color=ring_color, alpha=0.8,
                family=list(CHART_FONTS))
    ax.set_xlim(-max_deg * 1.01, max_deg * 1.01)
    ax.set_ylim(-max_deg * 1.01, max_deg * 1.01)
    ax.set_aspect("equal")
    ax.set_axis_off()


# ======================================================================================================
# 晶体截面与面分组配色（图 1 / 图 7 共用；原在 fig_pyramid_faces.py，图 7 横向 import 它——code-review Minor 1 收进这里）
# ======================================================================================================

FACE_GROUPS = {                               # 组名 → (面号, 颜色)
    "底面": ((1, 2), PAL["ink_soft"]),
    "柱面": (tuple(range(3, 9)), PAL["face_4"]),
    "上锥面": (tuple(range(13, 19)), PAL["face_3"]),
    "下锥面": (tuple(range(23, 29)), PAL["face_6"]),
}
FACE_COLOR = {f: c for faces, c in FACE_GROUPS.values() for f in faces}


def section_polygon(p: Pyramid) -> np.ndarray:
    """y = 0 截面（xz 平面）：全部 20 个半平面 n·x ≤ d 限制在 y = 0 上，逐个裁一个大方框（凸多边形，逆时针）。"""
    poly = [np.array(v, float) for v in ((-9, -9), (9, -9), (9, 9), (-9, 9))]
    for f in p.faces:
        n = np.asarray(p.normal(f), float)
        d = float(n @ p.face_vertices(f)[0])
        n2 = np.array([n[0], n[2]])
        if np.linalg.norm(n2) < 1e-12:
            continue
        out: list[np.ndarray] = []
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            sa, sb = a @ n2 - d, b @ n2 - d
            if sa <= 1e-12:
                out.append(a)
            if (sa <= 1e-12) != (sb <= 1e-12):
                out.append(a + (b - a) * (sa / (sa - sb)))
        poly = out
    return np.array(poly)
