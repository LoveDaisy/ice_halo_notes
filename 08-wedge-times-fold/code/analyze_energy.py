# 产出 ../data/energy_table.md（34 个 Φ 类的蒙特卡洛能量份额表 + 与精确枚举的互证结论，入 git）与 ../data/analysis/
# （每档 h/a 的原始 CSV / lumice.log / provenance.json 落 analysis/<ha>/，MC 逐行表落 analysis/rows_<ha>.csv：面序列 →
# PBD 代表 → Φ 类，附互证状态；共 ~7 MB 文本，目录与 ../data/analysis.zip（打包缓存）都只留本地、不入 git（见 AGENTS.md「数据约定」）；
# 本脚本启动时若本地没有 analysis/ 而有 analysis.zip 就自动解包，跑完全五档后重新打包）：对 h/a ∈ {0.2, 0.5, 1, 2, 5}（与 enumerate_signatures.py
# 同一组常量）用 Lumice 4.6.x `analyze` 子命令跑随机朝向六棱柱、全天 ROI、`--symmetry none`（归并在 python 侧按 Φ 类做），
# 再与 enumerate_signatures.py 同一调用的精确枚举对表：MC 命中集 ⊆ 精确可达集（a01 独立证据链）。
#
# 口径：
# - Lumice `analyze` 子命令（release ≥ v4.6.1，`halo_notes.sim.fetch.ensure_lumice` 自动取；现存 `data/` 产物由 4.6.1 发版前的
#   本地 build 跑出，provenance 已记），config 落 data/analysis_<ha>.lumice.json（入 git），原始 CSV /
#   lumice.log / provenance.json 落 data/analysis/<ha>/（ignored，见上）；h/a 经 halo_notes.sim.config.hex_prism_height_ratio 换算（Lumice 的 a
#   是底面直径 = 2×边长）；
# - MC 侧链面数上限 MC_MAX_LEN = 7 < 精确侧 MAX_LEN = 8：Lumice distinct 链驻留表每 worker 只有 16384 槽（seeded run 单
#   worker），而 h/a=1 的精确可达集展开成 finest 序列后 ≤7 面 13688 条、≤8 面 29212 条——8 面必然溢出进 other 桶、`unseen`
#   无从判定；7 面全集可完整驻留，8 面链能量份额仅 ~0.7%（探针实测）。精确侧长度 8 的记录在互证里标「MC 未覆盖」；
# - 相邻重复面链（凸多面体上不可能，追迹数值边缘产物）整行剔除并计数上报；单面外反射行（`1`、`2`……）不在 34 类框架内，
#   只报能量份额；`other (not recorded)` 桶原样带到表尾；
# - `--rays` 量级准则：每档跑完用 ± 反推 34 类里最稀薄类的命中数，须 ≥ MIN_CLASS_COUNT，否则本脚本报警（不静默）。
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from enumerate_signatures import ENTRY_FACES, GRID, MAX_LEN, RATIOS, ha_label
from lumice_integral.geometry import HexPrism, fold_matrix
from lumice_integral.geometry.enumerate import RaypathRecord, enumerate_raypaths
from lumice_integral.symmetry import reflection_group as rg
from lumice_integral.symmetry.signature import PhiRow, phi_class, phi_class_table
from halo_notes.sim import analyze as A

DATA = Path(__file__).resolve().parent.parent / "data"
CACHE = DATA / "analysis"      # 大体积文本产物（只留本地）；另打包为 ZIP 缓存（同样只留本地）
ZIP = DATA / "analysis.zip"
MC_MAX_LEN = 7                 # 见文件头：16384 槽驻留表 ⇒ finest 全集只在 ≤7 面时放得下
RAYS = 50_000_000
SEED = 7
ROI = "sky"
SYMMETRY = "none"
MIN_CLASS_COUNT = 20           # `--rays` 量级准则：34 类里最稀薄类的命中数下限
RECHECK_STEP_DEG = 0.2         # 违反项归因：细网格复核的格距（枚举器用 2°）


def ensure_unpacked() -> None:
    """本地没有 data/analysis/ 而有 analysis.zip（本地打包缓存）时解包，让 --reuse 与读表脚本拿到文本文件。"""
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


def exact_area_by_class(ratio: float) -> dict[str, float]:
    """`signature_table_<ha>.csv` 里每个 Φ 类的可行方向面积之和（42 类粒度按 phi_class_id 汇总）。"""
    out: dict[str, float] = defaultdict(float)
    with (DATA / f"signature_table_{ha_label(ratio)}.csv").open() as fp:
        for row in csv.DictReader(fp):
            out[row["phi_class_id"]] += float(row["area_sr_sum"])
    return dict(out)


def run_one(ratio: float, rays: int, reuse: bool) -> A.AnalysisResult:
    stem = f"analysis_{ha_label(ratio)}"
    out_dir = CACHE / ha_label(ratio)
    cfg = A.analysis_config(ratio, max_len=MC_MAX_LEN, rays=rays)
    if reuse and (out_dir / "provenance.json").exists():
        res = A.load_analysis(out_dir)
        p = res.provenance
        if p["config"] == cfg and p["rays"] == rays and p["seed"] == SEED and p["roi"] == ROI and p["symmetry"] == SYMMETRY:
            print(f"h/a={ratio:g}: 复用 {out_dir.name}/（{p['n_rows']} 行，{p['wall_clock_s']} s）")
            return res
        print(f"h/a={ratio:g}: 已有产物参数不符，重跑")
    (DATA / f"{stem}.lumice.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    res = A.run_analysis(cfg, out_dir, roi=ROI, symmetry=SYMMETRY, rays=rays, seed=SEED)
    print(f"h/a={ratio:g}: {len(res.rows)} 行，total_rays={res.header.total_rays}，record_full_hits="
          f"{res.header.record_full_hits}，{res.wall_clock_s:.1f} s")
    return res


def exact_records(ratio: float) -> list[RaypathRecord]:
    """与 enumerate_signatures.classify() 完全相同的枚举调用（同 crystal / MAX_LEN / GRID / entry_faces / PBD 去重）。"""
    return enumerate_raypaths(HexPrism.from_ratio(ratio), MAX_LEN, GRID, entry_faces=ENTRY_FACES, symmetry_orbit=rg.pbd_orbit)


class Recheck:
    """一个违反项 PBD 代表的归因：细网格可行面积 / 格数、MC 命中合计、所属 Φ 类、归类桶。

    桶（bucket）三选一：``grid_miss``——细网格可行，枚举器 2° 网格漏判的窄窗口（回抛子任务 2 的真信号）；
    ``dead_angle``——所属 Φ 类楔角 ≥ 2·arcsin(1/n)（A120 / A180，Snell 定律下不可能透射），追迹数值边缘产物；
    ``infeasible``——可透射类但细网格上也没有可行方向，几何 + 光学判据下不存在，疑似同类追迹边缘产物（本脚本不下定论）。"""

    def __init__(self, rep: tuple[int, ...], area: float, n_cells: int, count: float, row: PhiRow) -> None:
        self.rep, self.area, self.n_cells, self.count, self.row = rep, area, n_cells, count, row
        self.bucket = "grid_miss" if n_cells > 0 else ("dead_angle" if not row.transmittable else "infeasible")

    @property
    def label(self) -> str:
        return "-".join(map(str, self.rep))


def recheck_violations(ratio: float, cc: A.CrosscheckResult, rows: tuple[PhiRow, ...]) -> list[Recheck]:
    """每个违反项 PBD 代表在 RECHECK_STEP_DEG 细网格上从头复核并归桶；按 MC 命中合计降序。"""
    crystal = HexPrism.from_ratio(ratio)
    by_cls = {r.phi_class: r for r in rows}
    counts: dict[tuple[int, ...], float] = defaultdict(float)
    for r, rep in cc.violations:
        counts[rep] += r.count or 0.0
    out = []
    for rep, cnt in counts.items():
        area, n = A.fine_grid_area(crystal, rep, step_deg=RECHECK_STEP_DEG)
        out.append(Recheck(rep, area, n, cnt, by_cls[phi_class(crystal, fold_matrix(crystal, rep), rep[0], rep[-1])]))
    out.sort(key=lambda r: -r.count)
    return out


def write_rows_csv(ratio: float, res: A.AnalysisResult, cc: A.CrosscheckResult, by_cls: dict) -> Path:
    """MC 逐行表：原始行 + PBD 代表 + Φ 类 + 互证状态（ok / violation / adjacent_repeat / single_face / other）。"""
    crystal = HexPrism.from_ratio(ratio)
    violating = {id(r) for r, _ in cc.violations}
    p = res.provenance
    path = CACHE / f"rows_{ha_label(ratio)}.csv"
    with path.open("w", newline="") as fp:
        fp.write(f"# h/a={ratio:g} (Lumice height={p['config']['crystal'][0]['shape']['height']}) roi={p['roi']} "
                 f"symmetry={p['symmetry']} rays={p['rays']} seed={p['seed']} max_hits={MC_MAX_LEN} "
                 f"total_rays={p['total_rays']} record_full_hits={p['record_full_hits']} "
                 f"lumice_git_head={p['lumice_git_head']} bin_sha256={p['lumice_bin_sha256'][:12]}\n")
        w = csv.writer(fp)
        w.writerow(["raypath", "pbd_rep", "phi_class_id", "length", "energy_pct", "cumulative_pct", "noise_pct", "count",
                    "status"])
        for r in res.rows:
            if r.is_other:
                rep, cid, status = "", "", "other"
            elif len(r.faces) == 1:
                rep, cid, status = r.label, "", "single_face"
            elif r.has_adjacent_repeat:
                rep, cid, status = "", "", "adjacent_repeat"
            else:
                rep = "-".join(map(str, min(rg.pbd_orbit(r.faces))))
                cid = by_cls[phi_class(crystal, fold_matrix(crystal, r.faces), r.faces[0], r.faces[-1])].id
                status = "violation" if id(r) in violating else "ok"
            w.writerow([r.label, rep, cid, len(r.faces), f"{r.energy_pct:.4f}", f"{r.cumulative_pct:.4f}",
                        "" if r.noise_pct is None else f"{r.noise_pct:.2f}",
                        "" if r.count is None else f"{r.count:.0f}", status])
    return path


def write_md(rows: tuple[PhiRow, ...], results: dict[float, A.AnalysisResult], aggs: dict[float, dict],
             ccs: dict[float, A.CrosscheckResult], areas: dict[float, dict[str, float]], exacts: dict[float, list[RaypathRecord]],
             rechecks: dict[float, list[Recheck]], rays: int) -> Path:
    live = [r for r in rows if r.transmittable]
    by_id = {r.id: r for r in live}
    agg_by_id = {ratio: {row.id: aggs[ratio][row.phi_class] for row in live if row.phi_class in aggs[ratio]}
                 for ratio in RATIOS}
    any_prov = results[RATIOS[0]].provenance
    build_desc = (f"本地 build，Ice Halo 仓 HEAD `{any_prov['lumice_git_head']}`" if any_prov["local_build"]
                  else f"release `{any_prov['lumice_version']}`")
    lines = ["# 六棱柱 Φ 类的蒙特卡洛能量份额表与互证（ch8，与 `signature_table.md` 同 34 行同序）", ""]
    lines.append(f"> 产出：`code/analyze_energy.py`（Lumice `analyze`，{build_desc}，"
                 f"二进制 sha256 `{any_prov['lumice_bin_sha256'][:12]}…`；`--roi {ROI} --symmetry {SYMMETRY} --rays {rays} "
                 f"--seed {SEED}`，`max_hits={MC_MAX_LEN}`，单波长 550 nm，随机朝向）；每档 h/a 的 config 在 "
                 f"`analysis_<ha>.lumice.json`，原始 CSV / provenance 在 `analysis/<ha>/`，MC 逐行表在 `analysis/rows_<ha>.csv`（目录 ignored，只留本地（打包缓存 `analysis.zip`）；脚本会自动解包）。")
    lines.append("> h/a 是本仓 `HexPrism` 口径（a = 六边形边长）；Lumice `height` = h/a ÷ 2（它的 a 是底面顶点对角线直径），"
                 "换算在 `halo_notes.sim.config.hex_prism_height_ratio`，方向已用判别光路实跑核实。")
    lines.append(f"> MC 侧链面数上限 {MC_MAX_LEN}（精确侧 {MAX_LEN}）：Lumice distinct 链驻留表每 worker 16384 槽，"
                 "8 面的 finest 全集放不下（h/a=1 为 29212 条）；8 面链能量份额约 0.7%，能量表因此少这一截，精确侧长度 8 的记录在互证里"
                 "只标「MC 未覆盖」不算 unseen。")
    lines.append("> 能量份额 = 该类全部 finest 行的 `Energy`（占总出射能量的百分比）之和；命中数 = 各行由 `+/-` 列反推的 "
                 "`(100/±)²` 之和；相邻重复面行、单面外反射行、`other` 桶不进类表，在互证小节单列。")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append("| h/a | " + " | ".join(ha_label(r) for r in RATIOS) + " |")
    lines.append("|---|" + "---|" * len(RATIOS))
    lines.append("| MC 命中 Φ 类数（/34） | " + " | ".join(str(len(agg_by_id[r])) for r in RATIOS) + " |")
    lines.append("| 精确可达 Φ 类数（`signature_table.md`） | " + " | ".join(str(len(areas[r])) for r in RATIOS) + " |")
    lines.append("| finest 行数（含单面 / 重复面 / other） | " + " | ".join(str(len(results[r].rows)) for r in RATIOS) + " |")
    lines.append("| `total_rays`（出射光线段数） | " + " | ".join(str(results[r].header.total_rays) for r in RATIOS) + " |")
    lines.append("| `record_full_hits` | " + " | ".join(str(results[r].header.record_full_hits) for r in RATIOS) + " |")
    lines.append("| 互证违反项（MC 命中但精确判不可达） | " + " | ".join(str(len(ccs[r].violations)) for r in RATIOS) + " |")
    lines.append("| 精确可达（≤7 面）但 MC 未见 | " + " | ".join(str(len(ccs[r].unseen)) for r in RATIOS) + " |")
    lines.append("| 精确可达 8 面记录（MC 未覆盖） | " + " | ".join(str(len(ccs[r].uncovered)) for r in RATIOS) + " |")
    lines.append("| 最稀薄类命中数（34 类内，准则 ≥ %d） | " % MIN_CLASS_COUNT
                 + " | ".join(f"{min(a.count for a in agg_by_id[r].values()):.0f}" for r in RATIOS) + " |")
    dead = {r: [(row, aggs[r][row.phi_class]) for row in rows if not row.transmittable and row.phi_class in aggs[r]] for r in RATIOS}
    lines.append("| 落入 TIR 死角类（A120/A180）的行数 / 命中 | "
                 + " | ".join(f"{sum(a.n_rows for _, a in dead[r])} / {sum(a.count for _, a in dead[r]):.0f}" for r in RATIOS) + " |")
    lines.append("| 墙钟 (s) | " + " | ".join(f"{results[r].wall_clock_s:.0f}" for r in RATIOS) + " |")
    lines.append("")
    lines.append("## 主表：34 个 Φ 类的能量份额（%）")
    lines.append("")
    lines.append("| 类 | 楔角 | 族 | " + " | ".join(f"能量@{ha_label(r)}" for r in RATIOS) + " | 最亮代表（h/a） |")
    lines.append("|---|---|---|" + "---|" * len(RATIOS) + "---|")
    for row in live:
        cells = []
        best = None
        for ratio in RATIOS:
            a = agg_by_id[ratio].get(row.id)
            if a is None:
                cells.append("—")
                continue
            cells.append(f"{a.energy_pct:.4f}")
            if best is None or a.brightest.energy_pct > best[0].energy_pct:
                best = (a.brightest, ratio)
        rep = f"`{best[0].label}`（{ha_label(best[1])}）" if best else "—"
        lines.append(f"| {row.id} | {row.wedge_deg:g}° | {row.family} | " + " | ".join(cells) + f" | {rep} |")
    lines.append("")
    lines.append("## 命中数（由 `+/-` 反推）与 PBD 代表数")
    lines.append("")
    lines.append("| 类 | " + " | ".join(f"命中@{ha_label(r)}" for r in RATIOS) + " | " + " | ".join(f"代表@{ha_label(r)}" for r in RATIOS) + " |")
    lines.append("|---|" + "---|" * (2 * len(RATIOS)))
    for row in live:
        counts = [f"{agg_by_id[r][row.id].count:.0f}" if row.id in agg_by_id[r] else "—" for r in RATIOS]
        reps = [str(len(agg_by_id[r][row.id].reps)) if row.id in agg_by_id[r] else "—" for r in RATIOS]
        lines.append(f"| {row.id} | " + " | ".join(counts) + " | " + " | ".join(reps) + " |")
    lines.append("")
    lines.append("## 互证结论：MC 命中集 ⊆ 精确可达集？")
    lines.append("")
    lines.append("判定按 PBD 代表（`min(pbd_orbit)`）对比，精确侧是 `enumerate_signatures.py` 同一调用（`max_len=8`、`entry_faces=(1, 3)`、"
                 "`LatLonGrid(180, 360)`）的记录。**违反项非空即为枚举器漏判或判据错**，本脚本不调阈值、不吞行；每个违反项另在 "
                 f"{RECHECK_STEP_DEG}° 细网格上（同一 `area_eps` / 临界角判据，`halo_notes.sim.analyze.fine_grid_area`）从头复核："
                 "细网格可行 ⇒ 2° 网格分辨率漏判（窗口窄于格距，DFS 在粗网格上被剪掉）；细网格也不可行 ⇒ 另一类问题，须单独归因。")
    lines.append("")
    lines.append("")
    lines.append("三个桶：**网格漏判**（细网格可行——枚举器在 2° 网格上把窄窗口剪掉了，是回抛给枚举器任务的真信号）；**TIR 死角类**"
                 "（所属 Φ 类楔角 ≥ 2·arcsin(1/n)，A120 / A180，Snell 定律下不可能透射——只能是追迹数值边缘产物，与相邻重复面链同类）；"
                 "**细网格也不可行**（可透射类，但同一几何 + 光学判据下没有可行方向——疑似同类追迹边缘产物，本表只报数不下定论）。")
    lines.append("")
    lines.append("| h/a | 违反 finest 行 | 违反 PBD 代表 | 网格漏判 代表 / 命中 / 面积 (sr) / 所属类 | TIR 死角类 代表 / 命中 / 最大单代表命中 | 细网格也不可行 代表 / 命中 / 最大单代表命中 | 违反项能量合计 (%) |")
    lines.append("|---|---|---|---|---|---|---|")
    for ratio in RATIOS:
        cc, rc = ccs[ratio], rechecks[ratio]
        gm = [r for r in rc if r.bucket == "grid_miss"]
        da = [r for r in rc if r.bucket == "dead_angle"]
        inf = [r for r in rc if r.bucket == "infeasible"]
        cls_ids = sorted({r.row.id for r in gm})
        lines.append(f"| {ha_label(ratio)} | {len(cc.violations)} | {len(rc)} | {len(gm)} / {sum(r.count for r in gm):.0f} / "
                     f"{sum(r.area for r in gm):.4f} / {', '.join(cls_ids) if cls_ids else '—'} | "
                     f"{len(da)} / {sum(r.count for r in da):.0f} / {max((r.count for r in da), default=0):.0f} | "
                     f"{len(inf)} / {sum(r.count for r in inf):.0f} / {max((r.count for r in inf), default=0):.0f} | "
                     f"{sum(r.energy_pct for r, _ in cc.violations):.4f} |")
    lines.append("")
    for ratio in RATIOS:
        cc = ccs[ratio]
        res = results[ratio]
        n_exact = sum(1 for rec in exacts[ratio] if rec.length > 1)
        n_le = sum(1 for rec in exacts[ratio] if 1 < rec.length <= MC_MAX_LEN)
        rc = rechecks[ratio]
        gm = [r for r in rc if r.bucket == "grid_miss"]
        da = [r for r in rc if r.bucket == "dead_angle"]
        inf = [r for r in rc if r.bucket == "infeasible"]
        verdict = "**通过**" if cc.ok else f"**违反 {len(rc)} 个代表（{len(cc.violations)} 行）：网格漏判 {len(gm)}、TIR 死角类 {len(da)}、细网格也不可行 {len(inf)}**"
        lines.append(f"### h/a = {ha_label(ratio)}：{verdict}")
        lines.append("")
        lines.append(f"- MC 可用行（非 other、长度 > 1、无相邻重复面）{len(A.usable_rows(res.rows))} 条 → PBD 代表 {len(cc.seen) + len(rc)} 个，"
                     f"其中 {len(cc.seen)} 个落在精确可达集（{n_exact} 条代表，其中 ≤{MC_MAX_LEN} 面 {n_le} 条）内"
                     + ("" if cc.ok else f"，{len(rc)} 个不在"))
        if gm:
            lines.append(f"- 网格漏判 {len(gm)} 个代表（MC 命中合计 {sum(r.count for r in gm):.0f}，{RECHECK_STEP_DEG}° 细网格面积合计 "
                         f"{sum(r.area for r in gm):.4f} sr；所属类均已在该档精确可达集内，类级结论不变）：")
            for r in gm:
                lines.append(f"  - `{r.label}`（{r.row.id}）：MC 命中 {r.count:.0f}；细网格可行 {r.n_cells} 格、面积 {r.area:.2e} sr")
        if da:
            lines.append(f"- TIR 死角类 {len(da)} 个代表（MC 命中合计 {sum(r.count for r in da):.0f}，单代表最多 {max(r.count for r in da):.0f}）："
                         + "、".join(f"`{r.label}`({r.row.id};{r.count:.0f})" for r in da))
        if inf:
            lines.append(f"- 细网格也不可行 {len(inf)} 个代表（MC 命中合计 {sum(r.count for r in inf):.0f}，单代表最多 {max(r.count for r in inf):.0f}）："
                         + "、".join(f"`{r.label}`({r.row.id};{r.count:.0f})" for r in inf))
        lines.append(f"- 精确可达（≤{MC_MAX_LEN} 面）但 MC 未见：{len(cc.unseen)} 条"
                     + (f"，面积最大的前 10 条（sr）：" + "、".join(f"`{rec.label}` {rec.area_sr:.4f}" for rec in cc.unseen[:10])
                        + f"；未见集合面积合计 {sum(rec.area_sr for rec in cc.unseen):.4f} sr，最大 {cc.unseen[0].area_sr:.4f} sr"
                        if cc.unseen else "")
                     + "；精确可达 8 面记录（MC 未覆盖）" + str(len(cc.uncovered)) + " 条")
        lines.append(f"- 剔除的相邻重复面行：{len(cc.dropped_adjacent_repeat)} 条，合计能量 {cc.dropped_energy_pct:.4f}%"
                     + ("（如 " + "、".join(f"`{r.label}`" for r in cc.dropped_adjacent_repeat[:5]) + "）" if cc.dropped_adjacent_repeat else "")
                     + f"；单面外反射行能量 {cc.single_face_energy_pct:.4f}%；`other` 桶能量 {cc.other_energy_pct:.4f}%")
        if res.header.record_full_hits:
            lines.append(f"- ⚠ `record_full_hits = {res.header.record_full_hits}`：distinct 链驻留表曾满，`other` 桶里有未列出的链，"
                         "上面的 unseen 集合可能不完整（只能说「未记录」，不能说「未命中」）")
        else:
            lines.append("- `record_full_hits = 0`：本档无驻留表溢出，unseen 集合完整")
        lines.append("")
    lines.append("## 面积 vs 能量：秩相关")
    lines.append("")
    lines.append("对每档 h/a，取精确可达的 Φ 类（`signature_table_<ha>.csv` 的 `area_sr_sum` 按类汇总）与其 MC 能量份额算 Spearman ρ"
                 "（定性核验「可行方向面积是权重骨架」，不做定量拟合——Fresnel、截面、TIR 都在面积之外）。")
    lines.append("")
    lines.append("| h/a | " + " | ".join(ha_label(r) for r in RATIOS) + " |")
    lines.append("|---|" + "---|" * len(RATIOS))
    rhos = []
    ns = []
    for ratio in RATIOS:
        ids = sorted(areas[ratio])
        x = [areas[ratio][i] for i in ids]
        y = [agg_by_id[ratio][i].energy_pct if i in agg_by_id[ratio] else 0.0 for i in ids]
        rhos.append(A.spearman_rho(x, y))
        ns.append(len(ids))
    lines.append("| Spearman ρ | " + " | ".join(f"{r:.3f}" for r in rhos) + " |")
    lines.append("| n（精确可达类数） | " + " | ".join(map(str, ns)) + " |")
    lines.append("")
    path = DATA / "energy_table.md"
    path.write_text("\n".join(lines))
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rays", type=int, default=RAYS, help=f"每档 --rays（默认 {RAYS}）")
    ap.add_argument("--ratios", type=float, nargs="*", default=list(RATIOS), help="只跑这些 h/a（调试用；正式产出须全五档）")
    ap.add_argument("--reuse", action="store_true", help="data/analysis/<ha>/ 已有同参数产物时不重跑 Lumice")
    args = ap.parse_args(argv)
    DATA.mkdir(exist_ok=True)
    ensure_unpacked()
    CACHE.mkdir(exist_ok=True)
    rows = phi_class_table(HexPrism.from_ratio(RATIOS[0]))
    assert sum(r.transmittable for r in rows) == 34
    by_cls = {r.phi_class: r for r in rows}
    results: dict[float, A.AnalysisResult] = {}
    aggs: dict[float, dict] = {}
    ccs: dict[float, A.CrosscheckResult] = {}
    areas: dict[float, dict[str, float]] = {}
    exacts: dict[float, list[RaypathRecord]] = {}
    rechecks: dict[float, dict] = {}
    warnings: list[str] = []
    for ratio in args.ratios:
        res = run_one(ratio, args.rays, args.reuse)
        crystal = HexPrism.from_ratio(ratio)
        agg = A.classify_rows(crystal, res.rows)
        exact = exact_records(ratio)
        cc = A.crosscheck(res.rows, exact, mc_max_len=MC_MAX_LEN)
        results[ratio], aggs[ratio], ccs[ratio], exacts[ratio] = res, agg, cc, exact
        areas[ratio] = exact_area_by_class(ratio)
        live_agg = {c: a for c, a in agg.items() if by_cls[c].transmittable}
        thin = min(live_agg.values(), key=lambda a: a.count)
        thin_id = by_cls[next(c for c, a in live_agg.items() if a is thin)].id
        print(f"  Φ 类 {len(live_agg)}/34（另 {len(agg) - len(live_agg)} 个 TIR 死角类有行），违反 {len(cc.violations)}，unseen {len(cc.unseen)}，uncovered {len(cc.uncovered)}，"
              f"重复面行 {len(cc.dropped_adjacent_repeat)}，other {cc.other_energy_pct:.4f}%，最稀薄类 {thin_id} 命中 {thin.count:.0f}")
        rechecks[ratio] = recheck_violations(ratio, cc, rows)
        for r in rechecks[ratio]:
            print(f"  ✗ 违反：{r.label}（{r.row.id}，MC 命中 {r.count:.0f}）→ {r.bucket}"
                  + (f"：{RECHECK_STEP_DEG}° 细网格可行 {r.n_cells} 格、{r.area:.2e} sr" if r.n_cells else ""))
        if thin.count < MIN_CLASS_COUNT:
            warnings.append(f"h/a={ratio:g}：最稀薄类 {thin_id} 命中 {thin.count:.0f} < {MIN_CLASS_COUNT}，--rays 不够")
        print("  →", write_rows_csv(ratio, res, cc, by_cls).name)
    if set(args.ratios) == set(RATIOS):
        print("  →", write_md(rows, results, aggs, ccs, areas, exacts, rechecks, args.rays).name)
        print("  →", pack().name, f"({ZIP.stat().st_size / 1e6:.2f} MB)")
    else:
        print("  （未跑全五档，不写 energy_table.md）")
    for w in warnings:
        print("⚠", w, file=sys.stderr)
    n_viol = sum(len(cc.violations) for cc in ccs.values())
    buckets = defaultdict(int)
    for rc in rechecks.values():
        for r in rc:
            buckets[r.bucket] += 1
    n_reps = sum(len(rc) for rc in rechecks.values())
    print(f"互证：{'全部通过' if n_viol == 0 else f'共 {n_viol} 行 / {n_reps} 个代表违反：' + '，'.join(f'{k} {v}' for k, v in sorted(buckets.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
