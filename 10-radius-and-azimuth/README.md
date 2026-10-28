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

## ch10 新图（第八批，待作者审看）

图 2 的旋转动作直接加载 9.1 `_sun_rotation.py`，只在本章增加 `3–5` 出射方向与天空等距投影；不复制旋转物理。图 3a–3d 共用 `fig_plate_terrain.draw_base()` 与只读缓存 `base_terrain()`，实际绘图层的数组/域/色阶由测试逐点对照。图 3c 重构前后 PNG SHA256 相同，保留作者认可版。图 5 调用既有 Bravais/球面角距函数，临界处之后不延伸有效曲线。

### 图 2 · 绕太阳转，角距离不变

![图 2](img/solar_circle.png)

### 图 3a · 光学定义域与等值线

![图 3a](img/terrain_domain.png)

### 图 3b · 随机取向可到达全局最低点

![图 3b](img/random_terrain.png)

### 图 3d · 柱晶可取带包含赤道

![图 3d](img/column_terrain.png)

### 图 4 · 沿棱守恒与水平截面

![图 4](img/bravais_prism.png)

### 图 5 · 两把尺子

![图 5](img/parhelion_rulers.png)

### 图 6 · 上下切点的真实姿态

![图 6](img/tangent_direction.png)

图 4 的三段传播向量由有限六棱柱内 `3–5` 真光路产生，守恒的是 `k = n × 单位传播方向` 的竖直分量；水平截面直接投影同一条光路。图 6 的两个真实柱晶姿态分别给出上、下切点；太阳 20° 时下切点在地平线下，图中空心点仅标几何方向，不代表可见亮弧。`test_prism_figures.py` 从事件点、凸体半空间、两界面切向守恒及实际 Matplotlib 图元独立核验。

## 图 3c（作者第七轮认可，图版未改变）

![图 3c 候选：片晶纬线在同一球面地形上的最低点](img/plate_terrain.png)

这是重启后的少量样图，不是定稿，尚未插入正文。第六轮改为共享 `Camera` 的真正透视（方位 310°、仰角 12°、距离 8）：像素从同一相机位置发散射线，与单位球求近交点得到真实 `u`；曲线按球面法向与局部观察方向判遮挡，轮廓来自相机切线圈，三者使用同一投影。着色与等值线直接来自 `check_parhelion.dp`，不以手画椭圆替代数据。颜色只表示角距离，不表示亮度；留白为光学域外，不判定有限晶体中的走廊或能量。0°、20°、40°、60° 纬线的最低点由数值搜索生成，65° 纬线无解；全光学域均在所选相机的可见球面内。`uv run pytest 10-radius-and-azimuth/code/test_plate_terrain.py -q` 独立核验像平面逆投影、同长横杆的深度缩放、同像素近远交点遮挡、切线轮廓与 raster 边界，以及 Bravais 最低点。

复用 ch8 `_ch8_plot.py` 的字体/外观，沿用冰蓝色系作连续角距离标尺、橙色作纬线；正式图的配色通过 `P.PAL` 与脚本内少量语义 token 集中配置。后续 3a/3b/3d 须调用同一个地形生成器。作者第三轮审图选择 A 原版冰蓝，B/C 暖灰和青灰未被接受，不再沿它们扩展配图；本轮保留 A 色阶，但透视重渲已替换旧正射图，须重新交作者审看，不能继承此前签核。以下变体保留为历史比较入口，不是后续配色方向，也不表示其余图已获签核。

`fig_plate_terrain.py` 默认生成上方 A 冰蓝透视图；`--style chalk` 为暖灰单调色阶，`--style mineral` 为低饱和青灰单调色阶。非默认版本须显式指定 `--output <本地 PNG 路径>`，未选版本只留本地：

```bash
uv run python 10-radius-and-azimuth/code/fig_plate_terrain.py --style mineral --output scratchpad/task-draw-ch9p1-ch10-figs/variants/terrain_mineral.png
```

这里的渐变是**角距离标尺，不是环面上的灯光 shade**；三版调用同一个 `terrain()`，共用 `Normalize(21,53)`、等值线及最低点，不给球面额外打光。测试检查三套色阶的线性亮度严格单调。纬线、点、等值线及直接数字标签沿用原有语义，并随同一透视相机重投影，可不依靠辨色读数。
