# 产出 ../data/energy_table.md（9 个楔角族在锥晶上的蒙特卡洛能量份额表 + 与精确枚举的族级 / 光路级互证，入 git）与 ../data/analysis/
# （每档几何的原始 CSV / lumice.log / provenance.json 落 analysis/<tier>/，MC 逐行表落 analysis/rows_<tier>.csv：面序列 → PBD 代表 →
# 楔角 / 族，附互证状态；目录被 .gitignore 忽略，打包成 ../data/analysis.zip 走 LFS 入库；启动时若本地没有 analysis/ 而有
# analysis.zip 就自动解包，跑完全部档位后重新打包）：对 enumerate_signatures.TIERS 的每个 (h/a, tip_ratio) 用 Lumice 4.6.x `analyze`
# 子命令跑随机朝向锥晶、全天 ROI、`--symmetry none`（归并在 python 侧按 Φ 类 → 族做），再与 enumerate_signatures.py 产出的
# raypaths_<tier>.csv（同一次枚举的 PBD 代表清单）对表：MC 命中集 ⊆ 精确可达集（a01 独立证据链）。
#
# 口径：
# - Lumice `analyze` 子命令（release ≥ v4.6.1，`halo_notes.sim.fetch.ensure_lumice` 自动取；现存 `data/` 产物由 4.6.1 发版前的
#   本地 build 跑出，provenance 已记），config 落 data/analysis_<tier>.lumice.json（入 git），
#   原始 CSV / lumice.log / provenance.json 落 data/analysis/<tier>/（ignored，见上）；锥晶经 halo_notes.sim.analyze.pyramid_analysis_config
#   → config.pyramid_crystal_from_geometry 换算（三条换算已由 task-pyramid-sim-glue 实测钉死）；
# - **MC 侧链面数上限 MC_MAX_LEN = 4 ≪ 精确侧 L_STAR = 6**：Lumice distinct 链驻留表每 worker 只有 16384 槽，锥晶 finest 链
#   `max_len=4` 7580 行（无溢出）、`max_len=5` 就 16385 行 + record_full_hits 20374@300k 光线（task-pyramid-sim-glue 实测），
#   这是硬上限，不是可调参数。精确侧长度 5–6 的记录在互证里一律标「MC 未覆盖」，与「MC 未见」（≤4 面精确可达但 MC 没命中，
#   真正的互证信号）分开统计，不混算——tip_ratio=0.8 档的 90° 族只在长度 ≥5 出现，正是这一区分的实例；
# - 相邻重复面链整行剔除并计数上报；单面外反射行不在族框架内，只报能量份额；`other (not recorded)` 桶原样带到表尾；
# - 族外（精确楔角不在 9 个已知楔角 ± TOL 内）的 MC 行按「族外」合并成一桶报能量份额——这是 explore 阶段三种几何代理都给不出的
#   **真实能量**口径，作背景注记，不做进一步截断裁定（那是 explore-pyramid-energy-truncation 的事）；
# - `--rays` 量级准则：每档跑完用 ± 反推 9 族里最稀薄族的命中数，须 ≥ MIN_FAMILY_COUNT，否则报警（不静默）；止损：不自动加大，
#   RAYS_CAP 之上仍不达标就如实记「覆盖不足」（plan review 建议）。锥晶 MC_MAX_LEN=4 下链空间小，5M 光线就远超准则，加到 20M
#   只是为了压低「≤4 面精确可达但 MC 未见」的采样缺口（见 RAYS 旁注）。
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from enumerate_signatures import (DATA, KNOWN_WEDGES, L_STAR, TIERS, TOL, family_name, family_of, tier_label,
                                  tier_pyramid)
from lumice_integral.geometry import fold_matrix
from lumice_integral.symmetry import reflection_group as rg
from lumice_integral.symmetry.signature import A_MAX_DEG, PhiClass, phi_class
from halo_notes.sim import analyze as A

CACHE = DATA / "analysis"      # 大体积文本产物（ignored）；打包为 ZIP 走 LFS
ZIP = DATA / "analysis.zip"
MC_MAX_LEN = 4                 # 见文件头：16384 槽驻留表 ⇒ 锥晶 finest 全集只在 ≤4 面时放得下
assert MC_MAX_LEN < L_STAR
RAYS = 20_000_000              # 默认档探针：5M 时最稀薄族命中 89009（准则早已满足），但 ≤4 面精确可达却 MC 未见 14 条；20M 降到 7 条、每档 ≈ 50 s，取 20M
RAYS_CAP = 20_000_000          # 止损：超过这个量级仍不达 MIN_FAMILY_COUNT 就如实记覆盖不足，不再加大（plan review 建议）
SEED = 7
ROI = "sky"
SYMMETRY = "none"
MIN_FAMILY_COUNT = 20          # `--rays` 量级准则：9 族里最稀薄族的命中数下限（ch8 对 34 类用同一个数）
RECHECK_STEP_DEG = 0.2         # 违反项归因：细网格复核的格距（枚举器用 1°）

Tier = tuple[float, float]


def ensure_unpacked() -> None:
    """本地没有 data/analysis/ 而有 analysis.zip（LFS）时解包，让 --reuse 与读表脚本拿到文本文件。"""
    import zipfile
    if CACHE.exists() or not ZIP.exists():
        return
    if ZIP.stat().st_size < 1024 and ZIP.read_bytes().startswith(b"version https://git-lfs"):
        raise RuntimeError(f"{ZIP} 是 LFS 指针，先 `git lfs pull`")
    with zipfile.ZipFile(ZIP) as zf:
        zf.extractall(DATA)
    print(f"已从 {ZIP.name} 解包到 {CACHE.relative_to(DATA.parent)}/")


def pack() -> Path:
    """把 data/analysis/ 确定性打包成 analysis.zip（文件按路径排序、时间戳固定），内容不变则 zip 字节不变。"""
    import zipfile
    files = sorted(p for p in CACHE.rglob("*") if p.is_file())
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in files:
            info = zipfile.ZipInfo(str(f.relative_to(DATA)), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, f.read_bytes())
    return ZIP


# ---------- 精确侧：读 enumerate_signatures.py 的产出，不重跑枚举 ----------


@dataclass(frozen=True)
class ExactRecord:
    """`raypaths_<tier>.csv` 的一行（PBD 代表）；字段名与 `RaypathRecord` 对齐，`crosscheck` 只用 faces / length / area_sr。"""

    faces: tuple[int, ...]
    area_sr: float
    min_incidence_deg: float
    wedge_deg: float | None      # 单面行为 None
    family: float | None         # 族外 / 单面为 None

    @property
    def length(self) -> int:
        return len(self.faces)

    @property
    def label(self) -> str:
        return "-".join(map(str, self.faces))


def exact_records(tier: Tier) -> list[ExactRecord]:
    path = DATA / f"raypaths_{tier_label(tier)}.csv"
    out = []
    with path.open() as fp:
        for row in csv.DictReader(fp):
            out.append(ExactRecord(tuple(int(x) for x in row["raypath"].split("-")), float(row["area_sr"]),
                                   float(row["min_incidence_deg"]), float(row["wedge_deg"]) if row["wedge_deg"] else None,
                                   float(row["family"]) if row["family"] else None))
    return out


# ---------- MC 侧 ----------


def run_one(tier: Tier, rays: int, reuse: bool) -> A.AnalysisResult:
    label = tier_label(tier)
    out_dir = CACHE / label
    cfg = A.pyramid_analysis_config(tier_pyramid(tier), max_len=MC_MAX_LEN, rays=rays)
    if reuse and (out_dir / "provenance.json").exists():
        res = A.load_analysis(out_dir)
        p = res.provenance
        if p["config"] == cfg and p["rays"] == rays and p["seed"] == SEED and p["roi"] == ROI and p["symmetry"] == SYMMETRY:
            print(f"{label}: 复用 {out_dir.name}/（{p['n_rows']} 行，{p['wall_clock_s']} s）")
            return res
        print(f"{label}: 已有产物参数不符，重跑")
    (DATA / f"analysis_{label}.lumice.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    res = A.run_analysis(cfg, out_dir, roi=ROI, symmetry=SYMMETRY, rays=rays, seed=SEED)
    print(f"{label}: {len(res.rows)} 行，total_rays={res.header.total_rays}，record_full_hits={res.header.record_full_hits}，"
          f"{res.wall_clock_s:.1f} s")
    return res


class FamilyAgg:
    """一个族（或「族外」桶）的 MC 聚合：能量份额、命中数、行数、Φ 类数、PBD 代表数、最亮一行。"""

    def __init__(self) -> None:
        self.energy_pct = 0.0
        self.count = 0.0
        self.n_rows = 0
        self.classes: set[PhiClass] = set()
        self.reps: set[tuple[int, ...]] = set()
        self.brightest: A.AnalysisRow | None = None

    def add(self, cls: PhiClass, a: A.AggregatedClass) -> None:
        self.energy_pct += a.energy_pct
        self.count += a.count
        self.n_rows += a.n_rows
        self.classes.add(cls)
        self.reps |= a.reps
        if self.brightest is None or a.brightest.energy_pct > self.brightest.energy_pct:
            self.brightest = a.brightest


def aggregate_families(agg: dict[PhiClass, A.AggregatedClass]) -> tuple[dict[float, FamilyAgg], FamilyAgg]:
    """`classify_rows` 的 Φ 类聚合 → (9 族 → FamilyAgg（未命中的族不出现）, 族外桶)。"""
    fams: dict[float, FamilyAgg] = {}
    off = FamilyAgg()
    for cls, a in agg.items():
        fam = family_of(cls.wedge_deg)
        (off if fam is None else fams.setdefault(fam, FamilyAgg())).add(cls, a)
    return fams, off


class Recheck:
    """一个违反项 PBD 代表的归因：细网格可行面积 / 格数、MC 命中合计、精确楔角、归类桶。

    桶三选一：``grid_miss``——细网格可行，枚举器 1° 网格漏判的窄窗口；``dead_angle``——楔角 ≥ 2·arcsin(1/n)（Snell 定律下
    不可能透射），追迹数值边缘产物；``infeasible``——可透射楔角但细网格上也没有可行方向，疑似同类追迹边缘产物（不下定论）。"""

    def __init__(self, rep: tuple[int, ...], area: float, n_cells: int, count: float, wedge_deg: float) -> None:
        self.rep, self.area, self.n_cells, self.count, self.wedge_deg = rep, area, n_cells, count, wedge_deg
        self.family = family_of(wedge_deg)
        self.bucket = "grid_miss" if n_cells > 0 else ("dead_angle" if wedge_deg >= A_MAX_DEG else "infeasible")

    @property
    def label(self) -> str:
        return "-".join(map(str, self.rep))


def recheck_violations(tier: Tier, cc: A.CrosscheckResult) -> list[Recheck]:
    """每个违反项 PBD 代表在 RECHECK_STEP_DEG 细网格上从头复核并归桶；按 MC 命中合计降序。"""
    pyramid = tier_pyramid(tier)
    counts: dict[tuple[int, ...], float] = defaultdict(float)
    for r, rep in cc.violations:
        counts[rep] += r.count or 0.0
    out = []
    for rep, cnt in counts.items():
        area, n = A.fine_grid_area(pyramid, rep, step_deg=RECHECK_STEP_DEG)
        wedge = phi_class(pyramid, fold_matrix(pyramid, rep), rep[0], rep[-1]).wedge_deg
        out.append(Recheck(rep, area, n, cnt, wedge))
    out.sort(key=lambda r: -r.count)
    return out


def write_rows_csv(tier: Tier, res: A.AnalysisResult, cc: A.CrosscheckResult) -> Path:
    """MC 逐行表：原始行 + PBD 代表 + 精确楔角 / 族 + 互证状态（ok / violation / adjacent_repeat / single_face / other）。"""
    pyramid = tier_pyramid(tier)
    violating = {id(r) for r, _ in cc.violations}
    p = res.provenance
    shape = p["config"]["crystal"][0]["shape"]
    path = CACHE / f"rows_{tier_label(tier)}.csv"
    with path.open("w", newline="") as fp:
        fp.write(f"# tier={tier_label(tier)} (Lumice prism_h={shape['prism_h']} upper_h={shape['upper_h']} lower_h={shape['lower_h']}) "
                 f"roi={p['roi']} symmetry={p['symmetry']} rays={p['rays']} seed={p['seed']} max_hits={MC_MAX_LEN} "
                 f"total_rays={p['total_rays']} record_full_hits={p['record_full_hits']} "
                 f"lumice_git_head={p['lumice_git_head']} bin_sha256={p['lumice_bin_sha256'][:12]}\n")
        w = csv.writer(fp)
        w.writerow(["raypath", "pbd_rep", "wedge_deg", "family", "length", "energy_pct", "cumulative_pct", "noise_pct", "count",
                    "status"])
        for r in res.rows:
            if r.is_other:
                rep, wedge, fam, status = "", "", "", "other"
            elif len(r.faces) == 1:
                rep, wedge, fam, status = r.label, "", "", "single_face"
            elif r.has_adjacent_repeat:
                rep, wedge, fam, status = "", "", "", "adjacent_repeat"
            else:
                rep = "-".join(map(str, min(rg.pbd_orbit(r.faces))))
                cls = phi_class(pyramid, fold_matrix(pyramid, r.faces), r.faces[0], r.faces[-1])
                f = family_of(cls.wedge_deg)
                wedge, fam = f"{cls.wedge_deg:.1f}", "" if f is None else f"{f:g}"
                status = "violation" if id(r) in violating else "ok"
            w.writerow([r.label, rep, wedge, fam, len(r.faces), f"{r.energy_pct:.4f}", f"{r.cumulative_pct:.4f}",
                        "" if r.noise_pct is None else f"{r.noise_pct:.2f}",
                        "" if r.count is None else f"{r.count:.0f}", status])
    return path


# ---------- 族级互证 ----------


@dataclass
class FamilyCheck:
    """一个 (族, 档位) 的互证状态。"""

    exact_min_len: int | None        # 精确侧该族最短代表长度（不可达为 None）
    exact_area_le_mc: float          # 精确侧 ≤ MC_MAX_LEN 面的代表面积合计
    n_exact_le_mc: int               # 精确侧 ≤ MC_MAX_LEN 面的代表数
    mc: FamilyAgg | None             # MC 聚合（未命中为 None）

    @property
    def status(self) -> str:
        if self.mc is not None and self.exact_min_len is None:
            return "违反"                      # MC 命中但精确判该族不可达（任何长度）
        if self.mc is not None:
            return "命中"                      # MC 命中且精确可达（MC 行本身逐条另在光路级互证）
        if self.exact_min_len is None:
            return "—"                         # 两侧都没有
        if self.exact_min_len > MC_MAX_LEN:
            return "MC 未覆盖"                 # 精确侧只在 > MC_MAX_LEN 面出现，MC 按设计看不到
        return "MC 未见"                       # 精确侧 ≤ MC_MAX_LEN 面可达但 MC 没命中：真正的互证信号


def family_checks(exact: list[ExactRecord], fams: dict[float, FamilyAgg]) -> dict[float, FamilyCheck]:
    out = {}
    for w in KNOWN_WEDGES:
        recs = [r for r in exact if r.family == w]
        le = [r for r in recs if r.length <= MC_MAX_LEN]
        out[w] = FamilyCheck(min((r.length for r in recs), default=None), sum(r.area_sr for r in le), len(le), fams.get(w))
    return out


# ---------- energy_table.md ----------


def write_md(results: dict[Tier, A.AnalysisResult], fams: dict[Tier, dict[float, FamilyAgg]], offs: dict[Tier, FamilyAgg],
             ccs: dict[Tier, A.CrosscheckResult], exacts: dict[Tier, list[ExactRecord]], rechecks: dict[Tier, list[Recheck]],
             checks: dict[Tier, dict[float, FamilyCheck]], rays: int) -> Path:
    tiers = list(results)
    labels = [f"({ha:g}, {tr:g})" for ha, tr in tiers]
    any_prov = results[tiers[0]].provenance
    build_desc = (f"本地 build，Ice Halo 仓 HEAD `{any_prov['lumice_git_head']}`" if any_prov["local_build"]
                  else f"release `{any_prov['lumice_version']}`")
    lines = ["# 锥晶九种楔角族的蒙特卡洛能量份额表与互证（ch9，与 `signature_table.md` 同 9 行同序）", ""]
    lines.append(f"> 产出：`code/analyze_energy.py`（Lumice `analyze`，{build_desc}，"
                 f"二进制 sha256 `{any_prov['lumice_bin_sha256'][:12]}…`；`--roi {ROI} --symmetry {SYMMETRY} --rays {rays} "
                 f"--seed {SEED}`，`max_hits={MC_MAX_LEN}`，单波长 550 nm，随机朝向）；每档的 config 在 `analysis_<tier>.lumice.json`，"
                 "原始 CSV / provenance 在 `analysis/<tier>/`，MC 逐行表在 `analysis/rows_<tier>.csv`（目录 ignored，打包为 `analysis.zip` 走 LFS；"
                 "脚本会自动解包）。")
    lines.append("> 档位 (h/a, tip_ratio) 与 `signature_table.md` 同：Lumice `prism_h` = h/a ÷ 2、`upper_h` = `lower_h` = tip_ratio、锥面 Miller 指数 "
                 "`[1,0,1]`，换算在 `halo_notes.sim.config.pyramid_crystal_from_geometry`，三条都已用固定取向单光路渲染 / 判别光路实跑核实（task-pyramid-sim-glue）。")
    lines.append(f"> **MC 侧链面数上限 {MC_MAX_LEN}，精确侧 {L_STAR}**：Lumice distinct 链驻留表每 worker 16384 槽，锥晶 finest 链 `max_len=5` 就溢出"
                 f"（16385 行 + `record_full_hits` 20374@300k 光线），{MC_MAX_LEN} 面是不溢出的硬上限，比六棱柱（ch8 用 7）低得多。"
                 f"精确侧长度 {MC_MAX_LEN + 1}–{L_STAR} 的记录在互证里**只标「MC 未覆盖」不算 unseen**；族级同理——某族在某档只在长度 > {MC_MAX_LEN} 出现时，"
                 "MC 未命中它是设计使然，不是互证信号。")
    lines.append("> 能量份额 = 该族全部 finest 行的 `Energy`（占总出射能量的百分比）之和；命中数 = 各行由 `+/-` 列反推的 `(100/±)²` 之和；"
                 f"族 = 行的精确 Φ 类楔角落在 9 个已知楔角 ±{TOL:g}° 内，族外行合并成「族外」桶；相邻重复面行、单面外反射行、`other` 桶不进族表，在互证小节单列。")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append("| 档位 (h/a, tip_ratio) | " + " | ".join(labels) + " |")
    lines.append("|---|" + "---|" * len(tiers))
    lines.append("| MC 命中族数（/9） | " + " | ".join(str(len(fams[t])) for t in tiers) + " |")
    lines.append(f"| 精确可达族数（长度 ≤ {L_STAR}，`signature_table.md`） | " + " | ".join(str(sum(1 for c in checks[t].values() if c.exact_min_len is not None)) for t in tiers) + " |")
    lines.append(f"| 精确可达族数（长度 ≤ {MC_MAX_LEN}，MC 可覆盖） | " + " | ".join(str(sum(1 for c in checks[t].values() if c.n_exact_le_mc)) for t in tiers) + " |")
    lines.append("| 族级互证：违反 / MC 未见 / MC 未覆盖 | " + " | ".join(" / ".join(str(sum(1 for c in checks[t].values() if c.status == s)) for s in ("违反", "MC 未见", "MC 未覆盖")) for t in tiers) + " |")
    lines.append("| 9 族能量合计（%） | " + " | ".join(f"{sum(f.energy_pct for f in fams[t].values()):.4f}" for t in tiers) + " |")
    lines.append("| 族外能量（%）/ 族外 Φ 类数 | " + " | ".join(f"{offs[t].energy_pct:.4f} / {len(offs[t].classes)}" for t in tiers) + " |")
    lines.append("| 单面外反射能量（%） | " + " | ".join(f"{ccs[t].single_face_energy_pct:.4f}" for t in tiers) + " |")
    lines.append("| `other` 桶能量（%） | " + " | ".join(f"{ccs[t].other_energy_pct:.4f}" for t in tiers) + " |")
    lines.append("| finest 行数（含单面 / 重复面 / other） | " + " | ".join(str(len(results[t].rows)) for t in tiers) + " |")
    lines.append("| `total_rays`（出射光线段数） | " + " | ".join(str(results[t].header.total_rays) for t in tiers) + " |")
    lines.append("| `record_full_hits` | " + " | ".join(str(results[t].header.record_full_hits) for t in tiers) + " |")
    lines.append("| 光路级互证违反项（MC 命中但精确判不可达） | " + " | ".join(str(len(ccs[t].violations)) for t in tiers) + " |")
    lines.append(f"| 精确可达（≤{MC_MAX_LEN} 面）但 MC 未见 | " + " | ".join(str(len(ccs[t].unseen)) for t in tiers) + " |")
    lines.append(f"| 精确可达 {MC_MAX_LEN + 1}–{L_STAR} 面记录（MC 未覆盖） | " + " | ".join(str(len(ccs[t].uncovered)) for t in tiers) + " |")
    lines.append(f"| 最稀薄族命中数（准则 ≥ {MIN_FAMILY_COUNT}） | " + " | ".join(f"{min(f.count for f in fams[t].values()):.0f}" for t in tiers) + " |")
    lines.append("| 墙钟 (s) | " + " | ".join(f"{results[t].wall_clock_s:.0f}" for t in tiers) + " |")
    lines.append("")
    lines.append("## 主表：9 个楔角族的能量份额（%）")
    lines.append("")
    lines.append("| 楔角 | 晕 | " + " | ".join(f"能量@{lab}" for lab in labels) + " | 最亮代表（档位） |")
    lines.append("|---|---|" + "---|" * len(tiers) + "---|")
    for w in KNOWN_WEDGES:
        cells, best = [], None
        for t in tiers:
            f = fams[t].get(w)
            if f is None:
                cells.append("未覆盖" if checks[t][w].status == "MC 未覆盖" else "—")
                continue
            cells.append(f"{f.energy_pct:.4f}")
            if best is None or f.brightest.energy_pct > best[0].energy_pct:
                best = (f.brightest, t)
        rep = f"`{best[0].label}`（{labels[tiers.index(best[1])]}）" if best else "—"
        lines.append(f"| {w:g}° | {family_name(w)} | " + " | ".join(cells) + f" | {rep} |")
    lines.append("")
    lines.append("## 命中数（由 `+/-` 反推）/ Φ 类数 / PBD 代表数")
    lines.append("")
    lines.append("| 楔角 | " + " | ".join(f"@{lab}" for lab in labels) + " |")
    lines.append("|---|" + "---|" * len(tiers))
    for w in KNOWN_WEDGES:
        lines.append(f"| {w:g}° | " + " | ".join(f"{fams[t][w].count:.0f} / {len(fams[t][w].classes)} / {len(fams[t][w].reps)}" if w in fams[t] else "—" for t in tiers) + " |")
    lines.append("")
    lines.append("## 族外背景注记（真实能量口径）")
    lines.append("")
    lines.append(f"族外 = 精确楔角不在 9 个已知楔角 ±{TOL:g}° 内的 MC 行（≤{MC_MAX_LEN} 面）。explore 阶段用几何面积 / Fresnel 代理都算出"
                 "「族外面积占比 ~57%」，这里给出真实光子能量的口径，只作背景，不据此做截断裁定：")
    lines.append("")
    for t in tiers:
        o = offs[t]
        lines.append(f"- {labels[tiers.index(t)]}：族外 {len(o.classes)} 个 Φ 类、{o.n_rows} 行、能量 {o.energy_pct:.4f}%（9 族合计 "
                     f"{sum(f.energy_pct for f in fams[t].values()):.4f}%）；最亮族外行 `{o.brightest.label}`（{o.brightest.energy_pct:.4f}%）。"
                     if o.brightest else f"- {labels[tiers.index(t)]}：族外无行。")
    lines.append("")
    lines.append("## 族级互证：MC 命中 ⇒ 精确可达")
    lines.append("")
    lines.append(f"状态：**命中** = MC 有行且精确侧可达；**MC 未覆盖** = 精确侧该族最短代表长度 > {MC_MAX_LEN}（MC 按设计看不到，不是信号）；"
                 f"**MC 未见** = 精确侧 ≤{MC_MAX_LEN} 面可达但 MC 没命中（互证信号，须解释）；**违反** = MC 命中但精确侧任何长度都不可达。"
                 "格内附精确侧最短代表长度 / ≤MC 面代表数。")
    lines.append("")
    lines.append("| 楔角 | " + " | ".join(f"@{lab}" for lab in labels) + " |")
    lines.append("|---|" + "---|" * len(tiers))
    for w in KNOWN_WEDGES:
        cells = []
        for t in tiers:
            c = checks[t][w]
            cells.append(f"{c.status}（L≥{c.exact_min_len}，{c.n_exact_le_mc} 条）" if c.exact_min_len is not None else c.status)
        lines.append(f"| {w:g}° | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## 光路级互证：MC 命中集 ⊆ 精确可达集？")
    lines.append("")
    lines.append(f"判定按 PBD 代表（`min(pbd_orbit)`）对比，精确侧是 `enumerate_signatures.py` 同一次枚举（`max_len={L_STAR}`、`entry_faces=(1, 3, 13)`、"
                 "1° 网格）落盘的 `raypaths_<tier>.csv`。**违反项非空即为枚举器漏判或判据错**，本脚本不调阈值、不吞行；每个违反项另在 "
                 f"{RECHECK_STEP_DEG}° 细网格上（同一 `area_eps` / 临界角判据，`halo_notes.sim.analyze.fine_grid_area`）从头复核，三个桶："
                 "**网格漏判**（细网格可行——1° 网格把窄窗口剪掉了）；**TIR 死角**（楔角 ≥ 2·arcsin(1/n)，Snell 定律下不可能透射——追迹数值边缘产物）；"
                 "**细网格也不可行**（可透射楔角但同一判据下没有可行方向——疑似同类边缘产物，只报数不下定论）。")
    lines.append("")
    lines.append("| 档位 | 违反 finest 行 | 违反 PBD 代表 | 网格漏判 代表 / 命中 / 面积 (sr) / 所属族 | TIR 死角 代表 / 命中 / 最大单代表命中 | 细网格也不可行 代表 / 命中 / 最大单代表命中 | 违反项能量合计 (%) |")
    lines.append("|---|---|---|---|---|---|---|")
    for t in tiers:
        cc, rc = ccs[t], rechecks[t]
        gm = [r for r in rc if r.bucket == "grid_miss"]
        da = [r for r in rc if r.bucket == "dead_angle"]
        inf = [r for r in rc if r.bucket == "infeasible"]
        fam_ids = sorted({r.family for r in gm if r.family is not None})
        lines.append(f"| {labels[tiers.index(t)]} | {len(cc.violations)} | {len(rc)} | {len(gm)} / {sum(r.count for r in gm):.0f} / "
                     f"{sum(r.area for r in gm):.4f} / {', '.join(f'{f:g}°' for f in fam_ids) if fam_ids else '—'}"
                     f"{'（另族外 ' + str(sum(1 for r in gm if r.family is None)) + '）' if any(r.family is None for r in gm) else ''} | "
                     f"{len(da)} / {sum(r.count for r in da):.0f} / {max((r.count for r in da), default=0):.0f} | "
                     f"{len(inf)} / {sum(r.count for r in inf):.0f} / {max((r.count for r in inf), default=0):.0f} | "
                     f"{sum(r.energy_pct for r, _ in cc.violations):.4f} |")
    lines.append("")
    for t in tiers:
        cc, res, rc = ccs[t], results[t], rechecks[t]
        exact = exacts[t]
        n_exact = sum(1 for r in exact if r.length > 1)
        n_le = sum(1 for r in exact if 1 < r.length <= MC_MAX_LEN)
        gm = [r for r in rc if r.bucket == "grid_miss"]
        da = [r for r in rc if r.bucket == "dead_angle"]
        inf = [r for r in rc if r.bucket == "infeasible"]
        verdict = "**通过**" if cc.ok else f"**违反 {len(rc)} 个代表（{len(cc.violations)} 行）：网格漏判 {len(gm)}、TIR 死角 {len(da)}、细网格也不可行 {len(inf)}**"
        lines.append(f"### {labels[tiers.index(t)]}：{verdict}")
        lines.append("")
        lines.append(f"- MC 可用行（非 other、长度 > 1、无相邻重复面）{len(A.usable_rows(res.rows))} 条 → PBD 代表 {len(cc.seen) + len(rc)} 个，"
                     f"其中 {len(cc.seen)} 个落在精确可达集（{n_exact} 条代表，其中 ≤{MC_MAX_LEN} 面 {n_le} 条）内"
                     + ("" if cc.ok else f"，{len(rc)} 个不在"))
        if gm:
            lines.append(f"- 网格漏判 {len(gm)} 个代表（MC 命中合计 {sum(r.count for r in gm):.0f}，{RECHECK_STEP_DEG}° 细网格面积合计 "
                         f"{sum(r.area for r in gm):.4f} sr）：")
            for r in gm:
                fam = f"{r.family:g}° 族" if r.family is not None else "族外"
                lines.append(f"  - `{r.label}`（楔角 {r.wedge_deg:.1f}°，{fam}）：MC 命中 {r.count:.0f}；细网格可行 {r.n_cells} 格、面积 {r.area:.2e} sr")
        if da:
            lines.append(f"- TIR 死角 {len(da)} 个代表（MC 命中合计 {sum(r.count for r in da):.0f}，单代表最多 {max(r.count for r in da):.0f}）："
                         + "、".join(f"`{r.label}`({r.wedge_deg:.1f}°;{r.count:.0f})" for r in da))
        if inf:
            lines.append(f"- 细网格也不可行 {len(inf)} 个代表（MC 命中合计 {sum(r.count for r in inf):.0f}，单代表最多 {max(r.count for r in inf):.0f}）："
                         + "、".join(f"`{r.label}`({r.wedge_deg:.1f}°;{r.count:.0f})" for r in inf))
        lines.append(f"- 精确可达（≤{MC_MAX_LEN} 面）但 MC 未见：{len(cc.unseen)} 条"
                     + (f"，面积最大的前 10 条（sr）：" + "、".join(f"`{rec.label}` {rec.area_sr:.4f}" for rec in cc.unseen[:10])
                        + f"；未见集合面积合计 {sum(rec.area_sr for rec in cc.unseen):.4f} sr，最大 {cc.unseen[0].area_sr:.4f} sr"
                        if cc.unseen else "")
                     + f"；精确可达 {MC_MAX_LEN + 1}–{L_STAR} 面记录（MC 未覆盖）{len(cc.uncovered)} 条")
        lines.append(f"- 剔除的相邻重复面行：{len(cc.dropped_adjacent_repeat)} 条，合计能量 {cc.dropped_energy_pct:.4f}%"
                     + ("（如 " + "、".join(f"`{r.label}`" for r in cc.dropped_adjacent_repeat[:5]) + "）" if cc.dropped_adjacent_repeat else "")
                     + f"；单面外反射行能量 {cc.single_face_energy_pct:.4f}%；`other` 桶能量 {cc.other_energy_pct:.4f}%")
        if res.header.record_full_hits:
            lines.append(f"- ⚠ `record_full_hits = {res.header.record_full_hits}`：distinct 链驻留表曾满，`other` 桶里有未列出的链，"
                         "上面的 unseen 集合可能不完整（只能说「未记录」，不能说「未命中」）")
        else:
            lines.append("- `record_full_hits = 0`：本档无驻留表溢出，unseen 集合完整")
        lines.append("")
    lines.append("## 面积 vs 能量：族级秩相关")
    lines.append("")
    lines.append(f"对每档，取 9 族在精确侧 ≤{MC_MAX_LEN} 面代表的可行方向面积合计（`raypaths_<tier>.csv`）与其 MC 能量份额算 Spearman ρ（n = 9，"
                 "定性核验「可行方向面积是权重骨架」——Fresnel、截面、TIR 都在面积之外；样本只有 9 个族，不做定量解读）。")
    lines.append("")
    lines.append("| 档位 | " + " | ".join(labels) + " |")
    lines.append("|---|" + "---|" * len(tiers))
    rhos = []
    for t in tiers:
        x = [checks[t][w].exact_area_le_mc for w in KNOWN_WEDGES]
        y = [fams[t][w].energy_pct if w in fams[t] else 0.0 for w in KNOWN_WEDGES]
        rhos.append(A.spearman_rho(x, y))
    lines.append("| Spearman ρ | " + " | ".join(f"{r:.3f}" for r in rhos) + " |")
    lines.append("")
    path = DATA / "energy_table.md"
    path.write_text("\n".join(lines))
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rays", type=int, default=RAYS, help=f"每档 --rays（默认 {RAYS}，止损 {RAYS_CAP}）")
    ap.add_argument("--tiers", nargs="*", default=[tier_label(t) for t in TIERS],
                    help="只跑这些档位（`h<h/a>_t<tip_ratio>`，调试用；正式产出须全部档位）")
    ap.add_argument("--reuse", action="store_true", help="data/analysis/<tier>/ 已有同参数产物时不重跑 Lumice")
    args = ap.parse_args(argv)
    if args.rays > RAYS_CAP:
        print(f"⚠ --rays {args.rays} 超过止损 {RAYS_CAP}", file=sys.stderr)
    by_label = {tier_label(t): t for t in TIERS}
    tiers = [by_label[x] for x in args.tiers]
    DATA.mkdir(exist_ok=True)
    ensure_unpacked()
    CACHE.mkdir(exist_ok=True)
    results: dict[Tier, A.AnalysisResult] = {}
    fams: dict[Tier, dict[float, FamilyAgg]] = {}
    offs: dict[Tier, FamilyAgg] = {}
    ccs: dict[Tier, A.CrosscheckResult] = {}
    exacts: dict[Tier, list[ExactRecord]] = {}
    rechecks: dict[Tier, list[Recheck]] = {}
    checks: dict[Tier, dict[float, FamilyCheck]] = {}
    warnings: list[str] = []
    for tier in tiers:
        res = run_one(tier, args.rays, args.reuse)
        agg = A.classify_rows(tier_pyramid(tier), res.rows)
        fams[tier], offs[tier] = aggregate_families(agg)
        exacts[tier] = exact = exact_records(tier)
        ccs[tier] = cc = A.crosscheck(res.rows, exact, mc_max_len=MC_MAX_LEN)
        checks[tier] = fc = family_checks(exact, fams[tier])
        results[tier] = res
        thin_w = min(fams[tier], key=lambda w: fams[tier][w].count)
        thin = fams[tier][thin_w].count
        print(f"  族 {len(fams[tier])}/9（族级：" + "，".join(f"{w:g}° {fc[w].status}" for w in KNOWN_WEDGES if fc[w].status != "命中")
              + f"），族外 {len(offs[tier].classes)} 类 / {offs[tier].energy_pct:.4f}%，违反 {len(cc.violations)}，unseen {len(cc.unseen)}，"
              f"uncovered {len(cc.uncovered)}，重复面行 {len(cc.dropped_adjacent_repeat)}，other {cc.other_energy_pct:.4f}%，"
              f"最稀薄族 {thin_w:g}° 命中 {thin:.0f}")
        rechecks[tier] = recheck_violations(tier, cc)
        for r in rechecks[tier]:
            print(f"  ✗ 违反：{r.label}（楔角 {r.wedge_deg:.1f}°，MC 命中 {r.count:.0f}）→ {r.bucket}"
                  + (f"：{RECHECK_STEP_DEG}° 细网格可行 {r.n_cells} 格、{r.area:.2e} sr" if r.n_cells else ""))
        if thin < MIN_FAMILY_COUNT:
            warnings.append(f"{tier_label(tier)}：最稀薄族 {thin_w:g}° 命中 {thin:.0f} < {MIN_FAMILY_COUNT}，--rays 不够")
        for w in KNOWN_WEDGES:
            if fc[w].status in ("违反", "MC 未见"):
                warnings.append(f"{tier_label(tier)}：{w:g}° 族级互证 {fc[w].status}")
        print("  →", write_rows_csv(tier, res, cc).name)
    if set(tiers) == set(TIERS):
        print("  →", write_md(results, fams, offs, ccs, exacts, rechecks, checks, args.rays).name)
        print("  →", pack().name, f"({ZIP.stat().st_size / 1e6:.2f} MB)")
    else:
        print("  （未跑全部档位，不写 energy_table.md）")
    for w in warnings:
        print("⚠", w, file=sys.stderr)
    n_viol = sum(len(cc.violations) for cc in ccs.values())
    buckets: dict[str, int] = defaultdict(int)
    for rc in rechecks.values():
        for r in rc:
            buckets[r.bucket] += 1
    n_reps = sum(len(rc) for rc in rechecks.values())
    print(f"光路级互证：{'全部通过' if n_viol == 0 else f'共 {n_viol} 行 / {n_reps} 个代表违反：' + '，'.join(f'{k} {v}' for k, v in sorted(buckets.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
