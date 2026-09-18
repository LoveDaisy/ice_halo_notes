# 图 B1（fig_b1_same_class.py）与 B2（fig_b2_unnamed_cell.py）共用的 Lumice 过滤器构造与帧中心选取（一份实现）。
# 本篇正文里的「格子」是 **Φ 类**（signature 类，`halo_notes.math.signature.phi_class`），不是 ch7 的矩阵共轭类：
# 同一 Φ 类的全部面序列从 `lumice_integral.geometry.enumerate` 枚举（参数与 `enumerate_signatures.py` 逐字相同：
# `max_len=8`、`entry_faces=(1, 3)`、PBD 轨道去重、`LatLonGrid(180, 360)`），逐条经 `phi_class` 落类，取 `row.id == class_id`
# 的全部代表装进 `complex` 复合过滤器（OR）——ch7 图 6 的教训：单条代表光路只占类总能量 0.4%，不能只放最短代表。
# 输出形态与 `07-reflection-group/code/_ch7_sim.class_filters` 逐字一致（复合过滤器 id=FILTER_ID、PBD 写在复合过滤器上、
# 子过滤器各带 PBD），只是数据来源从 `reflection_group.raypaths_of_class` 换成枚举器 + `phi_class`。
# B1 是三条**单光路**对照（A60-10 类内 `3-1-5-2-6-7` / `3-1-5-6-2-7` / `3-1-2-5-6-7`），走 `single_raypath_filter`，不走 OR；
# 它的子图是 rectangular 全天图裁到反日点一侧的窗口（`rectangular_window`），不走 globe 选帧中心。
# 晶体口径：本仓 `HexPrism` 的 h/a（a = 六边形边长），Lumice `height` 经 `config.hex_prism_height_ratio` 换算（÷2），
# 与 `analyze_energy.py` / `data/energy_table.md` 同一口径；ch7 图 6 直接写 Lumice height=2（本仓口径 h/a=4），本篇不沿用那个数。
# 帧中心机械选取（`choose_center` / `cap_energy_fractions` / `linear_luminance` / `sky_grid`）照抄 ch7 `fig_halos_columns.py`——
# 跨章复用的代码按 AGENTS.md 应上提到 `halo_notes/`，本任务 plan 划定 `halo_notes/` 只读，先章内复制、上提另起任务（progress 有记）。
# 太阳高度：B1（图 5）沿用模块默认 `SUN_ALTITUDE`=10°；B2 系列（`fig_b2_unnamed_cell.py`、`fig_cross_section_sensitivity.py`）改太阳 0°
# （task-revise-ch8：Liljequist 窄峰与 142° 鼓包两层同现需太阳贴地平线），一律经 `scene(..., sun_alt=)` / `candidates_for(sun_alt)` 显式传入，
# 不改全局常量。幻日环条带方位剖面 `azimuth_profile` 是唯一实现（抽自 scratchpad probe_liljequist_azimuth.py），B1 / B2 / 截面敏感性图都调它。
from __future__ import annotations

import numpy as np

from lumice_integral.geometry import HexPrism, fold_matrix
from lumice_integral.geometry.enumerate import enumerate_raypaths_with_stats
from lumice_integral.geometry.feasibility import LatLonGrid
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import phi_class, phi_class_table
from halo_notes.sim import config as C
from halo_notes.sim.projection import GLOBE_CAP_DEG, project_rectangular, rectangular_pixel_directions

FILTER_ID = 1          # 顶层过滤器的 id（复合或单光路）；scattering entry 引用它
MAX_LEN = 8            # 与 enumerate_signatures.py 一致
SYMMETRY = "PBD"
ENTRY_FACES = (1, 3)
GRID = LatLonGrid(180, 360)

# 三张 B 类子图共用的场景参数（沿 ch7 图 6：Σ=10°、D65、globe fov 30、zenith σ=0.5°、经纬网格 30°）
SUN_ALTITUDE = 10.0
ZENITH_STD = 0.5
SKY_PX = 1400
LENS_TYPE, FOV_DEG = "globe", 30
REF_RESOLUTION = (1440, 720)
GRID_STEP, GRID_OPACITY, GRID_COLOR, GRID_LABEL = 30, 0.35, [0.55, 0.55, 0.55], False
MAX_HITS = 9           # 类里有 8 面代表；analyze 实测 max_hits = 链面数（含入射面），渲染路径未单独实测，取 MAX_LEN + 1 兜底

_MEMBERS: dict[tuple[float, int], dict[str, tuple[tuple[int, ...], ...]]] = {}


def crystal(ratio: float, orientation: str) -> dict:
    """单一 population：``orientation`` = ``"plate"``（c 轴竖直）或 ``"column"``（c 轴水平、roll 均匀），zenith σ=0.5°。"""
    axis = {"plate": C.plate_axis, "column": C.column_axis}[orientation](ZENITH_STD)
    return C.prism_crystal(1, C.hex_prism_height_ratio(ratio), axis=axis)


def class_members(ratio: float, *, max_len: int = MAX_LEN) -> dict[str, tuple[tuple[int, ...], ...]]:
    """h/a=``ratio`` 下 34 类 id → 该类全部可行光路（PBD 代表，按 (长度, 字典序) 排）；枚举约 50 s，进程内缓存。"""
    key = (float(ratio), max_len)
    if key not in _MEMBERS:
        crys = HexPrism.from_ratio(ratio)
        by_row = {r.phi_class: r for r in phi_class_table(crys)}
        recs, _ = enumerate_raypaths_with_stats(crys, max_len, GRID, entry_faces=ENTRY_FACES, symmetry_orbit=rg.pbd_orbit)
        members: dict[str, list[tuple[int, ...]]] = {}
        for r in recs:
            if len(r.faces) == 1:
                continue                          # 外反射不在 34 类框架内
            row = by_row[phi_class(crys, fold_matrix(crys, r.faces), r.faces[0], r.faces[-1])]
            members.setdefault(row.id, []).append(tuple(r.faces))
        _MEMBERS[key] = {k: tuple(sorted(v, key=lambda s: (len(s), s))) for k, v in members.items()}
    return _MEMBERS[key]


def class_id_of(ratio: float, faces: tuple[int, ...]) -> str:
    """一条面序列所属的 Φ 类 id（不看可行性，只看 (M, a, b)）。"""
    crys = HexPrism.from_ratio(ratio)
    by_row = {r.phi_class: r for r in phi_class_table(crys)}
    return by_row[phi_class(crys, fold_matrix(crys, faces), faces[0], faces[-1])].id


def class_representatives(class_id: str, ratio: float, *, max_len: int = MAX_LEN) -> tuple[tuple[int, ...], ...]:
    """Φ 类 ``class_id`` 在 h/a=``ratio`` 下的全部可行光路（PBD 代表）；该档不可达抛 ``KeyError``。"""
    return class_members(ratio, max_len=max_len)[class_id]


def phi_class_filters(class_id: str, ratio: float, *, max_len: int = MAX_LEN, symmetry: str = SYMMETRY) -> list[dict]:
    """过滤器段：``[complex(id=FILTER_ID, OR 全部代表), raypath(id=2, 代表 1), raypath(id=3, 代表 2), …]``（形态同 ch7）。"""
    reps = class_representatives(class_id, ratio, max_len=max_len)
    subs = [C.raypath_filter(FILTER_ID + 1 + i, list(seq), symmetry) for i, seq in enumerate(reps)]
    return [C.complex_filter(FILTER_ID, [f["id"] for f in subs], symmetry)] + subs


def single_raypath_filter(faces: tuple[int, ...], *, symmetry: str = SYMMETRY) -> list[dict]:
    """过滤器段：一条光路（B1 用），``[raypath(id=FILTER_ID, faces, PBD)]``。"""
    return [C.raypath_filter(FILTER_ID, list(faces), symmetry)]


def class_filter_paths(filters: list[dict]) -> set[tuple[int, ...]]:
    """反向：过滤器段里顶层过滤器覆盖的全部子光路（复合 → 引用的子过滤器；单光路 → 它自己），单测用。"""
    by_id = {f["id"]: f for f in filters}
    top = by_id[FILTER_ID]
    if top["type"] == "complex":
        return {tuple(by_id[i]["raypath"]) for i in C.composition_ids(top)}
    return {tuple(top["raypath"])}


# ---- 场景 / 渲染段（B1、B2 共用） ----


def sky(el_deg: float, az_deg: float) -> np.ndarray:
    e, a = np.radians(el_deg), np.radians(az_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


# 候选帧中心（天空方向）；Lumice 方位角 0° = +x = 太阳方向。场景关于太阳—反日点竖直面镜像对称，侧向只列 +90°（同 ch7）
CENTER_TEXT = {"sun": "帧中心：太阳", "anthelic": "帧中心：反日点", "side": "帧中心：侧向（方位角 90°）"}


def candidates_for(sun_alt: float) -> dict[str, np.ndarray]:
    """太阳高度 ``sun_alt`` 下的三个候选帧中心（都在幻日环高度上）。"""
    return {"sun": sky(sun_alt, 0), "anthelic": sky(sun_alt, 180), "side": sky(sun_alt, 90)}


CANDIDATES = candidates_for(SUN_ALTITUDE)      # B1 与既有单测用的默认（10°）


def sky_grid(*, step: int = GRID_STEP, opacity: float = GRID_OPACITY, label: bool = GRID_LABEL) -> dict:
    """经纬网格：仰角 / 方位角每 ``step`` 度一条（低透明度），地平线单独一条更亮。"""
    elev = [C.grid_line(v, opacity=opacity, color=GRID_COLOR) for v in range(-90 + step, 90, step) if v != 0]
    elev.append(C.grid_line(0, opacity=min(1.0, opacity * 2), color=GRID_COLOR))
    lon = [C.grid_line(v, opacity=opacity, color=GRID_COLOR) for v in range(0, 360, step)]
    return C.grid(elevation=elev, longitude=lon, extra={"label": label})


def scene(ray_num: int, sun_alt: float = SUN_ALTITUDE, *, filtered: bool = True) -> dict:
    """场景段：太阳 ``sun_alt``、D65；``filtered=False`` 时 entry 不挂过滤器（渲染全部光路，B2 方位剖面的「全部」曲线用）。"""
    entry = C.entry(1, filter=FILTER_ID) if filtered else C.entry(1)
    return C.scene(C.sun(sun_alt), ray_num, [entry], max_hits=MAX_HITS)


def reference_render(intensity_factor: float = 3.0) -> dict:
    """全天 ``rectangular`` 参考图的 render 段（无网格、absolute 曝光），只用于选帧中心。"""
    return C.render_unit(1, C.lens("rectangular"), list(REF_RESOLUTION), visible="full", background=[0, 0, 0],
                         ev_mode="absolute", intensity_factor=intensity_factor)


def globe_render(view: dict, *, ev_mode: str = "relative", intensity_factor: float = 1.0, grid: dict | None = None) -> dict:
    return C.render_unit(1, C.lens(LENS_TYPE, fov=FOV_DEG), [SKY_PX, SKY_PX], view=view, visible="full",
                         background=[0, 0, 0], ev_mode=ev_mode, intensity_factor=intensity_factor,
                         grid=sky_grid() if grid is None else grid)


def linear_luminance(image: np.ndarray) -> np.ndarray:
    """8-bit sRGB → 线性亮度（三通道之和）。"""
    a = np.asarray(image, float) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return lin.sum(axis=-1) if lin.ndim == 3 else lin


def cap_energy_fractions(image: np.ndarray, render: dict, candidates: dict[str, np.ndarray],
                         cap_deg: float = GLOBE_CAP_DEG) -> dict[str, float]:
    """参考图（rectangular）上，各候选中心周围 ``cap_deg`` 球冠内的能量占全天的比例（像素按 cos(lat) 立体角加权）。"""
    dirs, weight = rectangular_pixel_directions(render)
    energy = linear_luminance(image) * weight
    total = energy.sum()
    if total <= 0:
        raise ValueError("参考图全黑：过滤器没有命中任何光线，帧中心无法选取")
    cos_cap = np.cos(np.radians(cap_deg))
    return {name: float(energy[(dirs @ c) > cos_cap].sum() / total) for name, c in candidates.items()}


def choose_center(image: np.ndarray, render: dict, candidates: dict[str, np.ndarray] = CANDIDATES) -> tuple[str, dict[str, float]]:
    """帧中心 = 球冠内能量占比最大的候选（并列取 CANDIDATES 顺序靠前者）。"""
    fr = cap_energy_fractions(image, render, candidates)
    best = max(candidates, key=lambda n: (round(fr[n], 9), -list(candidates).index(n)))
    return best, fr


def sky_energy(image: np.ndarray, render: dict) -> float:
    """参考图（rectangular、absolute 曝光）的全天线性能量（立体角加权），供两条光路的亮度比对。"""
    _, weight = rectangular_pixel_directions(render)
    return float((linear_luminance(image) * weight).sum())


def azimuth_profile(image: np.ndarray, render: dict, sun_alt: float, *, half_deg: float = 1.5,
                    edges: np.ndarray | None = None, bin_deg: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """幻日环条带方位剖面：``rectangular`` 参考图上仰角 = ``sun_alt`` ± ``half_deg`` 的条带，线性能量（立体角加权）沿 |方位角|
    （太阳 = 0°；场景左右镜像对称，两侧合并）按 ``edges``（度，默认 0…180 每 ``bin_deg``）分桶。返回 ``(桶中心, 各桶能量)``。
    抽自 scratchpad/task-write-ch8/probe_liljequist_azimuth.py::profile，B1 `strip_profile`、B2 三曲线、截面敏感性图共用这一份实现。"""
    if edges is None:
        edges = np.arange(0.0, 180.0 + bin_deg, bin_deg)
    edges = np.asarray(edges, float)
    dirs, weight = rectangular_pixel_directions(render)
    el = np.degrees(np.arcsin(np.clip(dirs[..., 2], -1.0, 1.0)))
    az = np.abs(np.degrees(np.arctan2(dirs[..., 1], dirs[..., 0])))
    strip = np.abs(el - sun_alt) <= half_deg
    hist, _ = np.histogram(az[strip], bins=edges, weights=(linear_luminance(image) * weight)[strip])
    return (edges[:-1] + edges[1:]) / 2, hist


def rectangular_window(render: dict, az_range: tuple[float, float], el_range: tuple[float, float]) -> tuple[slice, slice]:
    """``rectangular`` 图上方位 ``az_range``、仰角 ``el_range``（度，闭区间；方位 0° = 太阳，按 Lumice 约定取值）覆盖的像素窗口，
    返回 ``(行切片, 列切片)``——B1 三张子图裁到反日点一侧同一窗口用。取像素中心落在范围内的行列，边界经
    :func:`project_rectangular` 正投影四个角算出（不铺整幅方向网格，5760×2880 的子图也只算 4 个点）；方位区间跨过
    ±180° 接缝时直接报错而不是静默给一个错窗口。"""
    w, h = int(render["resolution"][0]), int(render["resolution"][1])
    uv = project_rectangular([sky(el, az) for el in el_range for az in az_range], render)
    u_lo, u_hi = float(uv[0, 0]), float(uv[1, 0])            # 同一仰角、方位 az_lo → az_hi
    v_top, v_bot = float(uv[2, 1]), float(uv[0, 1])          # 仰角 el_hi 在上、el_lo 在下（v 向下）
    if u_hi <= u_lo:
        u_hi += w                                            # 方位上限恰落在接缝（如 180°）时 u 折回 0，补一圈
    if u_hi > w + 1e-6:
        raise ValueError("方位区间跨过了 ±180° 接缝，窗口不连续")
    cols = slice(int(np.ceil(u_lo - 0.5)), int(np.floor(u_hi - 0.5)) + 1)
    rows = slice(int(np.ceil(v_top - 0.5)), int(np.floor(v_bot - 0.5)) + 1)
    if rows.stop <= rows.start or cols.stop <= cols.start:
        raise ValueError("范围在这张图上没有像素")
    return rows, cols


FEATURE_WINDOW = (120.0, 180.0)    # 方位剖面取数窗口：反日点一侧（B2 三曲线与截面敏感性图共用）
OUTER_FRAC = 0.1                   # 「外缘」= 剖面从峰值降到 10% 处


def _crossing(x: np.ndarray, y: np.ndarray, level: float, i: int, step: int) -> float:
    """从桶 ``i``（y[i] ≥ level）沿 ``step`` 方向走到首个 y < level 的桶，两桶之间线性插值出 y = level 的方位。"""
    j = i
    while 0 <= j + step < len(y) and y[j + step] >= level:
        j += step
    k = j + step
    if not 0 <= k < len(y):
        return float(x[j])
    t = (y[j] - level) / (y[j] - y[k])
    return float(x[j] + t * (x[k] - x[j]))


def profile_features(centers: np.ndarray, hist: np.ndarray, window: tuple[float, float] | None = None,
                     outer_frac: float | None = None) -> dict[str, float]:
    """方位剖面在 ``window`` 内的机械特征：``peak_az``（argmax 桶中心）、``edge_az``（峰值内侧的半高交点——「锐边」位置）、
    ``rise_deg``（内侧从 10% 爬到 90% 峰值经过的方位跨度——锐边有多「锐」）、``outer_az``（峰值外侧降到 ``outer_frac`` 峰值的交点）、
    ``fwhm_deg``（半高全宽）、``energy``（窗口内条带能量）。"""
    window = FEATURE_WINDOW if window is None else window
    outer_frac = OUTER_FRAC if outer_frac is None else outer_frac
    m = (centers >= window[0]) & (centers <= window[1])
    x, y = centers[m], hist[m]
    if y.max() <= 0:
        raise ValueError("剖面在窗口内全零")
    i = int(np.argmax(y))
    p = float(y[i])
    return {
        "peak_az": float(x[i]),
        "edge_az": _crossing(x, y, 0.5 * p, i, -1),
        "rise_deg": _crossing(x, y, 0.9 * p, i, -1) - _crossing(x, y, 0.1 * p, i, -1),
        "outer_az": _crossing(x, y, outer_frac * p, i, +1),
        "fwhm_deg": _crossing(x, y, 0.5 * p, i, +1) - _crossing(x, y, 0.5 * p, i, -1),
        "energy": float(y.sum()),
    }
