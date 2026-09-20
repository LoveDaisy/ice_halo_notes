# 产出 ../data/signature_table.md（9 个已知单反射透射楔角族在锥晶上的可达性 + 代表光路主表）、../data/signature_table_<tier>.csv
# （每个几何档位一份：该档位下每个精确 Φ 类一行，族内 / 族外都列）与 ../data/raypaths_<tier>.csv（该档位全部可行光路 PBD 代表清单，
# 供 analyze_energy.py 互证与 task-odd-radius-instances 挑「族外」实例，不用重跑枚举）。
# 这是 ch9 定理 7（九种楔）的可达性一侧：framework §3 定理 7′ 的每个数字都从这里的产出文件里来。
#
# 口径（与 scratchpad/scrum-ch9-prep/explore-pyramid-class-convergence 的裁定一致，Step 1 探针结果见该 scrum 下
# task-pyramid-signature-table/progress.md）：
# - **不做原始 Φ 类穷举**：锥晶镜面闭包群无限（定理 6），`phi_class` 的精确楔角判据（0.1°）随字长不收敛（2° 网格 L=2..7 类数
#   13/76/328/925/2247/4980，增量比值 ~2）。本表的行主键是**族**（9 行），不是类；类只作明细进 csv；
# - 族 = 精确 Φ 类楔角落在 9 个已知可透射楔角（定理 7）± TOL 内；族外类只记总数 / 总面积作背景，不逐类展开；
# - 截断字长 L_STAR：**诚实声明**该字长下每族的类数 / 条数 / 面积 / 最短代表，不宣称穷尽（族内类数在更大 L 下仍缓慢增长）；
# - 枚举参数：entry_faces=(1, 3, 13)（D6h 商掉后顶面 / 侧面 / 上锥面三个环带代表）、pbd_orbit 去重（D6 逐环带 × 上下互换 B，
#   explore 已用真实光路 Φ 指纹核对 7778 对同轨道 0 不一致）、GRID 见旁注、refine_levels=0（粗网格面积）；
# - 「面积」= 该族在该档位下全部 PBD 代表光路的 area_sr 逐条求和，每个对称轨道计一次；
# - 「细缝格」：同 ch8 判据（该格全部光路的 min_incidence_deg 都 > SLIVER_DEG，压在临界角 49.8° 下的贴棱掠射），主表用 † 标出；
# - 单面序列（外反射）无折射、Φ = S_n，不在族框架内，只在 md 末尾记一笔。
from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path

from lumice_integral.geometry import Pyramid, fold_matrix
from lumice_integral.geometry.core import N_ICE
from lumice_integral.geometry.enumerate import RaypathRecord, enumerate_raypaths_with_stats
from lumice_integral.geometry.feasibility import LatLonGrid
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import PhiClass, phi_class

DATA = Path(__file__).resolve().parent.parent / "data"
TIERS: tuple[tuple[float, float], ...] = ((1.0, 0.5), (0.5, 0.3), (2.0, 0.8), (1.0, 0.8))
"""几何档位 (h/a, tip_ratio)：默认几何、参数空间两个对角极值、以及只改 tip_ratio 的 (1, 0.8)。Step 1（L=4、2° 网格）扫
h/a ∈ {0.5,1,2} × tip_ratio ∈ {0.3,0.5,0.8} 全组合：族级可达 bitmap 只随 tip_ratio 变——tip_ratio=0.8 时 90° 族（顶面↔侧面，
`1-3` 走廊被锥面挡死）在 L=4 不可达、L=5 起经更长光路重新出现；h/a 不改 bitmap。(1, 0.8) 与默认档只差 tip_ratio 一个变量，
把这个效应单独隔离出来。"""
L_STAR = 6
"""截断字长（含入射面与出射面）。Step 1 实测 2° 网格 L=6 每档 ≈ 30 s，1° ≈ ×2.7；也是 tip_ratio=0.8 下 90° 族重新出现
（L=5 首现）有一档余量的最小值。"""
GRID = LatLonGrid(180, 360)
"""1° 网格（与 ch8 定案同分辨率）。Step 1 探针（默认几何、L=4）：2° → 1° 族级 bitmap / 每族类数不变，仅 28.0° / 52.4° 两族各多
召回 2 条窄窗口代表、族外多 9 类，耗时比值 2.7（ch8 经验 3.5×）——按 plan 判据本可沿用 2°，但成本差可忽略而 1° 与 ch8
口径一致且减少 MC 互证的「网格漏判」桶，取 1°。"""
ENTRY_FACES = (1, 3, 13)
KNOWN_WEDGES = (0.0, 28.0, 52.4, 56.0, 60.0, 62.0, 63.8, 80.2, 90.0)
"""定理 7 的 9 个可透射楔角（`check_pyramid.py` 的断言值）。"""
TOL = 0.5
"""族归并容差（°）：explore `scan_area.py` 同值；相邻两族最近相差 1.8°（62.0 / 63.8），±0.5° 不会互相吞并。"""
SLIVER_DEG = 49.0


def tier_label(tier: tuple[float, float]) -> str:
    ha, tr = tier
    return f"h{ha:g}_t{tr:g}"


def tier_pyramid(tier: tuple[float, float]) -> Pyramid:
    ha, tr = tier
    return Pyramid(a=1.0, h=ha, tip_ratio=tr)


def family_of(wedge_deg: float) -> float | None:
    """精确楔角 → 所属族的标称楔角（KNOWN_WEDGES 之一）；族外返回 None。"""
    for w in KNOWN_WEDGES:
        if abs(wedge_deg - w) <= TOL:
            return w
    return None


def min_deviation_deg(wedge_deg: float) -> float:
    """楔角 → 最小偏向角（晕半径）：$2\\arcsin(n\\sin(A/2)) - A$，$n$ = N_ICE。0° 给 0。"""
    s = N_ICE * math.sin(math.radians(wedge_deg / 2))
    return 2 * math.degrees(math.asin(min(1.0, s))) - wedge_deg


def family_name(wedge: float) -> str:
    """族的晕名：0° → 平行光路族；其余按最小偏向角取整，如 28.0° → 「9° 晕」。"""
    return "平行" if wedge == 0.0 else f"{round(min_deviation_deg(wedge)):d}° 晕"


class Cell:
    """一个 (族或类, 档位) 格子的聚合。"""

    def __init__(self) -> None:
        self.n_paths = 0
        self.area_sr = 0.0
        self.min_incidence_deg = math.inf
        self.shortest: RaypathRecord | None = None
        self.classes: set[PhiClass] = set()

    @property
    def sliver(self) -> bool:
        return self.min_incidence_deg > SLIVER_DEG

    def add(self, r: RaypathRecord, cls: PhiClass) -> None:
        self.n_paths += 1
        self.area_sr += r.area_sr
        self.min_incidence_deg = min(self.min_incidence_deg, r.min_incidence_deg)
        self.classes.add(cls)
        if self.shortest is None or (r.length, r.faces) < (self.shortest.length, self.shortest.faces):
            self.shortest = r


class TierResult:
    """一个档位的枚举 + 聚合：``by_family``（9 族 → Cell，不可达的族不出现）、``by_class``（每个精确 Φ 类 → Cell）、
    ``off``（族外全部类合并成一个 Cell）、单面记录、耗时。"""

    def __init__(self, tier: tuple[float, float], recs: list[RaypathRecord], elapsed_s: float, prune_rate: float) -> None:
        self.tier = tier
        self.recs = recs
        self.elapsed_s = elapsed_s
        self.prune_rate = prune_rate
        pyramid = tier_pyramid(tier)
        self.by_family: dict[float, Cell] = {}
        self.by_class: dict[PhiClass, Cell] = {}
        self.off = Cell()
        self.singles: list[RaypathRecord] = []
        self.class_of: dict[tuple[int, ...], PhiClass] = {}
        for r in recs:
            if r.length == 1:
                self.singles.append(r)
                continue
            cls = phi_class(pyramid, fold_matrix(pyramid, r.faces), r.faces[0], r.faces[-1])
            self.class_of[r.faces] = cls
            self.by_class.setdefault(cls, Cell()).add(r, cls)
            fam = family_of(cls.wedge_deg)
            if fam is None:
                self.off.add(r, cls)
            else:
                self.by_family.setdefault(fam, Cell()).add(r, cls)

    @property
    def n_multi(self) -> int:
        return len(self.recs) - len(self.singles)

    @property
    def area_total(self) -> float:
        return sum(c.area_sr for c in self.by_class.values())


def enumerate_tier(tier: tuple[float, float], max_len: int = L_STAR, grid: LatLonGrid = GRID) -> TierResult:
    """一个档位的完整枚举（与 analyze_energy.py 互证所用的口径完全相同：同 Pyramid / max_len / grid / entry_faces / PBD 去重）。"""
    t0 = time.monotonic()
    recs, stats = enumerate_raypaths_with_stats(tier_pyramid(tier), max_len, grid, entry_faces=ENTRY_FACES,
                                                 symmetry_orbit=rg.pbd_orbit)
    res = TierResult(tier, list(recs), time.monotonic() - t0, stats.prune_rate)
    ha, tr = tier
    print(f"h/a={ha:g}, tip_ratio={tr:g}: {len(recs)} 条记录（含 {len(res.singles)} 条外反射），Φ 类 {len(res.by_class)}"
          f"（族内 {sum(len(c.classes) for c in res.by_family.values())}，族外 {len(res.off.classes)}），"
          f"9 族命中 {len(res.by_family)}/9，prune_rate={res.prune_rate:.3f}，{res.elapsed_s:.1f} s")
    return res


# ---------- 产出文件 ----------


def write_raypaths_csv(res: TierResult) -> Path:
    """该档位全部可行光路（PBD 代表）清单：面序列 / 长度 / 面积 / 最小入射角 / 精确楔角 / 所属族（空 = 族外）。"""
    path = DATA / f"raypaths_{tier_label(res.tier)}.csv"
    with path.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["raypath", "length", "area_sr", "min_incidence_deg", "wedge_deg", "family"])
        for r in sorted(res.recs, key=lambda r: (r.length, r.faces)):
            if r.length == 1:
                w.writerow([r.label, 1, f"{r.area_sr:.6f}", f"{r.min_incidence_deg:.3f}", "", ""])
                continue
            cls = res.class_of[r.faces]
            fam = family_of(cls.wedge_deg)
            w.writerow([r.label, r.length, f"{r.area_sr:.6f}", f"{r.min_incidence_deg:.3f}", f"{cls.wedge_deg:.1f}",
                        "" if fam is None else f"{fam:g}"])
    return path


def class_rows(res: TierResult) -> list[tuple[PhiClass, Cell]]:
    """csv 行序：族内按 (族, 最短代表长度, 最短代表面序列)，族外排在后面同序。"""
    def key(item: tuple[PhiClass, Cell]) -> tuple:
        cls, cell = item
        fam = family_of(cls.wedge_deg)
        return (fam is None, fam if fam is not None else cls.wedge_deg, cell.shortest.length, cell.shortest.faces)
    return sorted(res.by_class.items(), key=key)


def write_csv(res: TierResult) -> Path:
    """每个精确 Φ 类一行：楔角 / 族 / 规范 signature 的入出面 / 折叠矩阵 / 条数 / 面积 / 最小入射角 / 细缝 / 最短代表。"""
    path = DATA / f"signature_table_{tier_label(res.tier)}.csv"
    with path.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["wedge_deg", "family", "sig_entry", "sig_exit", "fold_matrix", "n_paths", "area_sr_sum",
                    "min_incidence_deg", "sliver", "shortest_path", "shortest_area_sr", "shortest_min_incidence_deg"])
        for cls, cell in class_rows(res):
            fam = family_of(cls.wedge_deg)
            k, a, b = cls.signature
            s = cell.shortest
            w.writerow([f"{cls.wedge_deg:.1f}", "" if fam is None else f"{fam:g}", a, b, " ".join(f"{x:g}" for x in k),
                        cell.n_paths, f"{cell.area_sr:.6f}", f"{cell.min_incidence_deg:.3f}", int(cell.sliver),
                        s.label, f"{s.area_sr:.6f}", f"{s.min_incidence_deg:.3f}"])
    return path


def fmt_cell(cell: Cell | None) -> str:
    if cell is None:
        return "—"
    return f"{len(cell.classes)} / {cell.n_paths} / {cell.area_sr:.4f}{'†' if cell.sliver else ''}"


def write_md(results: dict[tuple[float, float], TierResult]) -> Path:
    tiers = list(results)
    labels = [f"({ha:g}, {tr:g})" for ha, tr in tiers]
    lines = []
    lines.append("# 锥晶九种楔角族的可达性表（ch9 定理 7′ 的数据）")
    lines.append("")
    lines.append(f"> 产出：`code/enumerate_signatures.py`（`max_len={L_STAR}`、`entry_faces={ENTRY_FACES}`、PBD 去重、"
                 f"`LatLonGrid({GRID.n_theta}, {GRID.n_phi})`、粗网格面积；族归并容差 ±{TOL:g}°）；每个档位的精确 Φ 类明细在 "
                 "`signature_table_<tier>.csv`，全部可行光路清单在 `raypaths_<tier>.csv`（`<tier>` = `h<h/a>_t<tip_ratio>`）。")
    lines.append("> 档位 = (h/a, tip_ratio)：h/a 是棱柱段高度 / 六边形边长（`Pyramid(a=1, h=h/a)`），tip_ratio 是锥台截顶位置占理论锥高的比例；"
                 f"锥面倾角固定 c/a = {Pyramid().c_over_a:g}（62.0°）。")
    lines.append("> 族 = 精确 Φ 类楔角（`halo_notes.math.signature.phi_class`，0.1°）落在定理 7 的 9 个可透射楔角 ± 容差内；晕名按最小偏向角 "
                 f"$2\\arcsin(n\\sin(A/2))-A$（$n={N_ICE:g}$）取整。")
    lines.append("> 格子 = 类数 / 光路条数（PBD 代表）/ 面积（sr，全部代表光路可行方向集面积逐条求和，每个对称轨道计一次）；† = 细缝格"
                 f"（格内全部光路的最小入射角都 > {SLIVER_DEG:g}°，压在临界角 49.8° 下的贴棱掠射，同 ch8 判据）。")
    lines.append(f"> **诚实声明**：锥晶镜面闭包群无限（定理 6），精确 Φ 类数随字长上限不收敛（2° 网格 L=2..7：13/76/328/925/2247/4980），"
                 f"族内类数在 L>{L_STAR} 下仍会缓慢增长。本表只声明「长度 ≤ {L_STAR} 下每族可达、代表光路是什么、方向集有多大」，"
                 "不宣称穷尽；「可达」这一结论本身在 L=2 就已对 9 族全部成立。")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append("| 档位 (h/a, tip_ratio) | " + " | ".join(labels) + " |")
    lines.append("|---|" + "---|" * len(tiers))
    lines.append("| 9 族命中数 | " + " | ".join(f"{len(results[t].by_family)}" for t in tiers) + " |")
    lines.append("| 其中扎实可达（剔除细缝格 †） | " + " | ".join(str(sum(1 for c in results[t].by_family.values() if not c.sliver)) for t in tiers) + " |")
    lines.append(f"| 精确 Φ 类数（长度 ≤ {L_STAR}） | " + " | ".join(str(len(results[t].by_class)) for t in tiers) + " |")
    lines.append("| 其中族内 / 族外 | " + " | ".join(f"{sum(len(c.classes) for c in results[t].by_family.values())} / {len(results[t].off.classes)}" for t in tiers) + " |")
    lines.append(f"| 光路条数（PBD 代表，长度 2–{L_STAR}） | " + " | ".join(str(results[t].n_multi) for t in tiers) + " |")
    lines.append("| 其中族内 / 族外 | " + " | ".join(f"{sum(c.n_paths for c in results[t].by_family.values())} / {results[t].off.n_paths}" for t in tiers) + " |")
    lines.append("| 面积合计 (sr) 族内 / 族外 | " + " | ".join(f"{sum(c.area_sr for c in results[t].by_family.values()):.4f} / {results[t].off.area_sr:.4f}" for t in tiers) + " |")
    lines.append("| 族外面积占比 | " + " | ".join(f"{results[t].off.area_sr / results[t].area_total:.1%}" for t in tiers) + " |")
    lines.append("| prune_rate | " + " | ".join(f"{results[t].prune_rate:.3f}" for t in tiers) + " |")
    lines.append("| 枚举耗时 (s) | " + " | ".join(f"{results[t].elapsed_s:.0f}" for t in tiers) + " |")
    lines.append("")
    lines.append("## 主表：9 个楔角族")
    lines.append("")
    lines.append("| 楔角 | 晕 | 可达档位 | 最短代表 | " + " | ".join(f"类数 / 条数 / 面积@{lab}" for lab in labels) + " |")
    lines.append("|---|---|---|---|" + "---|" * len(tiers))
    for wedge in KNOWN_WEDGES:
        reach = [t for t in tiers if wedge in results[t].by_family]
        if reach:
            best = min(((results[t].by_family[wedge].shortest, t) for t in reach), key=lambda p: (p[0].length, p[0].faces, tiers.index(p[1])))
            shortest = f"`{best[0].label}`"
        else:
            shortest = "—"
        cells = " | ".join(fmt_cell(results[t].by_family.get(wedge)) for t in tiers)
        lines.append(f"| {wedge:g}° | {family_name(wedge)} | {', '.join(labels[tiers.index(t)] for t in reach) if reach else '—'} | {shortest} | {cells} |")
    lines.append("")
    lines.append("## 每族每档位的最短代表")
    lines.append("")
    lines.append("| 楔角 | " + " | ".join(f"最短代表@{lab}（面积 sr / 最小入射角）" for lab in labels) + " |")
    lines.append("|---|" + "---|" * len(tiers))
    for wedge in KNOWN_WEDGES:
        cells = []
        for t in tiers:
            c = results[t].by_family.get(wedge)
            cells.append("—" if c is None else f"`{c.shortest.label}`（{c.shortest.area_sr:.4f} / {c.shortest.min_incidence_deg:.1f}°）")
        lines.append(f"| {wedge:g}° | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## 每族首次出现的字长（该档位下最短代表的长度）")
    lines.append("")
    lines.append("| 楔角 | " + " | ".join(labels) + " |")
    lines.append("|---|" + "---|" * len(tiers))
    for wedge in KNOWN_WEDGES:
        lines.append(f"| {wedge:g}° | " + " | ".join("—" if wedge not in results[t].by_family else str(results[t].by_family[wedge].shortest.length) for t in tiers) + " |")
    lines.append("")
    lines.append("## 族外背景注记")
    lines.append("")
    lines.append(f"族外 = 精确楔角不在 9 个已知楔角 ±{TOL:g}° 内的 Φ 类（多次反射把 62.0° 锥面法向转到新方向后与入出面夹出的「奇异」楔角）。"
                 "它们不是本表的对象（穷举不收敛，见诚实声明），但它们的方向集面积并不可忽略——这是 explore 阶段已证实的事实，本表如实带上：")
    lines.append("")
    for t in tiers:
        res = results[t]
        lines.append(f"- {labels[tiers.index(t)]}：族外 {len(res.off.classes)} 类、{res.off.n_paths} 条、面积 {res.off.area_sr:.4f} sr"
                     f"（占全部 {res.area_total:.4f} sr 的 {res.off.area_sr / res.area_total:.1%}）；最短族外代表 `{res.off.shortest.label}`"
                     f"（楔角 {res.class_of[res.off.shortest.faces].wedge_deg:.1f}°）。逐条见 `raypaths_{tier_label(t)}.csv` 的 `family` 空列。")
    lines.append("")
    lines.append("## 细缝格与单档不可达")
    lines.append("")
    for t in tiers:
        res = results[t]
        missing = [w for w in KNOWN_WEDGES if w not in res.by_family]
        slivers = [(w, res.by_family[w]) for w in KNOWN_WEDGES if w in res.by_family and res.by_family[w].sliver]
        lines.append(f"- {labels[tiers.index(t)]}：不可达 {len(missing)} 族" + (f"（{', '.join(f'{w:g}°' for w in missing)}）" if missing else "")
                     + f"；细缝格 {len(slivers)} 个" + ("（" + "；".join(f"{w:g}°：{c.n_paths} 条、面积 {c.area_sr:.4f} sr、最小入射角 {c.min_incidence_deg:.2f}°、最短 `{c.shortest.label}`" for w, c in slivers) + "）" if slivers else "") + "。")
    lines.append("")
    lines.append("## 外反射")
    lines.append("")
    lines.append("单面序列（外反射，无折射，Φ = S_n）不在族框架内；每档恒可达，可行方向集为半球（面积 2π ≈ "
                 f"{2 * math.pi:.4f} sr）：" + "；".join(f"{labels[tiers.index(t)]}: " + ", ".join(f"`{s.label}`" for s in results[t].singles) for t in tiers) + "。")
    lines.append("")
    path = DATA / "signature_table.md"
    path.write_text("\n".join(lines))
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-len", type=int, default=L_STAR, help=f"截断字长（调试用；正式产出用 {L_STAR}）")
    args = ap.parse_args(argv)
    if args.max_len != L_STAR:
        print(f"⚠ max_len={args.max_len} ≠ L_STAR={L_STAR}，只打印不写文件")
    DATA.mkdir(exist_ok=True)
    results: dict[tuple[float, float], TierResult] = {}
    for tier in TIERS:
        results[tier] = res = enumerate_tier(tier, args.max_len)
        if args.max_len == L_STAR:
            print("  →", write_csv(res).name, "，", write_raypaths_csv(res).name)
    if args.max_len == L_STAR:
        print("  →", write_md(results).name)
    missing = {tier: [w for w in KNOWN_WEDGES if w not in results[tier].by_family] for tier in TIERS}
    if any(missing.values()):
        print("⚠ 空族：", {tier: m for tier, m in missing.items() if m})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
