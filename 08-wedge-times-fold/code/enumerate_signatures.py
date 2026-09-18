# 产出 ../data/signature_table.md（34 个 Φ 类的可达性主表）与 ../data/signature_table_<ha>.csv（42 个 signature 类粒度，
# 每个高径比一份）：对 h/a ∈ {0.2, 0.5, 1, 2, 5} 用 lumice_integral.geometry.enumerate 枚举长度 ≤ 8 的全部可行光路（PBD 代表），
# 每条经 halo_notes.math.signature 落到 signature 类 / Φ 类，按类聚合可达 h/a、光路条数、可行方向面积之和、最短代表。
# 这是 ch8 定理 5′ 上界（34）的下界一侧：framework §2 定理 5″ 的每个数字都从这里的产出文件里来。
#
# 口径：
# - 枚举参数沿用子任务 15.2：entry_faces=(1, 3)、pbd_orbit 去重、LatLonGrid(180, 360)（1° 网格，n_phi 是 6 的倍数，D6h 精确不变；15.2/15.4 时为 2°，见 GRID 旁注）、
#   refine_levels=0（粗网格面积）。PBD = D6 × 上下互换 = D6h，与 signature 商掉的群相同，每条记录代表一个 D6h 轨道；
# - 「面积」= 该类在该 h/a 下全部 PBD 代表光路的 area_sr 逐条求和（每个对称轨道计一次），不是某一条代表的面积；
# - 「细缝格」：该格全部光路的「首尾入（出）射角较大者的最小值」都 > 49°（压在临界角 49.8° 下，子任务 15.2 对 1-3-4 等
#   贴棱掠射条目的同一判据），几何上可达但方向集是一条细缝，主表用 † 标出并在汇总里单独计数，不与扎实可达混算；
# - 单面序列（外反射 1、3）没有折射、Φ = S_n，不在 34 类框架内，只在 md 末尾记一笔；
# - 42 类粒度的 csv 行 = 一条规范 signature (M, a, b)，带 phi_class_id 指向所属的 34 类主键（同一份类归属只在
#   halo_notes.math.signature.phi_class_table 里算一次，csv 只是引用）。
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from lumice_integral.geometry import HexPrism, Pyramid, fold_matrix
from lumice_integral.geometry.enumerate import RaypathRecord, enumerate_raypaths_with_stats
from lumice_integral.geometry.feasibility import LatLonGrid
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import PhiRow, phi_class, phi_class_table

DATA = Path(__file__).resolve().parent.parent / "data"
RATIOS = (0.2, 0.5, 1.0, 2.0, 5.0)
MAX_LEN = 8
GRID = LatLonGrid(180, 360)   # 1° 网格：2° 时五档共漏判 240 个窄窗口代表（MC 互证发现），1° 全部召回、0.5° 不再多，耗时约 3.5×（主 session 探针 2026-09-15）
ENTRY_FACES = (1, 3)
SLIVER_DEG = 49.0            # 细缝格判据：格内全部光路的 min_incidence_deg 都 > 49°

# 表注里要点名的已知晕（issue 第 3 条）：面序列 → 说明
KNOWN_HALOS = {
    (3, 5): "22° 幻日 / 22° 晕（22° 族，M = e）",
    (3, 1, 5): "映幻日（22° 族，M = b）",
    (1, 3): "环天顶弧（46° 族，M = e，顶面进侧面出）",
    (3, 2): "环地平弧（46° 族，M = e，侧面进底面出）",
    (1, 2): "太阳原像（平行，M = e）",
    (3, 1, 5, 7, 4): "映 120° 幻日（平行，M = #3，ch7 代表光路）",
}


def ha_label(ratio: float) -> str:
    return f"{ratio:g}"


class Cell:
    """一个 (类, h/a) 格子的聚合。"""

    def __init__(self) -> None:
        self.n_paths = 0
        self.area_sr = 0.0
        self.min_incidence_deg = math.inf
        self.shortest: RaypathRecord | None = None

    @property
    def sliver(self) -> bool:
        return self.min_incidence_deg > SLIVER_DEG

    def add(self, r: RaypathRecord) -> None:
        self.n_paths += 1
        self.area_sr += r.area_sr
        self.min_incidence_deg = min(self.min_incidence_deg, r.min_incidence_deg)
        if self.shortest is None or (r.length, r.faces) < (self.shortest.length, self.shortest.faces):
            self.shortest = r


def classify(ratio: float, rows: tuple[PhiRow, ...]) -> tuple[dict[str, Cell], dict[tuple, Cell], list[RaypathRecord]]:
    """枚举一个高径比并按 Φ 类（34）与 signature 类（42）聚合；返回 ``(按 row.id, 按 (row.id, signature), 单面记录)``。"""
    crystal = HexPrism.from_ratio(ratio)
    recs, stats = enumerate_raypaths_with_stats(crystal, MAX_LEN, GRID, entry_faces=ENTRY_FACES,
                                                symmetry_orbit=rg.pbd_orbit)
    by_row = {r.phi_class: r for r in rows}
    by_class: dict[str, Cell] = {}
    by_sig: dict[tuple, Cell] = {}
    singles = []
    for r in recs:
        if r.length == 1:
            singles.append(r)
            continue
        cls = phi_class(crystal, fold_matrix(crystal, r.faces), r.faces[0], r.faces[-1])
        row = by_row[cls]
        by_class.setdefault(row.id, Cell()).add(r)
        by_sig.setdefault((row.id, cls.signature), Cell()).add(r)
    print(f"h/a={ratio:g}: {len(recs)} 条记录（含 {len(singles)} 条外反射），Φ 类 {len(by_class)}，signature 类 {len(by_sig)}，"
          f"prune_rate={stats.prune_rate:.3f}")
    return by_class, by_sig, singles


def write_csv(ratio: float, rows: tuple[PhiRow, ...], by_sig: dict[tuple, Cell]) -> Path:
    path = DATA / f"signature_table_{ha_label(ratio)}.csv"
    with path.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["phi_class_id", "wedge_deg", "family", "folds", "sig_fold", "sig_entry", "sig_exit", "n_paths",
                    "area_sr_sum", "min_incidence_deg", "sliver", "shortest_path", "shortest_area_sr",
                    "shortest_min_incidence_deg"])
        for row in rows:
            if not row.transmittable:
                continue
            for sig in row.signatures:
                k, a, b = sig
                cell = by_sig.get((row.id, sig))
                if cell is None:
                    continue          # 该 h/a 下不可达的 signature 类不出现（md 主表里不可达仍占行）
                fold = rg.identify(np.array(k).reshape(3, 3)).number
                s = cell.shortest
                w.writerow([row.id, f"{row.wedge_deg:g}", row.family, "/".join(map(str, row.folds)), fold, a, b,
                            cell.n_paths, f"{cell.area_sr:.6f}", f"{cell.min_incidence_deg:.3f}", int(cell.sliver),
                            s.label, f"{s.area_sr:.6f}", f"{s.min_incidence_deg:.3f}"])
    return path


def fmt_pairs(row: PhiRow) -> str:
    return ", ".join(f"{a}→{b}" for a, b in row.face_pairs)


def fmt_folds(row: PhiRow) -> str:
    return "#" + "/#".join(map(str, row.folds))


def write_md(rows: tuple[PhiRow, ...], cells: dict[float, dict[str, Cell]], singles: dict[float, list[RaypathRecord]]) -> Path:
    live = [r for r in rows if r.transmittable]
    reach = {r.id: [ratio for ratio in RATIOS if r.id in cells[ratio]] for r in live}
    per_ratio = {ratio: sorted(cells[ratio]) for ratio in RATIOS}
    union = sorted({rid for ratio in RATIOS for rid in cells[ratio]})
    lines = []
    lines.append("# 六棱柱 Φ 类可达性表（ch8 定理 5″ 的数据）")
    lines.append("")
    lines.append(f"> 产出：`code/enumerate_signatures.py`（`max_len={MAX_LEN}`、`entry_faces={ENTRY_FACES}`、PBD 去重、"
                 f"`LatLonGrid({GRID.n_theta}, {GRID.n_phi})`、粗网格面积）；每个 h/a 的 42 类粒度明细在 `signature_table_<ha>.csv`。")
    lines.append("> 类编号 `A<楔角>-<序号>` 由 `halo_notes.math.signature.phi_class_table` 按 (楔角, 折叠类最小编号, 规范 signature) 排序确定，与运行顺序无关。")
    lines.append("> 面积 = 该类在该 h/a 下全部 PBD 代表光路的可行方向集面积（sr）逐条求和，每个对称轨道计一次，不是某一条代表的面积。")
    lines.append("> 最短代表 = 五档 h/a 里按 (长度, 字典序) 最小的代表光路（PBD 轨道代表，即轨道里字典序最小的面序列）。")
    lines.append(f"> † = 细缝格：该格全部光路的最小入射角都 > {SLIVER_DEG:g}°（压在临界角 49.8° 下的贴棱掠射，与子任务 15.2 对 `1-3-4` 的判据相同），"
                 "几何上可达但方向集只是一条细缝；汇总里「扎实可达」不计它们。")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append("| h/a | " + " | ".join(ha_label(r) for r in RATIOS) + " | 五档并集 | 上界 |")
    lines.append("|---|" + "---|" * (len(RATIOS) + 2))
    lines.append("| 可达 Φ 类数 | " + " | ".join(str(len(per_ratio[r])) for r in RATIOS) + f" | {len(union)} | 34 |")
    solid = {ratio: sorted(rid for rid, c in cells[ratio].items() if not c.sliver) for ratio in RATIOS}
    solid_union = sorted(set().union(*solid.values()))
    lines.append("| 其中扎实可达（剔除细缝格 †） | " + " | ".join(str(len(solid[r])) for r in RATIOS) + f" | {len(solid_union)} | 34 |")
    for wedge in (0.0, 60.0, 90.0):
        ids = {r.id for r in live if r.wedge_deg == wedge}
        total = len(ids)
        lines.append(f"| 其中 {wedge:g}° | " + " | ".join(str(len(ids & set(per_ratio[r]))) for r in RATIOS)
                     + f" | {len(ids & set(union))} | {total} |")
    lines.append("| 光路条数（PBD 代表，长度 2–8） | " + " | ".join(str(sum(c.n_paths for c in cells[r].values())) for r in RATIOS) + " | — | — |")
    lines.append("")
    lines.append("## 主表：34 个 Φ 类")
    lines.append("")
    lines.append("| 类 | 楔角 | 族 | 折叠类 | 入出面对 | 可达 h/a | 最短代表 | " + " | ".join(f"面积@{ha_label(r)}" for r in RATIOS) + " |")
    lines.append("|---|---|---|---|---|---|---|" + "---|" * len(RATIOS))
    for r in live:
        rs = reach[r.id]
        if rs:
            best = min(((cells[x][r.id].shortest, x) for x in rs), key=lambda t: (t[0].length, t[0].faces, t[1]))
            shortest = f"`{best[0].label}`"
        else:
            shortest = "—"
        areas = " | ".join(f"{cells[x][r.id].area_sr:.4f}{'†' if cells[x][r.id].sliver else ''}" if r.id in cells[x] else "—"
                           for x in RATIOS)
        lines.append(f"| {r.id} | {r.wedge_deg:g}° | {r.family} | {fmt_folds(r)} | {fmt_pairs(r)} | "
                     f"{', '.join(ha_label(x) for x in rs) if rs else '—'} | {shortest} | {areas} |")
    lines.append("")
    lines.append("## 光路条数（PBD 代表）")
    lines.append("")
    lines.append("| 类 | " + " | ".join(f"条数@{ha_label(r)}" for r in RATIOS) + " |")
    lines.append("|---|" + "---|" * len(RATIOS))
    for r in live:
        lines.append(f"| {r.id} | " + " | ".join(str(cells[x][r.id].n_paths) if r.id in cells[x] else "—" for x in RATIOS) + " |")
    lines.append("")
    empty = [r for r in live if not reach[r.id]]
    lines.append("## 五档 h/a 都不可达的类")
    lines.append("")
    if empty:
        for r in empty:
            lines.append(f"- {r.id}（{r.wedge_deg:g}°，{fmt_folds(r)}，{fmt_pairs(r)}）：（几何原因待逐条补写）")
    else:
        lines.append("（无：34 个类在长度 ≤ 8、五档 h/a 的并集下全部可达。）")
    lines.append("")
    lines.append("## 细缝格与单档不可达")
    lines.append("")
    for x in RATIOS:
        missing = [r.id for r in live if r.id not in cells[x]]
        slivers = [(r.id, cells[x][r.id]) for r in live if r.id in cells[x] and cells[x][r.id].sliver]
        lines.append(f"- h/a={ha_label(x)}：不可达 {len(missing)} 类" + (f"（{', '.join(missing)}）" if missing else "")
                     + f"；细缝格 {len(slivers)} 个" + ("（" + "；".join(f"{rid}：{c.n_paths} 条、面积 {c.area_sr:.4f} sr、最小入射角 {c.min_incidence_deg:.2f}°、最短 `{c.shortest.label}`" for rid, c in slivers) + "）" if slivers else "") + "。")
    lines.append("")
    lines.append("## 表注：已知晕的格子")
    lines.append("")
    by_row = {r.phi_class: r for r in rows}
    crystal = HexPrism.from_ratio(0.2)
    for faces, note in KNOWN_HALOS.items():
        cls = phi_class(crystal, fold_matrix(crystal, faces), faces[0], faces[-1])
        row = by_row[cls]
        label = "-".join(map(str, faces))
        rs = reach[row.id]
        lines.append(f"- `{label}`：{note} → **{row.id}**（可达 h/a：{', '.join(ha_label(x) for x in rs) if rs else '—'}）")
    lines.append("")
    lines.append("## 外反射")
    lines.append("")
    lines.append("单面序列 `1`、`3`（外反射，无折射，Φ = S_n）不在 34 类框架内；每档 h/a 恒可达，可行方向集为半球（面积 2π ≈ "
                 f"{2 * math.pi:.4f} sr）：" + "；".join(f"h/a={ha_label(x)}: " + ", ".join(f"`{s.label}`" for s in singles[x]) for x in RATIOS) + "。")
    lines.append("")
    path = DATA / "signature_table.md"
    path.write_text("\n".join(lines))
    return path


def pyramid_smoke() -> int:
    """锥晶 smoke：`Pyramid()` 默认参数、max_len=3，只证管线不崩、类数非平凡增长（完整枚举是 ch9 的事）。"""
    pyramid = Pyramid()
    recs, _ = enumerate_raypaths_with_stats(pyramid, 3, LatLonGrid(45, 90), entry_faces=(1, 3, 13))
    classes = {phi_class(pyramid, fold_matrix(pyramid, r.faces), r.faces[0], r.faces[-1]) for r in recs if r.length > 1}
    assert len(classes) > 1
    print(f"锥晶 smoke：{len(recs)} 条记录（max_len=3）→ {len(classes)} 个 Φ 类（六棱柱可透射类共 34）")
    return len(classes)


def main() -> None:
    DATA.mkdir(exist_ok=True)
    rows = phi_class_table(HexPrism.from_ratio(RATIOS[0]))
    assert sum(r.transmittable for r in rows) == 34
    cells: dict[float, dict[str, Cell]] = {}
    singles: dict[float, list[RaypathRecord]] = {}
    for ratio in RATIOS:
        by_class, by_sig, singles[ratio] = classify(ratio, rows)
        cells[ratio] = by_class
        print("  →", write_csv(ratio, rows, by_sig).name)
    print("  →", write_md(rows, cells, singles).name)
    pyramid_smoke()


if __name__ == "__main__":
    main()
