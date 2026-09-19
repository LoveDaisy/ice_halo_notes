# 产出 ../img/phi_class_grid.png（图 3「34 个方向映射类」）：行 = 漫谈(7) 的 6 个折叠类（e / b / R_z(±120°) / b·R_z(±120°) / S / b·S），
# 列分三组 = 三种可透射楔角（0° 平行族 6 格、60° 22° 族 12 格、90° 46° 族 16 格），每格写该类的最短代表光路、入出面对，有名有姓的
# 标晕名；正走 / 倒走互为一对的两格并成一个圆角框（中间 ⇄），自对偶的格子单独成框。34 = 10 对 × 2 + 14 个自对偶。
# 数据全部从 ../data/signature_table.md（enumerate_signatures.py 的产出）读：类 id、楔角、折叠类、入出面对、最短代表；配对关系
# 由「最短代表倒过来走归到哪一类」机械算出（_ch8_sim.class_id_of），不手填。类编号 A60-10 之类不进图面（正文不出现）。
# 读者要看出：① 34 = 6 + 12 + 16 是「6 种折叠 × 3 种楔」再按入出面对拆开的结果；② 常见晕只占少数几个格子，多数格子无名；
# ③ 60° 楔 + R_z(±120°) 折叠这一行有两格（3→3 与 3→7），本篇 §5–§6 讨论的是 3→7（`3-4-5-7`）那一格。
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from halo_notes.draw.style import DEFAULT_LIGHT
from halo_notes.draw.style.mapping import CJK_SANS

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch8_sim as S  # noqa: E402

OUT = CODE_DIR.parent / "img" / "phi_class_grid.png"
TABLE = CODE_DIR.parent / "data" / "signature_table.md"
WIDTH, HEIGHT, DPI = 2400, 1500, 200
PAL = DEFAULT_LIGHT
FONTS = ("Helvetica Neue", *CJK_SANS)
RATIO = 1.0                                     # 配对判定只看 (M, a, b)，与 h/a 无关；取 1 只是为了构造晶体

# 行：折叠类（用 ch7 的记号）；顺序从简单到复杂
FOLD_ROWS = (
    ("#12", "$e$", "不动"),
    ("#11", "$b$", "上下翻转"),
    ("#4/#6", "$R_z(\\pm120^\\circ)$", "绕 c 轴转 120°"),
    ("#3/#5", "$b\\,R_z(\\pm120^\\circ)$", "转 120° 再翻转"),
    ("#2/#8/#10", "$S$", "侧面镜反射"),
    ("#1/#7/#9", "$b\\,S$", "侧面镜反射再翻转"),
)
WEDGE_GROUPS = ((0, "0° 楔 · 平行族", 1, 300), (60, "60° 楔 · 22° 族", 3, 248), (90, "90° 楔 · 46° 族", 4, 248))   # (楔角, 标题, 本组最多几格, 格宽)
# 有名有姓的格子：最短代表 → 晕名（片晶取向 / 柱晶取向按 ch7 的口径——0° 列的 S / bS 两格柱晶下是「以太阳和映日点 / 以对日点和反日点
# 为中心的弥散」，这里缩写成「弥散（柱晶）」；60° / 90° 组是否弥散没有判据，不标；`3-4-5-7` 是本篇 §5–§6 的主角）
HALO_NAMES = {
    "1-2": "太阳原像",
    "1-2-1": "映日（片晶）/ 幻日环（柱晶）",
    "1-3-2": "幻日环（片晶）/ 弥散（柱晶）",
    "1-2-3-1": "映幻日环（片晶）/ 弥散（柱晶）",
    "1-3-4-2": "120° 幻日 / 映偕日弧",
    "1-2-3-4-1": "映 120° 幻日 / 特里克尔弧",
    "3-5": "22° 幻日 / 22° 晕",
    "3-1-5": "映幻日",
    "1-3": "环天顶弧",
    "3-1": "环地平弧",
    "3-4-5-7": "142° 幻日（本篇 §5–§6）",
}
STAR = "3-4-5-7"

# 版面（像素）
LABEL_W = 330          # 左侧行标签列
HEADER_H = 150         # 顶部组标题
LEGEND_H = 90          # 底部图例
CELL_H = 200
GAP = 14               # 组与组之间的额外间距
PAD = 8                # 格子内边距 / 框到格子边缘


def load_rows() -> list[dict]:
    """解析 signature_table.md 主表：类 id、楔角、折叠类、入出面对、最短代表。"""
    rows = []
    pat = re.compile(r"\| (A\d+-\d+) \| (\d+)° \| [^|]+ \| ([^|]+) \| ([^|]+) \| [^|]+ \| `([\d-]+)` \|")
    for line in TABLE.read_text().splitlines():
        m = pat.match(line)
        if m:
            cid, wedge, folds, pairs, path = m.groups()
            rows.append({"id": cid, "wedge": int(wedge), "folds": folds.strip(), "faces": pairs.strip(), "path": path})
    assert len(rows) == 34, len(rows)
    return rows


def pair_up(rows: list[dict]) -> dict[str, str]:
    """每类的倒走归属：最短代表反过来走属于哪一类（自对偶时是自己）。"""
    out = {}
    for r in rows:
        faces = tuple(int(x) for x in r["path"].split("-"))
        out[r["id"]] = S.class_id_of(RATIO, faces[::-1])
    for a, b in out.items():
        assert out[b] == a, (a, b)          # 配对必须对称
    return out


def layout(rows: list[dict], partner: dict[str, str]) -> list[dict]:
    """给每个格子分配 (行, 组, 组内列)：同一行同一组里先摆成对的（相邻），再摆自对偶的。"""
    cells = []
    for ri, (folds, _, _) in enumerate(FOLD_ROWS):
        for gi, (wedge, _, _, _) in enumerate(WEDGE_GROUPS):
            mine = [r for r in rows if r["folds"] == folds and r["wedge"] == wedge]
            placed: list[str] = []
            col = 0
            for r in sorted(mine, key=lambda r: (partner[r["id"]] == r["id"], r["id"])):
                if r["id"] in placed:
                    continue
                mate = partner[r["id"]]
                if mate != r["id"]:
                    m = next(x for x in mine if x["id"] == mate)
                    cells.append({**r, "row": ri, "group": gi, "col": col, "pair": "left"})
                    cells.append({**m, "row": ri, "group": gi, "col": col + 1, "pair": "right"})
                    placed += [r["id"], mate]
                    col += 2
                else:
                    cells.append({**r, "row": ri, "group": gi, "col": col, "pair": "self"})
                    placed.append(r["id"])
                    col += 1
    assert len(cells) == 34, len(cells)
    return cells


def group_x0(gi: int) -> float:
    x = LABEL_W
    for k in range(gi):
        x += WEDGE_GROUPS[k][2] * WEDGE_GROUPS[k][3] + GAP
    return x


def main() -> None:
    rows = load_rows()
    partner = pair_up(rows)
    n_pairs = sum(1 for a, b in partner.items() if a < b)
    n_self = sum(1 for a, b in partner.items() if a == b)
    assert (n_pairs, n_self) == (10, 14), (n_pairs, n_self)
    cells = layout(rows, partner)

    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(HEIGHT, 0)
    ax.set_axis_off()
    ink, soft, faint = PAL["ink"], PAL["ink_soft"], PAL["ink_faint"]

    def text(x, y, s, size, color=ink, ha="center", va="center", **kw):
        ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontfamily=list(FONTS), **kw)

    # ---- 组标题与分隔 ----
    for gi, (wedge, title, ncol, cw) in enumerate(WEDGE_GROUPS):
        x0, w = group_x0(gi), ncol * cw
        count = sum(1 for c in cells if c["group"] == gi)
        text(x0 + w / 2, HEADER_H * 0.42, title, 13.5, weight="bold")
        text(x0 + w / 2, HEADER_H * 0.72, f"{count} 类", 10.5, soft)
        ax.plot([x0 + PAD, x0 + w - PAD], [HEADER_H - 8, HEADER_H - 8], color=soft, lw=1.0)
    # ---- 行标签 ----
    for ri, (folds, latex, note) in enumerate(FOLD_ROWS):
        y = HEADER_H + ri * CELL_H + CELL_H / 2
        ax.text(LABEL_W - 40, y - 16, latex, fontsize=13, color=ink, ha="right", va="center")
        text(LABEL_W - 40, y + 16, note, 9.5, soft, ha="right")
        if ri:
            ax.plot([LABEL_W - 300, WIDTH - 40], [HEADER_H + ri * CELL_H, HEADER_H + ri * CELL_H], color=faint, lw=0.7)
    # ---- 格子 ----
    for c in cells:
        CELL_W = WEDGE_GROUPS[c["group"]][3]
        x0 = group_x0(c["group"]) + c["col"] * CELL_W
        y0 = HEADER_H + c["row"] * CELL_H
        star = c["path"] == STAR
        if c["pair"] in ("left", "self"):
            wbox = (2 if c["pair"] == "left" else 1) * CELL_W - 2 * PAD
            ax.add_patch(FancyBboxPatch((x0 + PAD, y0 + PAD), wbox, CELL_H - 2 * PAD, boxstyle="round,pad=0,rounding_size=14",
                                        facecolor=PAL["highlight"] if star else "none", alpha=0.35 if star else 1.0,
                                        edgecolor=PAL["accent_warm"] if star else (soft if c["pair"] == "left" else faint),
                                        linewidth=1.6 if star else (1.1 if c["pair"] == "left" else 0.9),
                                        linestyle="-" if c["pair"] == "left" or star else (0, (4, 3)), zorder=1))
        if c["pair"] == "left":
            text(x0 + CELL_W, y0 + CELL_H / 2, "⇄", 15, soft)
        cx = x0 + CELL_W / 2
        text(cx, y0 + CELL_H * 0.36, c["path"], 15.5, ink, weight="bold" if star else "normal")
        text(cx, y0 + CELL_H * 0.57, c["faces"].replace("→", " → "), 9.5, soft)
        if c["path"] in HALO_NAMES:
            text(cx, y0 + CELL_H * 0.77, HALO_NAMES[c["path"]], 9.2, PAL["accent_warm"] if star else soft)
    # ---- 图例 ----
    y = HEADER_H + len(FOLD_ROWS) * CELL_H + LEGEND_H * 0.55
    text(LABEL_W + 20, y, f"实线框里的两格 ⇄ 互为正走 / 倒走（{n_pairs} 对）；虚线框是自对偶的格子（{n_self} 个）；"
         f"格内是该类的最短代表光路与入出面对；黄底是本篇 §5–§6 讨论的那一格。", 10.5, soft, ha="left")
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
