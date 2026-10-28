---
type: note
---

# 10-radius-and-azimuth：重生成说明

本章在 git 里只有正文、被引用的插图、代码与小体积文本数据（config / provenance / csv / numbers.json 等）；原始渲染、中间数据、未被引用的图只留在本地，需要时按下面的入口重新生成。划界规则见仓库根 `AGENTS.md`「数据约定」。

## 重生成入口

```bash
uv sync
uv run python -m halo_notes.sim.fetch            # 按钉住版本拉 Lumice release 二进制到 .lumice/（首次）
uv run python 10-radius-and-azimuth/code/regen.py --dry-run   # 列步骤：是否需要 Lumice、粗估墙钟
uv run python 10-radius-and-azimuth/code/regen.py             # 按序执行默认步骤
```

步骤表（顺序、参数、哪些默认不跑）的唯一权威是 `code/regen.py`，这里不复述。常用选项：`--only NAME …` 只跑某几步、`--skip-lumice` 只重画不需要 Lumice 的图、`--with-optional` 连同核验脚本等默认不跑的步骤。

## 如何验证

- `uv run pytest 10-radius-and-azimuth/code -q`：地形逐像素定义域、纬线最低点对 Bravais 闭式、沿棱分量守恒、临界后空域及全定义域可见性核验。
- 既有 `check_parhelion` / `check_parhelion_lumice` 保持为可选核验项；本次两幅风格样图不需要 Lumice，不代表后续天象图已完成 MC 验证。

## 图 3c 风格样图（待作者审看）

![图 3c 候选：片晶纬线在同一球面地形上的最低点](img/plate_terrain.png)

这是重启后的少量样图，不是定稿，尚未插入正文。正射球面上每个像素对应一个真实 `u`；着色与等值线直接来自 `check_parhelion.dp`，不以手画椭圆替代数据。颜色只表示角距离，不表示亮度；留白为光学域外，不判定有限晶体中的走廊或能量。0°、20°、40°、60° 纬线的最低点由数值搜索生成，65° 纬线无解；全光学域均在所选可见半球内。

复用 ch8 `_ch8_plot.py` 的字体/外观，沿用冰蓝色系作连续角距离标尺、橙色作纬线。后续 3a/3b/3d 须调用同一个地形生成器。作者第三轮审图选择 A 原版冰蓝，B/C 暖灰和青灰未被接受，不再沿它们扩展配图；原图保持不变。以下变体保留为历史比较入口，不是后续配色方向，也不表示其余图已获签核。

`fig_plate_terrain.py` 默认保留上方原图；`--style chalk` 为暖灰单调色阶，`--style mineral` 为低饱和青灰单调色阶。非默认版本须显式指定 `--output <本地 PNG 路径>`，未选版本只留本地：

```bash
uv run python 10-radius-and-azimuth/code/fig_plate_terrain.py --style mineral --output scratchpad/task-draw-ch9p1-ch10-figs/variants/terrain_mineral.png
```

这里的渐变是**角距离标尺，不是环面上的灯光 shade**；三版调用同一个 `terrain()`，共用 `Normalize(21,53)`、等值线及最低点，不给球面额外打光。新增测试检查三套色阶的线性亮度严格单调。纬线、点、等值线及直接数字标签保持原样，可不依靠辨色读数。
