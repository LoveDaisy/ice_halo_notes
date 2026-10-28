---
type: note
---

# 09.1-orientation-space：重生成说明

本章在 git 里只有正文、被引用的插图、代码与小体积文本数据（config / provenance / csv / numbers.json 等）；原始渲染、中间数据、未被引用的图只留在本地，需要时按下面的入口重新生成。划界规则见仓库根 `AGENTS.md`「数据约定」。

## 重生成入口

```bash
uv sync
uv run python 09.1-orientation-space/code/regen.py --dry-run   # 列步骤：是否需要 Lumice、粗估墙钟
uv run python 09.1-orientation-space/code/regen.py             # 按序执行默认步骤
```

步骤表（顺序、参数、哪些默认不跑）的唯一权威是 `code/regen.py`，这里不复述。常用选项：`--only NAME …` 只跑某几步、`--skip-lumice` 只重画不需要 Lumice 的图、`--with-optional` 连同核验脚本等默认不跑的步骤。

## 如何验证

- `uv run pytest 09.1-orientation-space/code -q`：柱晶体轴约束、Parry 柱面朝上、两个角的周期性，以及环面表面方程和遮挡核验。
- 既有全篇核验仍以 `--only check_orientation_space` 执行；样图测试不能代替全篇核验或作者签核。

## 图 2a 风格样图（待作者审看）

![图 2a 候选：柱晶参数环面与 Parry 圈](img/column_torus.png)

这是重启后的少量样图，不是定稿，尚未插入正文。沿用系列白底、冰蓝实体与中文标注；蓝圈表示绕 c 轴自转，橙圈表示固定自转角的 Parry 族。字体/外观直接调用 ch8 `_ch8_plot.py`。

画的是与带面号柱晶姿态一一对应的**参数环面**，不是轴角球中的欧氏嵌入，也不以环面的欧氏面积表示 Haar 面积。图面已标明这一口径。表面与线条在同一射线命中点着色，避免背面透线；物理姿态仍由 `column_attitude` 唯一实现提供。静态几何，不使用 MC。作者未裁定前不扩展同风格批量成图。
