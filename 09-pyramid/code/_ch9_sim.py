# 四个 fig_odd_radius_*.py（全景 / 逐族 / 余量 / top-3，task-odd-radius-instances）共用的过滤器构造、场景段与机械判据（一份实现）。
# 数据来源全部复用已交付的产物、不重新枚举 / 不重跑 analyze：
#   - 族成员：`../data/raypaths_h1_t0.5.csv`（`enumerate_signatures.py` 产出，L_STAR=6、1° 网格、PBD 代表）`family` 列按族分组，
#     每族**全部**代表装进 `complex` 复合过滤器（OR，`symmetry="PBD"` 由 Lumice 展开对称像）——ch7 图 6 / ch8 B 类图的教训：单条代表只占
#     该类能量的零头，必须放全类；形态与 `08-wedge-times-fold/code/_ch8_sim.phi_class_filters` 逐字一致（复合过滤器 id=FILTER_ID、PBD 写在复合
#     过滤器上、子过滤器各带 PBD），只是成员来源从「枚举器实时算」换成「读现成 CSV」；
#   - 族外 top-3：`../data/analysis/rows_h1_t0.5.csv`（`analyze_energy.py` 产出，MC 逐行表）里 `family` 空且 `status == ok` 的行按 `pbd_rep`
#     分组求和 `energy_pct` 取前 3——分组口径与「族能量份额」的加总口径同源（同一份数据不用两套统计口径）；
#   - 楔角 → 晕半径（最小偏向角）直接调 `enumerate_signatures.min_deviation_deg`，不另抄公式。
# 渲染口径：默认档 (h/a, tip_ratio) = (1, 0.5)、随机取向（`random_axis()`）、太阳 20°（与 `analysis_h1_t0.5.lumice.json` 同）、D65；
# **`max_hits = 4`，与 `energy_table.md` 的 MC 口径（`analyze_energy.MC_MAX_LEN = 4`）对齐**——机械核对「族图像素能量 ÷ 全景像素能量 ≈ 表里份额」
# 的分母必须是同一个宇宙（≤ 4 面链）。过滤器只装长度 ≤ MAX_HITS 的成员（`renderable_members`）：max_hits=4 下长度 5–6 的链根本产生不了，
# 装不装语义相同；而 Lumice v4.5.1 一份 config 最多 256 个过滤器（MAX_FILTERS），全部 1520 条 / 28° 族 269 条都放不下，≤4 面的 207 条 / 36 条才放得下。
# 「能量」= 像素线性亮度（sRGB 8-bit 解码后三通道之和）× 像素立体角（cos lat），`rectangular` 全天图、absolute 曝光、同一光线数，按 intensity
# 归一后可比：absolute 曝光下像素值与光线数无关（2×10⁷ / 4×10⁷ 实测比 1.0015）、与 intensity 线性（E/i 随 i 收敛）。8-bit 量化对暗像素是净损失
# （余量图 i=0.2 时丢 17%，i=4 只剩 ~1%），所以每份产出**各自曝光到盘外最亮像素 ≈ TARGET_PX 再按 intensity 归一**（`exposed_render`），不共用一个
# intensity。太阳盘（θ ≤ DISK_DEG）单独处理：0° 族里无反射的平行光路（`1-2`、`3-6`…）不偏折、全落在太阳 0.5° 盘内几个像素里，任何能看清晕环的曝光
# 都把它削顶，所以全景与 0° 族各多渲染一份 dim 曝光只取盘内能量，与 bright 曝光的盘外能量按 intensity 归一后相加。像素积分 vs MC 光子计数是两条
# 独立链路（D65 vs 550 nm、R+G+B vs Y、量化残余），单轨道探针相对偏差 −2%…+9%，容差在 fig_odd_radius_families.py 里先用 63.8° 族实测后写死。
# 模块分两区：**领域专属**（族 / 过滤器 / top-3 / 场景段）与**通用角度统计**（径向剖面、峰/背景、环带方位覆盖率——只认图与方向，不认晶体），
# 后者是将来第三个同类实例出现时提炼进 `halo_notes/` 的切分点（本任务 `halo_notes/` 只读）。`linear_luminance` 与 `_ch8_sim` 同一份实现的
# 章内复制（跨章上提待另立任务，与 ch8 记的同一笔债）。
from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from halo_notes.sim import config as C
from halo_notes.sim import fetch
from halo_notes.sim.figure import sim_figure
from halo_notes.sim.projection import rectangular_pixel_directions
from halo_notes.sim.run import RenderResult, render

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import analyze_energy as AE  # noqa: E402
import enumerate_signatures as ES  # noqa: E402

CHAPTER = CODE_DIR.parent
DATA = CHAPTER / "data"

TIER: tuple[float, float] = (1.0, 0.5)      # 默认档（signature_table / energy_table 的默认档，数据最全）
FILTER_ID = 1                                # 顶层过滤器 id（复合或单光路）；scattering entry 引用它
SYMMETRY = "PBD"
SUN_ALT = 20.0                               # 与 analysis_h1_t0.5.lumice.json 同；20°–24° 那一圈不贴地平线
MAX_HITS = AE.MC_MAX_LEN                     # = 4，见文件头
RECT_RESOLUTION = (1440, 720)                # 1/4°/px 全天图（同 ch8 参考图）。2880×1440 曾试过：numpy 2.5.3 + Accelerate 对 (1440, 2880, 3) @ (3, 3)
                                             # 批量 matmul 第 2 次调用即 segfault（`projection.rectangular_pixel_directions`，1440×720 连跑 30 次无事），
                                             # 本任务 `halo_notes/` 只读，先退回 ch8 已验证的分辨率，bug 记 scratchpad/backlog.md
FISHEYE_PX = 1800
PROFILE_BIN_DEG = 0.25                       # 径向剖面桶宽（= 1 px；20°–24° 四圈相邻只差 1°，桶再宽就分不开）
MAX_FILTERS = 256                            # Lumice v4.5.1 `LUMICE_MAX_CONFIG_FILTERS`（src/include/lumice.h:543，c_api.cpp:2883 超限即 error code 3
                                             # INVALID_CONFIG，2026-09-20 用 1521 个过滤器的余量 config 实测撞上）；复合过滤器本身占 1 个槽

DISK_DEG = 1.0                               # 太阳盘掩模半径：0° 族无反射光路不偏折，全在太阳 0.5° 盘 + 1 px 内（2×10⁷ 探针：盘内能量 100% 来自 0° 族）
TARGET_PX = 200                              # 曝光目标：关注区域最亮像素 ≈ 200/255（留 20% 余量给正式光线数下的热像素）
PROBE_RAYS_DIV = 10                          # 曝光探针用正式光线数的 1/10（热像素只会更亮，换算出的 intensity 偏保守）
PX_OK = (100, 254)                           # 正式渲染后关注区域最亮像素须落在此区间，否则再修正一轮
MAX_EXPOSURE_ROUNDS = 4                      # 关注区域削顶就再压低一轮重渲（小光线数下散斑热像素会削顶），最多 4 轮

KNOWN_WEDGES = ES.KNOWN_WEDGES
KNOWN_RADII = {w: ES.min_deviation_deg(w) for w in KNOWN_WEDGES if w > 0}   # 8 个晕半径（0° 平行族无晕）


# ======================================================================================================
# 领域专属：Lumice 版本门槛 / 族成员 / 过滤器 / 族外 top-3 / 场景段
# ======================================================================================================


def ensure_lumice_version(expected: str = fetch.LUMICE_VERSION) -> Path:
    """正式渲染的版本门槛（机制化，不靠步骤顺序）：环境里不得有 ``LUMICE_BIN`` 覆盖（那是本地 build 的入口），
    并经 :func:`halo_notes.sim.fetch.ensure_lumice` 取得 / 下载 release ``expected`` 的缓存二进制，返回路径必须落在
    ``cached_binary(expected)``。``--replot``（不跑仿真）不调本函数。"""
    override = os.environ.get("LUMICE_BIN")
    if override:
        raise RuntimeError(f"正式渲染只用 release {expected}：检测到 LUMICE_BIN={override!r}（本地 build 入口），先 `unset LUMICE_BIN`")
    path = fetch.ensure_lumice(expected)
    want = fetch.cached_binary(expected)
    if path.resolve() != want.resolve():
        raise RuntimeError(f"ensure_lumice 返回 {path}，不是 release {expected} 的缓存路径 {want}")
    return path


@dataclass(frozen=True)
class RaypathRow:
    """`raypaths_<tier>.csv` 的一行（PBD 代表）。"""

    faces: tuple[int, ...]
    length: int
    area_sr: float
    wedge_deg: float | None
    family: float | None

    @property
    def label(self) -> str:
        return "-".join(map(str, self.faces))


_ROWS: dict[tuple[float, float], tuple[RaypathRow, ...]] = {}


def load_raypaths(tier: tuple[float, float] = TIER) -> tuple[RaypathRow, ...]:
    """读 `raypaths_<tier>.csv`（进程内缓存）。"""
    if tier not in _ROWS:
        path = DATA / f"raypaths_{ES.tier_label(tier)}.csv"
        with path.open() as fp:
            rows = tuple(
                RaypathRow(
                    faces=tuple(int(f) for f in r["raypath"].split("-")),
                    length=int(r["length"]),
                    area_sr=float(r["area_sr"]),
                    wedge_deg=float(r["wedge_deg"]) if r["wedge_deg"] else None,
                    family=float(r["family"]) if r["family"] else None,
                )
                for r in csv.DictReader(fp)
            )
        _ROWS[tier] = rows
    return _ROWS[tier]


def family_members(tier: tuple[float, float] = TIER) -> dict[float, tuple[tuple[int, ...], ...]]:
    """9 族标称楔角 → 该族在该档全部代表光路（按 (长度, 字典序) 排）。"""
    out: dict[float, list[tuple[int, ...]]] = {}
    for r in load_raypaths(tier):
        if r.family is not None:
            out.setdefault(r.family, []).append(r.faces)
    return {w: tuple(sorted(v, key=lambda s: (len(s), s))) for w, v in out.items()}


def off_family_members(tier: tuple[float, float] = TIER) -> tuple[tuple[int, ...], ...]:
    """族外代表光路（`family` 空且长度 > 1——单面外反射不在族框架里，也不算「族外」）。"""
    return tuple(r.faces for r in load_raypaths(tier) if r.family is None and r.length > 1)


def renderable_members(wedge: float, tier: tuple[float, float] = TIER, *, max_hits: int = MAX_HITS) -> tuple[tuple[int, ...], ...]:
    """族 ``wedge`` 在 ``max_hits`` 下**能被命中**的代表：长度 ≤ max_hits 的成员（Lumice 一条光线最多碰 max_hits 个面，含入射面，
    doc/configuration.md `max_hits`）。装进过滤器的就是这个集合，与「全部成员」的差集只含长度 > max_hits 的条目（单测钉住）。"""
    members = family_members(tier)
    if wedge not in members:
        raise KeyError(f"族 {wedge:g}° 在档位 {tier} 不可达（raypaths csv 里没有成员）")
    return tuple(seq for seq in members[wedge] if len(seq) <= max_hits)


def _complex_over(members: tuple[tuple[int, ...], ...], *, action: str, symmetry: str = SYMMETRY) -> list[dict]:
    if len(members) + 1 > MAX_FILTERS:
        raise ValueError(f"{len(members)} 个子过滤器 + 1 个复合过滤器超过 Lumice v4.5.1 上限 {MAX_FILTERS}")
    subs = [C.raypath_filter(FILTER_ID + 1 + i, list(seq), symmetry) for i, seq in enumerate(members)]
    return [C.complex_filter(FILTER_ID, [f["id"] for f in subs], symmetry, action=action)] + subs


def family_filters(wedge: float, tier: tuple[float, float] = TIER) -> list[dict]:
    """过滤器段：``[complex(id=FILTER_ID, OR 该族 ≤ MAX_HITS 面的全部代表, PBD), raypath(id=2), raypath(id=3), …]``（形态同 ch7 / ch8）。"""
    return _complex_over(renderable_members(wedge, tier), action="filter_in")


def remainder_filter(tier: tuple[float, float] = TIER) -> list[dict]:
    """过滤器段：9 族（≤ MAX_HITS 面）全部代表的并集装一个 ``complex(action="filter_out")``——渲染「全天 − 9 族」。单面外反射（长度 1）
    天然不在并集里，所以余量同时含「族外多次反射」与「单面外反射」，与 `energy_table.md` 的族外 + 单面外反射口径一致。"""
    union = tuple(seq for w in sorted(family_members(tier)) for seq in renderable_members(w, tier))
    return _complex_over(union, action="filter_out")


def single_raypath_filter(faces: tuple[int, ...], *, symmetry: str = SYMMETRY) -> list[dict]:
    """过滤器段：一条光路（top-3 用），``[raypath(id=FILTER_ID, faces, PBD)]``。"""
    return [C.raypath_filter(FILTER_ID, list(faces), symmetry)]


def filter_paths(filters: list[dict]) -> set[tuple[int, ...]]:
    """反向：顶层过滤器覆盖的全部子光路（复合 → 引用的子过滤器；单光路 → 它自己），单测 / 脚本落盘自检用。"""
    by_id = {f["id"]: f for f in filters}
    top = by_id[FILTER_ID]
    if top["type"] == "complex":
        return {tuple(by_id[i]["raypath"]) for i in C.composition_ids(top)}
    return {tuple(top["raypath"])}


@dataclass(frozen=True)
class OffFamilyPath:
    """族外 PBD 代表 + 该轨道全部 MC 行的能量份额之和。"""

    faces: tuple[int, ...]
    wedge_deg: float
    energy_pct: float
    n_rows: int

    @property
    def label(self) -> str:
        return "-".join(map(str, self.faces))

    @property
    def radius_deg(self) -> float:
        """晕半径 = 最小偏向角（`enumerate_signatures.min_deviation_deg`）。"""
        return ES.min_deviation_deg(self.wedge_deg)


def top_out_of_family(n: int = 3, tier: tuple[float, float] = TIER) -> list[OffFamilyPath]:
    """`analysis/rows_<tier>.csv` 里 ``family == ''`` 且 ``status == 'ok'`` 的行按 ``pbd_rep`` 分组求和 ``energy_pct``，取前 ``n``。
    默认档已核实：`13-24-26`（19.5°）0.300% 居首；未分组单行第一 `28-13-15` 0.0129% 只是它的一个对称像。"""
    AE.ensure_unpacked()
    path = AE.CACHE / f"rows_{ES.tier_label(tier)}.csv"
    with path.open() as fp:
        rows = list(csv.DictReader(line for line in fp if not line.startswith("#")))
    acc: dict[str, list[float]] = {}
    wedge: dict[str, float] = {}
    for r in rows:
        if r["family"] != "" or r["status"] != "ok":
            continue
        acc.setdefault(r["pbd_rep"], []).append(float(r["energy_pct"]))
        w = float(r["wedge_deg"])
        if r["pbd_rep"] in wedge and abs(wedge[r["pbd_rep"]] - w) > 1e-9:
            raise ValueError(f"{r['pbd_rep']} 同一 PBD 轨道出现两个楔角 {wedge[r['pbd_rep']]} / {w}")
        wedge[r["pbd_rep"]] = w
    ranked = sorted(acc.items(), key=lambda kv: (-sum(kv[1]), kv[0]))
    return [OffFamilyPath(tuple(int(f) for f in rep.split("-")), wedge[rep], float(sum(v)), len(v)) for rep, v in ranked[:n]]


# ---- 场景 / 渲染段 ----


def crystal() -> dict:
    """默认档锥晶、随机取向（`random_axis()`：zenith 球面均匀，azimuth / roll 省略 = 均匀）。"""
    return C.pyramid_crystal_from_geometry(1, ES.tier_pyramid(TIER), axis=C.random_axis())


def scene(ray_num: int, *, filtered: bool = True) -> dict:
    """太阳 ``SUN_ALT``、D65；``filtered=False`` 时 entry 不挂过滤器（全景）。"""
    entry = C.entry(1, filter=FILTER_ID) if filtered else C.entry(1)
    return C.scene(C.sun(SUN_ALT), ray_num, [entry], max_hits=MAX_HITS)


def rect_render(intensity_factor: float) -> dict:
    """全天 ``rectangular``（absolute 曝光、无网格、黑底）：取数用，四类产出同一 intensity 才可比。"""
    return C.render_unit(1, C.lens("rectangular"), list(RECT_RESOLUTION), visible="full", background=[0, 0, 0],
                         ev_mode="absolute", intensity_factor=intensity_factor)


def fisheye_render(intensity_factor: float, *, ev_mode: str = "absolute") -> dict:
    """天顶朝上的等面积鱼眼（fov 180，仿 ch2 `fig_rp1_3_note.py`）：只看图，不取数。"""
    return C.render_unit(1, C.lens("fisheye_equal_area", fov=180), [FISHEYE_PX, FISHEYE_PX], view={"elevation": 90},
                         visible="full", background=[0, 0, 0], ev_mode=ev_mode, intensity_factor=intensity_factor)


def sky(el_deg: float, az_deg: float) -> np.ndarray:
    e, a = np.radians(el_deg), np.radians(az_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def sun_direction(sun_alt: float = SUN_ALT) -> np.ndarray:
    """太阳方向（Lumice 方位角 0° = +x = 太阳）。"""
    return sky(sun_alt, 0.0)


# ---- 曝光包围 / 产出读写 ----


def load_image(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def product_dir(name: str, variant: str | None, out_root: Path | None = None) -> Path:
    root = out_root or CHAPTER
    return root / "data" / name if variant is None else root / "data" / name / variant


def load_product(name: str, variant: str | None, out_root: Path | None = None) -> tuple[np.ndarray, dict]:
    """已落盘的一份渲染产出：``(图, config)``（`--replot` 用；config 读产出目录里的 `config.json`）。"""
    d = product_dir(name, variant, out_root)
    cfg = json.loads((d / "config.json").read_text())
    return load_image(d / "img_01.png"), cfg


def exposure_stats(image: np.ndarray, render: dict, *, sun_alt: float = SUN_ALT, disk_deg: float = DISK_DEG) -> dict[str, float]:
    """一张 rectangular 图的曝光 / 能量统计：盘内（θ ≤ disk_deg）与盘外各自的能量、最亮像素、削顶像素数；``intensity`` 取自 render 段，
    ``energy_*_per_i`` 已按 intensity 归一。"""
    energy, _, dirs = energy_map(image, render)
    theta = np.degrees(np.arccos(np.clip(dirs @ sun_direction(sun_alt), -1.0, 1.0)))
    disk = theta <= disk_deg
    mx = np.asarray(image).max(axis=-1)
    i = float(render["intensity_factor"])
    return {
        "intensity": i,
        "energy_out_per_i": float(energy[~disk].sum() / i),
        "energy_disk_per_i": float(energy[disk].sum() / i),
        "max_out": int(mx[~disk].max()),
        "max_disk": int(mx[disk].max()),
        "sat_out": int((mx[~disk] >= 255).sum()),
        "sat_disk": int((mx[disk] >= 255).sum()),
    }


def _srgb_to_linear(code: float) -> float:
    a = code / 255.0
    return a / 12.92 if a <= 0.04045 else ((a + 0.055) / 1.055) ** 2.4


def _exposure_gain(max_code: float, target: float = TARGET_PX) -> float:
    """把最亮像素从 sRGB 码值 ``max_code`` 抬到 ``target`` 需要乘的 intensity 倍率——intensity 与**线性**亮度成正比，码值是 gamma 编码的，
    按码值线性换算会欠曝一截（首轮实跑：码值 40 × 5 只到 89）。"""
    return _srgb_to_linear(target) / _srgb_to_linear(max_code)


def exposed_render(name: str, variant: str, make_config: Callable[[float, int], dict], *, region: str, ray_num: int,
                   out_root: Path | None = None, workers: int | None = None, backend: str | None = None,
                   probe_intensity: float = 0.2) -> tuple[RenderResult, dict, dict[str, float | int]]:
    """曝光包围后正式渲染一份产出：``make_config(intensity, ray_num)`` 生成 config；先用 ``ray_num // PROBE_RAYS_DIV`` 光线、
    ``probe_intensity`` 在临时目录探一次，按 ``region``（``"out"`` 盘外 / ``"disk"`` 盘内）最亮像素线性换算到 TARGET_PX，再以正式光线数经
    :func:`sim_figure` 落盘；落盘后关注区域最亮像素不在 PX_OK 内就再修正一轮（最多两轮）。返回 ``(RenderResult, config, stats)``，
    ``stats`` = :func:`exposure_stats` + ``probe_intensity`` / ``probe_max`` / ``rounds``。"""
    key = {"out": "max_out", "disk": "max_disk"}[region]
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_config(probe_intensity, max(ray_num // PROBE_RAYS_DIV, 1))
        res = render(cfg, Path(tmp) / "probe", workers=workers, backend=backend)
        probe = exposure_stats(load_image(res.images[0]), cfg["render"][0])
    if probe[key] <= 0:
        raise ValueError(f"{name}.{variant}: 曝光探针在关注区域（{region}）全黑，无法定曝光")
    intensity = probe_intensity * _exposure_gain(probe[key])
    sat_key = {"out": "sat_out", "disk": "sat_disk"}[region]
    for rounds in range(1, MAX_EXPOSURE_ROUNDS + 1):
        cfg = make_config(intensity, ray_num)
        res = sim_figure(name, CHAPTER, cfg, out_root=out_root, workers=workers, backend=backend, variant=variant)
        stats = exposure_stats(load_image(res.images[0]), cfg["render"][0])
        if stats[sat_key] > 0:                                   # 关注区域削顶：产出不可用，按 255 反推再压低一截重来
            intensity *= _exposure_gain(255, target=TARGET_PX * 0.75)
        elif PX_OK[0] <= stats[key] <= PX_OK[1] or rounds >= 2:  # 落在目标区间，或已修正过一轮（未削顶时第二轮就收）
            break
        else:
            intensity *= _exposure_gain(max(stats[key], 1))
    stats.update(probe_intensity=probe_intensity, probe_max=probe[key], rounds=rounds, ray_num=ray_num)
    return res, cfg, stats


def render_product(name: str, variant: str, make_config: Callable[[float, int], dict], *, ray_num: int, dim: str = "auto",
                   out_root: Path | None = None, workers: int | None = None, backend: str | None = None,
                   dim_probe_intensity: float = 0.001) -> dict[str, dict]:
    """一份产出的完整曝光集：bright（盘外定曝光，变体名 ``variant``）+ 视需要的 dim（盘内定曝光，变体名 ``variant + "_dim"``）。
    ``dim``：``"always"`` / ``"never"`` / ``"auto"``（bright 盘内有削顶像素才补 dim）。返回 ``{"bright": stats, "dim": stats | None}``。"""
    out: dict[str, dict] = {}
    _, _, out["bright"] = exposed_render(name, variant, make_config, region="out", ray_num=ray_num, out_root=out_root,
                                         workers=workers, backend=backend)
    need_dim = dim == "always" or (dim == "auto" and out["bright"]["sat_disk"] > 0)
    if need_dim:
        _, _, out["dim"] = exposed_render(name, variant + "_dim", make_config, region="disk", ray_num=ray_num, out_root=out_root,
                                          workers=workers, backend=backend, probe_intensity=dim_probe_intensity)
    else:
        out["dim"] = None
    return out


def reload_product(name: str, variant: str, out_root: Path | None = None) -> dict[str, dict]:
    """`--replot`：从已落盘的 bright（+ 可选 dim）产出重算 :func:`exposure_stats`（不跑 Lumice）。"""
    img, cfg = load_product(name, variant, out_root)
    out: dict[str, dict] = {"bright": exposure_stats(img, cfg["render"][0]), "dim": None}
    out["bright"]["ray_num"] = cfg["scene"]["ray_num"]
    if product_dir(name, variant + "_dim", out_root).exists():
        img, cfg = load_product(name, variant + "_dim", out_root)
        out["dim"] = exposure_stats(img, cfg["render"][0])
        out["dim"]["ray_num"] = cfg["scene"]["ray_num"]
    return out


def total_energy_per_i(bright: dict[str, float], dim: dict[str, float] | None = None) -> float:
    """一份产出按 intensity 归一的全天能量：盘外取 bright 曝光；盘内有 dim 曝光取 dim（bright 在盘内削顶），否则取 bright。
    bright 盘外削顶、或没有 dim 曝光而 bright 盘内削顶，都直接报错（数字不可信就不给数字）。"""
    if bright["sat_out"] > 0:
        raise ValueError(f"bright 曝光盘外有 {bright['sat_out']} 个削顶像素，能量不可信")
    if dim is None:
        if bright["sat_disk"] > 0:
            raise ValueError(f"没有 dim 曝光而 bright 曝光盘内有 {bright['sat_disk']} 个削顶像素")
        return bright["energy_out_per_i"] + bright["energy_disk_per_i"]
    if dim["sat_disk"] > 0:
        raise ValueError(f"dim 曝光盘内仍有 {dim['sat_disk']} 个削顶像素")
    return bright["energy_out_per_i"] + dim["energy_disk_per_i"]


def numbers_path(name: str, out_root: Path | None = None) -> Path:
    return (out_root or CHAPTER) / "data" / f"{name}.numbers.json"


def write_numbers(name: str, numbers: dict, out_root: Path | None = None) -> Path:
    """脚本的全部取数落 ``data/<name>.numbers.json``（入 git；`data/notes.md` 里的每个数字都能回溯到这里）。"""
    path = numbers_path(name, out_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(numbers, indent=2, ensure_ascii=False) + "\n")
    return path


def read_numbers(name: str, out_root: Path | None = None) -> dict:
    return json.loads(numbers_path(name, out_root).read_text())


# ======================================================================================================
# 通用角度统计：只认 rectangular 图 + render 段 + 一个中心方向，不认晶体
# ======================================================================================================

PEAK_RATIO = 3.0          # 「有峰」判据：峰值 / 局部背景 ≥ 3（plan 初值；调整须连同理由记 data/notes.md）
BG_WINDOW_DEG = 10.0      # 局部背景取峰位 ±10° 窗口内「非峰窗口」的中位数：剔除峰位 ±BG_EXCLUDE_DEG、8 个已知晕半径的环带（RING_ZONES，否则
BG_EXCLUDE_DEG = 2.0      # 20°–24° 四环挤在 4° 里时中位数被邻环抬高——2×10⁸ 探针 20° 环峰值是环间底噪的 9.5 倍、却只有邻环中位数的 1.5 倍）
                          # 与太阳盘外沿（θ < DISK_ZONE_DEG，0° 族削顶的盘 + 前向散射坡）；全天剖面近日 / 远日亮度差一个量级以上，不能用全局中位数
DISK_ZONE_DEG = 2.0
ARC_COVERAGE = 0.10       # 「弧」判据：环带内亮起的方位角格数占比 ≥ 10%（plan 初值）
ARC_BIN_RATIO = 2.0       # 方位格「亮起」= 该格环带均值 ≥ 2 × 局部径向背景
ARC_AZ_BIN_DEG = 5.0      # 方位角格宽
RING_INNER_DEG, RING_OUTER_DEG = 0.5, 2.5    # 环带 = [R − 0.5°, R + 2.5°]（晕的亮边在最小偏向角外侧，内缘锐、外侧拖尾）
RING_ZONES = tuple((r - RING_INNER_DEG, r + RING_OUTER_DEG) for r in sorted(KNOWN_RADII.values()))   # 背景估计时剔除的 8 个环带
WINDOW_BELOW_DEG, WINDOW_ABOVE_DEG = 0.25, 2.5    # 已知半径 R 的峰搜索窗 [R − 0.25°, R + 2.5°]：逐族图（2×10⁸）实测环的内缘都在 R（R − 0.3° 处为 0），
                                                  # 峰位 R + 0.4…1.9°（9°/22°/24° 环 +0.4…0.8°，46° 环 +1.6°，18° 环最宽 +1.85°）。单环图（逐族 / top-3）直接在窗内找 argmax；
                                                  # 全景里 20°/22°/23°/24° 相邻只差 1.0–1.8°、窗互相重叠，改为先找整条曲线的局部极大再归到
                                                  # 「峰位 − 0.25° 以下最近的已知半径」（`assign_peaks`），不用窗切邻环


def radius_window(radius_deg: float) -> tuple[float, float]:
    return (radius_deg - WINDOW_BELOW_DEG, radius_deg + WINDOW_ABOVE_DEG)


def assign_peaks(peaks: list[dict], radii: dict[float, float] | None = None) -> dict[float, dict | None]:
    """把 :func:`detect_peaks` 的峰归到已知半径：峰位 p 归给满足 R ≤ p + WINDOW_BELOW_DEG 且 p − R ≤ WINDOW_ABOVE_DEG 的**最大** R
    （峰在最小偏向角外侧，取下方最近的半径）；同一半径收到多个峰取 ratio 最高的。返回 {楔角: 峰 | None}。"""
    radii = KNOWN_RADII if radii is None else radii
    out: dict[float, dict | None] = {w: None for w in radii}
    for pk in peaks:
        p = float(pk["peak_deg"])
        cands = [(r, w) for w, r in radii.items() if r <= p + WINDOW_BELOW_DEG and p - r <= WINDOW_ABOVE_DEG]
        if not cands:
            continue
        _, w = max(cands)
        if out[w] is None or pk["ratio"] > out[w]["ratio"]:
            out[w] = pk
    return out


def linear_luminance(image: np.ndarray) -> np.ndarray:
    """8-bit sRGB → 线性亮度（三通道之和）；与 `_ch8_sim.linear_luminance` 同一实现。"""
    a = np.asarray(image, float) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return lin.sum(axis=-1) if lin.ndim == 3 else lin


def energy_map(image: np.ndarray, render: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(每像素能量 L·w, 立体角权重 w, 像素天空方向 dirs)``。"""
    dirs, weight = rectangular_pixel_directions(render)
    return linear_luminance(image) * weight, weight, dirs


def sky_energy(image: np.ndarray, render: dict) -> float:
    """全天线性能量（立体角加权）。"""
    energy, _, _ = energy_map(image, render)
    return float(energy.sum())


def angular_radial_profile(image: np.ndarray, render: dict, center_dir: np.ndarray, *, bin_deg: float = PROFILE_BIN_DEG,
                           max_deg: float = 180.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """以 ``center_dir``（太阳）为极点的径向剖面：像素按「与中心方向的夹角」θ 分桶（0…``max_deg`` 每 ``bin_deg``）。
    返回 ``(桶中心, 各桶平均辐亮度 Σ(L·w)/Σw, 各桶能量 Σ(L·w))``——「峰」看平均辐亮度（均匀背景在这条曲线上是平的，
    不带 sin θ 的环周长因子），「能量占比」看能量。"""
    energy, weight, dirs = energy_map(image, render)
    c = np.asarray(center_dir, float)
    c = c / np.linalg.norm(c)
    theta = np.degrees(np.arccos(np.clip(dirs @ c, -1.0, 1.0)))
    edges = np.arange(0.0, max_deg + bin_deg, bin_deg)
    e_hist, _ = np.histogram(theta, bins=edges, weights=energy)
    w_hist, _ = np.histogram(theta, bins=edges, weights=weight)
    radiance = np.divide(e_hist, w_hist, out=np.zeros_like(e_hist), where=w_hist > 0)
    return (edges[:-1] + edges[1:]) / 2, radiance, e_hist


def local_background(centers: np.ndarray, profile: np.ndarray, at_deg: float, *, window_deg: float = BG_WINDOW_DEG,
                     exclude_deg: float = BG_EXCLUDE_DEG, zones: tuple[tuple[float, float], ...] = RING_ZONES,
                     disk_zone_deg: float = DISK_ZONE_DEG) -> float:
    """``at_deg`` 处的局部背景：|θ − at| ≤ window、且 > exclude、且不落在任何 ``zones``（已知环带）与 θ < disk_zone 里的桶的中位数——
    「非峰窗口的中位数」。窗口里没剩下桶时把 window 翻倍再试（最多两次），仍没有就报错。"""
    d = np.abs(centers - at_deg)
    keep = (d > exclude_deg) & (centers >= disk_zone_deg)
    for lo, hi in zones:
        keep &= ~((centers >= lo) & (centers <= hi))
    for k in range(3):
        m = keep & (d <= window_deg * 2 ** k)
        if m.any():
            return float(np.median(profile[m]))
    raise ValueError(f"{at_deg}° 附近没有背景桶（window {window_deg}° ×4 内全被环带 / 排除区占满）")


def peak_over_background(centers: np.ndarray, profile: np.ndarray, window: tuple[float, float] | None = None, *,
                         ratio: float = PEAK_RATIO, bg_window_deg: float = BG_WINDOW_DEG,
                         bg_exclude_deg: float = BG_EXCLUDE_DEG, zones: tuple[tuple[float, float], ...] = RING_ZONES) -> dict[str, float | bool]:
    """``window``（度，闭区间；None = 整条曲线）内的峰：``peak_deg``（argmax 桶中心）、``peak``、``background``（局部背景）、
    ``ratio`` = peak / background（背景为 0 时 inf）、``is_local_max``（argmax 不落在窗口边缘、且 ≥ 左右邻桶——落在边缘说明窗口里只是
    单调坡，不是峰）、``detected`` = is_local_max 且 ratio ≥ ``ratio``。"""
    m = np.ones_like(centers, bool) if window is None else (centers >= window[0]) & (centers <= window[1])
    idx = np.flatnonzero(m)
    if idx.size == 0:
        raise ValueError(f"窗口 {window} 内没有桶")
    i = int(idx[np.argmax(profile[idx])])
    peak = float(profile[i])
    bg = local_background(centers, profile, float(centers[i]), window_deg=bg_window_deg, exclude_deg=bg_exclude_deg, zones=zones)
    r = None if bg <= 0 else peak / bg                      # 背景低于量化底（0）时比值无定义，记 None（JSON 里不写 Infinity）
    at_edge = i in (idx[0], idx[-1]) and window is not None
    neighbours = profile[max(i - 1, 0): i + 2]
    is_max = (not at_edge) and bool(np.all(peak >= neighbours)) and peak > 0
    return {"peak_deg": float(centers[i]), "peak": peak, "background": bg, "ratio": r, "is_local_max": is_max,
            "detected": bool(is_max and (r is None or r >= ratio))}


def detect_peaks(centers: np.ndarray, profile: np.ndarray, *, ratio: float = PEAK_RATIO, min_deg: float = DISK_ZONE_DEG,
                 max_deg: float = 179.0, bg_window_deg: float = BG_WINDOW_DEG,
                 bg_exclude_deg: float = BG_EXCLUDE_DEG, zones: tuple[tuple[float, float], ...] = RING_ZONES) -> list[dict[str, float | bool]]:
    """整条曲线上全部过阈值的局部极大（``min_deg``…``max_deg`` 内；两端各留 1° 防边界假峰）：每个局部极大算一次
    :func:`local_background`，ratio ≥ ``ratio`` 才收；相邻桶等高时取靠前的一个。按 θ 升序返回。"""
    out = []
    for i in range(1, len(profile) - 1):
        if not (min_deg <= centers[i] <= max_deg):
            continue
        if profile[i] <= 0 or profile[i] < profile[i - 1] or profile[i] <= profile[i + 1]:
            continue
        bg = local_background(centers, profile, float(centers[i]), window_deg=bg_window_deg, exclude_deg=bg_exclude_deg, zones=zones)
        r = None if bg <= 0 else float(profile[i] / bg)
        if r is None or r >= ratio:
            out.append({"peak_deg": float(centers[i]), "peak": float(profile[i]), "background": bg, "ratio": r,
                        "is_local_max": True, "detected": True})
    return out


def energy_quantiles(centers: np.ndarray, energy: np.ndarray, qs: tuple[float, ...] = (0.1, 0.5, 0.9)) -> dict[str, float]:
    """径向能量剖面的累积分位：``{"q10": θ, "q50": θ, "q90": θ}``——光「落在哪」的机械描述（一条光路的像不一定在最小偏向角半径上：
    带中间反射的光路被折叠矩阵 M 搬到别处，随机取向下可以散到反日侧整片天）。"""
    cum = np.cumsum(energy) / energy.sum()
    return {f"q{int(q * 100)}": float(centers[int(np.searchsorted(cum, q))]) for q in qs}


OBSERVED_BIN_DEG = 1.0    # 找「光实际最亮在哪」用 1° 桶：0.25° 桶在 θ → 180°（反日点）处一桶只剩两三个像素，辐亮度均值是噪声


def observed_peak(image: np.ndarray, render: dict, center_dir: np.ndarray, *, bin_deg: float = OBSERVED_BIN_DEG,
                  min_deg: float = DISK_ZONE_DEG, half_window_deg: float = 3.0, **kw) -> dict[str, float | bool]:
    """``bin_deg`` 桶的平均辐亮度曲线（θ ≥ min_deg）的最高点及其 :func:`peak_over_background`（窗 = 最高点 ±half_window）。"""
    centers, radiance, _ = angular_radial_profile(image, render, center_dir, bin_deg=bin_deg)
    m = centers >= min_deg
    i = int(np.flatnonzero(m)[np.argmax(radiance[m])])
    at = float(centers[i])
    out = peak_over_background(centers, radiance, (at - half_window_deg, at + half_window_deg), **kw)
    out["bin_deg"] = bin_deg
    return out


def _azimuth_about(dirs: np.ndarray, center: np.ndarray) -> np.ndarray:
    """每个方向绕 ``center`` 轴的方位角（度，0…360；零点取 ``center`` 与世界 z 轴张成平面里的「上」方向）。"""
    c = np.asarray(center, float)
    c = c / np.linalg.norm(c)
    up = np.array([0.0, 0.0, 1.0])
    u = up - (up @ c) * c
    if np.linalg.norm(u) < 1e-9:                       # 中心正对天顶：任取
        u = np.array([1.0, 0.0, 0.0]) - c[0] * c
    u /= np.linalg.norm(u)
    v = np.cross(c, u)
    return np.degrees(np.arctan2(dirs @ v, dirs @ u)) % 360.0


def arc_or_spot(image: np.ndarray, render: dict, center_dir: np.ndarray, radius_deg: float, *,
                inner_deg: float = RING_INNER_DEG, outer_deg: float = RING_OUTER_DEG, az_bin_deg: float = ARC_AZ_BIN_DEG,
                bin_ratio: float = ARC_BIN_RATIO, coverage: float = ARC_COVERAGE,
                profile_bin_deg: float = PROFILE_BIN_DEG, zones: tuple[tuple[float, float], ...] = RING_ZONES) -> dict[str, float | str | bool]:
    """环带 [R − inner, R + outer] 内按绕 ``center_dir`` 的方位角分格（``az_bin_deg``），格「亮起」= 格内平均辐亮度 ≥ ``bin_ratio`` ×
    局部径向背景（背景来自同一张图的径向剖面在 R 处的 :func:`local_background`，剔除环带本身）；``coverage`` = 亮起格数 / 总格数，
    ≥ ``coverage`` 判 ``"arc"``，0 < 覆盖率 < coverage 判 ``"spot"``，一格都没亮判 ``"none"``（环带与背景不可分）。顺带给出径向剖面在环带窗口内的峰（:func:`peak_over_background`），
    「环是否锐」看它的 ratio。注意：随机取向下天空关于太阳方向旋转对称，任何光路的像都是整圈——这时 coverage 恒接近 1，
    真正区分「有自己的弧 / 散成背景」的是径向峰/背景比。"""
    energy, weight, dirs = energy_map(image, render)
    c = np.asarray(center_dir, float)
    c = c / np.linalg.norm(c)
    theta = np.degrees(np.arccos(np.clip(dirs @ c, -1.0, 1.0)))
    ring = (theta >= radius_deg - inner_deg) & (theta <= radius_deg + outer_deg)
    centers, radiance, _ = angular_radial_profile(image, render, c, bin_deg=profile_bin_deg)
    bg = local_background(centers, radiance, radius_deg, exclude_deg=max(inner_deg, outer_deg),
                          zones=zones + ((radius_deg - inner_deg, radius_deg + outer_deg),))
    az = _azimuth_about(dirs[ring], c)
    edges = np.arange(0.0, 360.0 + az_bin_deg, az_bin_deg)
    e_hist, _ = np.histogram(az, bins=edges, weights=energy[ring])
    w_hist, _ = np.histogram(az, bins=edges, weights=weight[ring])
    mean = np.divide(e_hist, w_hist, out=np.zeros_like(e_hist), where=w_hist > 0)
    lit = mean >= bin_ratio * bg if bg > 0 else mean > 0
    cov = float(lit.sum() / lit.size)
    radial = peak_over_background(centers, radiance, (radius_deg - inner_deg, radius_deg + outer_deg), zones=zones)
    verdict = "arc" if cov >= coverage else ("spot" if cov > 0 else "none")     # none：环带里没有任何方位格亮到 bin_ratio × 背景
    return {"radius_deg": float(radius_deg), "background": bg, "coverage": cov, "n_bins": int(lit.size),
            "verdict": verdict, "ring_energy_frac": float(energy[ring].sum() / energy.sum()),
            "radial_peak_deg": radial["peak_deg"], "radial_ratio": radial["ratio"], "radial_is_local_max": radial["is_local_max"]}
