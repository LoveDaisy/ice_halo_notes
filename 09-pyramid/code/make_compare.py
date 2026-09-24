# 产出 scratchpad/task-draw-ch9-figs/compare.png（不入 git）：ch9 十一张正文插图的签核总览，每图一行——左侧缩略图，右侧图号 / 文件名 /
# 像素尺寸 / 正文图题（从正文 md 里按「图 N：」行读，不手抄）。给 owner 逐图目视签核用；图本身以 img/ 下的原图为准。
# 有备选版本的图（VARIANTS，返工 R2 图 2 的 A / B 两版）在该行左侧并排显示，各自标注。
from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

import _ch9_fig as F

FIGS = ("pyramid_faces", "direct_wedges", "closure_growth", "family_remainder", "isolated_ring", "panorama_triptych",
        "corridor_1_3", "crowded_profiles", "off_family_ring", "fold_edge_density", "plate_arcs")
BODY = F.CHAPTER / "锥晶的有限与无限.md"
VARIANTS = {"direct_wedges": (("direct_wedges", "A：R1 现状"), ("direct_wedges_b", "B：灰区只占轴上方，小晶体放大"))}
OUT = F.CHAPTER.parent / "scratchpad" / "task-draw-ch9-figs" / "compare.png"
ROW_PX, THUMB_W, TEXT_W, DPI = 520, 1100, 1100, 100
FONT = {"family": list(F.CHART_FONTS)}


def captions() -> dict[int, str]:
    out = {}
    for line in BODY.read_text().splitlines():
        m = re.match(r"图 (\d+)[：:]\s*(.*)", line)
        if m:
            out[int(m.group(1))] = m.group(2).replace("$", r"\$")      # 正文里的 $c$ 不按 mathtext 排
    return out


def wrap(text: str, width: int = 34) -> str:
    return "\n".join(text[i:i + width] for i in range(0, len(text), width))


def main(out: Path = OUT) -> Path:
    caps = captions()
    fig = plt.figure(figsize=((THUMB_W + TEXT_W) / DPI, ROW_PX * len(FIGS) / DPI), dpi=DPI)
    fig.patch.set_facecolor("white")
    n = len(FIGS)
    for i, name in enumerate(FIGS):
        y0 = 1 - (i + 1) / n
        versions = VARIANTS.get(name, ((name, None),))
        thumb_w = (THUMB_W / (THUMB_W + TEXT_W) - 0.02) / len(versions)
        size = "—"
        for k, (fname, tag) in enumerate(versions):
            path = F.IMG / f"{fname}.png"
            ax = fig.add_axes([0.01 + k * thumb_w, y0 + 0.05 / n, thumb_w - 0.005, (0.8 if tag else 0.9) / n])
            ax.set_axis_off()
            if path.exists():
                img = Image.open(path)
                ax.imshow(img)
                size = f"{img.width}×{img.height}"
            else:
                ax.text(0.5, 0.5, "（缺）", ha="center", va="center", fontsize=20, **FONT)
            if tag:
                fig.text(0.01 + (k + 0.5) * thumb_w, y0 + 0.92 / n, tag, ha="center", va="center", fontsize=12, fontweight="bold", **FONT)
        x = THUMB_W / (THUMB_W + TEXT_W) + 0.01
        fig.text(x, y0 + 0.85 / n, f"图 {i + 1}　{name}.png　{size}", fontsize=15, fontweight="bold", va="top", **FONT)
        fig.text(x, y0 + 0.62 / n, wrap(caps.get(i + 1, "（正文里没找到图题）")), fontsize=12, va="top", linespacing=1.5, **FONT)
        fig.add_artist(plt.Line2D([0, 1], [y0, y0], color="#cccccc", lw=0.8))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI)
    print(f"saved {out}")
    return out


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
