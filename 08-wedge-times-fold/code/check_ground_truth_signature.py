# 产出 ../data/ground_truth_signature.md：ch3 `raypath_ground_truth.txt` 的 93 条光路（按晕名分组）逐条过
# halo_notes.math.signature.phi_class（片晶 h/a = 0.2），核对「同组同 Φ 类」以及 0° 组与 ch7 发表的 6 类
# （reflection_group.HALO_NAMES）的对应；不一致的条目逐条列出（标题 / ch3 标签 / Φ 类三者互相对照）。
# 这是 framework §2 定理 5″ 升 [算] 的必要条件之一；单测 halo_notes/math/tests/test_signature_data.py 把本脚本的结论钉成回归锁。
from __future__ import annotations

from pathlib import Path

import numpy as np

from halo_notes.geometry import HexPrism, fold_matrix
from halo_notes.geometry.ground_truth import GroundTruthRow, ground_truth_groups
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import PhiRow, phi_batch, phi_class, phi_class_table

DATA = Path(__file__).resolve().parent.parent / "data"
CRYSTAL = HexPrism.from_ratio(0.2)          # ground truth 是片晶光路

# ch3 文件里的晕名 → ch7 HALO_NAMES 片晶列的写法（只差空格 / 度号 / 用词）
GROUP_ALIASES = {"原路前进": "太阳原像"}


def normalize(name: str) -> str:
    return GROUP_ALIASES.get(name, name).replace(" ", "").replace("°", "")


_DIRS = np.random.default_rng(1).normal(size=(2000, 3))
_DIRS /= np.linalg.norm(_DIRS, axis=1, keepdims=True)


def elevation_sign(faces: tuple[int, ...]) -> int | None:
    """在定义域上采样核验 Φ 是否保持仰角：出射 z 分量 = 入射 z 分量返回 +1（同一条等仰角圆），= −z 返回 −1（映到地平线下），
    否则 ``None``。竖直面折射 / 竖直镜都保持 z 分量，底面镜翻转它——片晶绕 z 旋转后，这决定光落在幻日环还是映幻日环上。"""
    M = fold_matrix(CRYSTAL, faces)
    out = phi_batch(CRYSTAL, M, faces[0], faces[-1], _DIRS)
    ok = ~np.isnan(out[:, 0])
    if not ok.any():
        return None
    if np.allclose(out[ok, 2], _DIRS[ok, 2], atol=1e-9):
        return 1
    if np.allclose(out[ok, 2], -_DIRS[ok, 2], atol=1e-9):
        return -1
    return None


def classify_row(row: GroundTruthRow, by_class: dict) -> tuple[str, int]:
    """返回 ``(Φ 类 id 或 'R'(外反射), 折叠矩阵编号)``。"""
    if len(row.faces) == 1:
        return "R", rg.identify(rg.MIRRORS[row.faces[0]]).number
    M = fold_matrix(CRYSTAL, row.faces)
    cls = phi_class(CRYSTAL, M, row.faces[0], row.faces[-1])
    return by_class[cls].id, rg.identify(M).number


def analyse() -> tuple[dict[str, dict[str, list[tuple[GroundTruthRow, int]]]], tuple[PhiRow, ...]]:
    """``{晕名: {Φ 类 id: [(行, M 编号), …]}}``。"""
    rows = phi_class_table(CRYSTAL)
    by_class = {r.phi_class: r for r in rows}
    out: dict[str, dict[str, list[tuple[GroundTruthRow, int]]]] = {}
    for name, members in ground_truth_groups().items():
        buckets = out.setdefault(name, {})
        for row in members:
            cid, fold = classify_row(row, by_class)
            buckets.setdefault(cid, []).append((row, fold))
    return out, rows


def main() -> None:
    result, rows = analyse()
    table = {r.id: r for r in rows}
    published_plate = {normalize(plate): t for t, (_, plate) in rg.HALO_NAMES.items()}
    lines = ["# ch3 ground truth 光路的 Φ 类对表（片晶 h/a = 0.2）", "",
             "> 产出：`code/check_ground_truth_signature.py`；数据：`03-parallel-raypaths/data/raypath_ground_truth.txt`（93 条，"
             "按晕名分组，每行带 ch3 当年的 1–14 类标签）。Φ 类编号见 `signature_table.md`。`R` = 单面外反射（不在 34 类框架内）。", ""]
    lines += ["## 分组 → Φ 类", "", "| 晕名 | 条数 | Φ 类（条数） | 一致 |", "|---|---|---|---|"]
    inconsistent: list[tuple[str, str, GroundTruthRow, int]] = []
    consistent_groups = 0
    for name, buckets in result.items():
        internal = {cid: v for cid, v in buckets.items() if cid != "R"}
        ok = len(internal) == 1
        consistent_groups += ok
        cells = ", ".join(f"{cid}（{len(v)}）" for cid, v in buckets.items())
        lines.append(f"| {name} | {sum(len(v) for v in buckets.values())} | {cells} | {'✓' if ok else '✗'} |")
        if not ok:
            main_id = max(internal, key=lambda cid: len(internal[cid]))
            for cid, v in internal.items():
                if cid != main_id:
                    inconsistent += [(name, cid, row, fold) for row, fold in v]
    n_rows = sum(len(v) for b in result.values() for v in b.values())
    lines += ["", f"共 {len(result)} 组 {n_rows} 条；{consistent_groups} 组内部同一 Φ 类，{len(result) - consistent_groups} 组不一致（共 {len(inconsistent)} 条落在组内多数类之外）。", ""]

    lines += ["## 0° 组 ↔ ch7 发表的 6 类（HALO_NAMES 片晶列）", "", "| 晕名 | Φ 类 | 折叠类 | HALO_NAMES 发表类型 | 对应 |", "|---|---|---|---|---|"]
    for name, buckets in result.items():
        for cid, v in buckets.items():
            if cid == "R" or table[cid].wedge_deg != 0.0 or len(v) < len(buckets.get(max(buckets, key=lambda c: len(buckets[c])), [])):
                continue
            row = table[cid]
            t = published_plate.get(normalize(name))
            match = t is not None and tuple(rg.class_of(row.folds[0])) == tuple(sorted(e.number for e in rg.ELEMENTS if e.published_type == t))
            lines.append(f"| {name} | {cid} | #{'/#'.join(map(str, row.folds))} | {t if t is not None else '—'} | {'✓' if match else '✗'} |")
    lines += ["", "## 外反射行", ""]
    for name, buckets in result.items():
        for row, fold in buckets.get("R", []):
            main_id = max((c for c in buckets if c != "R"), key=lambda c: len(buckets[c]))
            lines.append(f"- `{row.faces[0]}`（{name}）：Φ = S_{row.faces[0]} = #{fold}，与本组 0° 类 {main_id} 的折叠类 #{'/#'.join(map(str, table[main_id].folds))} "
                         f"{'一致' if fold in table[main_id].folds else '不一致'}")
    lines += ["", "## 不一致条目（逐条）", "",
              "| 标题（晕名） | ch3 标签 | 光路 | M | Φ 类 | 楔角 | 仰角 | 判读 |", "|---|---|---|---|---|---|---|---|"]
    verdicts: dict[str, int] = {}
    for name, cid, row, fold in inconsistent:
        r = table[cid]
        main_id = max((c for c in result[name] if c != "R"), key=lambda c: len(result[name][c]))
        same_class_groups = sorted({g for g, b in result.items() if cid in b and g != name})
        sign = elevation_sign(row.faces)
        expect = -1 if name.startswith("映") else 1
        if sign != expect:
            kind, verdict = "判据错", f"仰角核验失败（Φ 输出 z 分量与 {name} 应有的符号不符）"
        elif same_class_groups:
            kind = "标题与标签不一致"
            verdict = (f"与 {same_class_groups[0]} 组同 Φ 类、同 ch3 标签 {row.label}（该组的映射，定义域更小）；幻日本就落在幻日环上，"
                       f"标题按环归、标签按幻日归——文件内部两种归法并存")
        else:
            kind = "晕名粗于 Φ 类"
            verdict = (f"M = #{fold} 在 {name} 的折叠类里，但楔角 {r.wedge_deg:g}°（{r.family}），Φ 类 {cid} ≠ 组内多数 {main_id}；"
                       f"仰角核验 ✓（竖直面折射与竖直镜保持仰角{'、底面镜翻转' if sign < 0 else ''}），片晶绕 z 旋转后光仍落在{name}上——"
                       f"晕名按落点归组没错，Φ 类按映射分得更细")
        verdicts[kind] = verdicts.get(kind, 0) + 1
        lines.append(f"| {name} | {row.label} | `{'-'.join(map(str, row.faces))}` | #{fold} | {cid} | {r.wedge_deg:g}° | "
                     f"{'保持' if sign == 1 else '翻转' if sign == -1 else '✗'} | **{kind}**：{verdict} |")
    lines += ["", f"判读口径（issue 的三选一）：**判据错** = Φ 类算错（本任务归类逻辑有 bug；用仰角守恒独立核验，本次 {verdicts.get('判据错', 0)} 条）；"
              "**晕名粗于 Φ 类** = 对应 issue 的「分类错」——不是 ch3 错，而是「晕名」按片晶旋转后的落点归组、一个晕可由多个 Φ 类点亮，"
              "Φ 类是更细的分辨率；**标题与标签不一致** = 对应「数据错」，文件里同一条光路标题按环、标签按幻日。",
              "", "统计：" + "；".join(f"{k} {v} 条" for k, v in verdicts.items()) + "。", ""]
    path = DATA / "ground_truth_signature.md"
    path.write_text("\n".join(lines))
    print("\n".join(lines))
    print("→", path)


if __name__ == "__main__":
    main()
