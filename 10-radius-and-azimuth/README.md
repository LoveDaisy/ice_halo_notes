---
type: note
---

# 10-radius-and-azimuth：重生成说明

本章只跟踪正文、被引用的插图、代码和小体积文本数据。原始 Lumice 线性输出、缓存及未引用的图只留本地；MC 重渲不要求逐字节相同。划界规则见根目录 `AGENTS.md`。

## 重生成入口

```bash
uv sync
uv run python -m halo_notes.sim.fetch
uv run python 10-radius-and-azimuth/code/regen.py --dry-run
uv run python 10-radius-and-azimuth/code/regen.py
```

步骤表的唯一权威是 `code/regen.py`。`--only NAME …` 只跑指定步骤，`--skip-lumice` 跳过依赖仿真的步骤，`--with-optional` 包括既有数值/MC 核验。各绘图脚本支持 `--output <PNG>`，可在临时目录检验重生成而不覆盖正式图。

## 语义与验证

- 图 2 直接加载 9.1 的 `_sun_rotation.solar_orbit`，四帧仅画晶体、太阳转轴和观察方向之间的角距双箭头，不再另列天空整圆。圆弧来自两向量张成的大圆，再经真正的 perspective 相机投影；角距不是屏幕量角。
- 图 3a–3d 共用 `fig_plate_terrain.draw_base()` 与只读 `base_terrain()`：同一像素对应同一真实球面方向、光学定义域和角距离，逐点核对数组、掩码、色阶。3c 用临界 `h_c≈60.75°` 替代 60° 纬线，空心点只表示定义域闭包的掠入/掠出接触，透射趋零。3d 大图采用太阳 70°、纬度 ±20° 的半透明可取带，小图对比太阳 20°/45°/70°；叠层不更改底图值。
- 地形只陈述方向光学，不冒充有限晶体走廊或可见能量。片晶最低点由数值搜索产生，独立对照 Bravais；柱晶带用水平 c 轴姿态样本核验。色阶单调变暗，仅编码角距离，不加球面灯光改变数值颜色。
- 图 4 对照同一个有限六棱柱的正穿（0°）和斜穿（40°）：两组三维真光路各配同路水平投影，水平最小偏折从 21.84° 增到 36.32°。只在入射界面解释 `k=n×单位传播方向` 的竖直分量守恒与水平分量之比，不把冰内单位方向的竖直分量当守恒量。
- 图 5 为单幅透视球面图（相机方位 −32°、仰角 22°、距离 5）：两条经线从天顶经过太阳/幻日，落到赤道的单位方位方向（不是球内垂足）；球心 O 向太阳/幻日画两条半径，在两半径张成的三维平面内以 0.36 球半径的双箭头弧标 D，球面最短大圆弧退为细辅助线；赤道弧量 Δφ，同高度纬线小圆仅作点线辅助。40° 时为 27.63° / 36.32°；图面不列推导公式。所有曲线来自同一个单位球几何对象，独立核验过球心平面、端点、单位范数和球面长度，并把实际图元反投回球面或球心角平面检查；角距弧两端分别落在两半径、到 O 等距、张角与向量内积一致，双箭头绑定真实弧端，临界之后不生成有效几何。
- 图 6 固定太阳 25°，正穿和斜穿 β=40°/55° 的真实水平柱晶光路对应三个半径；天空采用方位等距投影，角距圈是真圆，下切点高度 3.16°。每个水平轴方向各取最小偏折，独立检查姿态→天空映射秩一、核方向二阶项非零及有向面积变号，才连接为切弧聚焦轨迹；只展示 |β|≤55° 一段，不表示光强或可见截止。等距投影复用图 2 的 `sky_xy`，不保留两份坐标实现。
- 图 1/7 用 release v4.6.1、580 nm、0.2° 日面；三族固定同一高度参数 3.0 的六棱柱，只改变取向，避免高太阳下薄片的直接 `3–5` 走廊被底面截断。过滤器仅取 `3–5` 及 PBD 晶体对称像，不混入 Parry 或底面反射。每景同一批光线输出全天 rectangular 取证图和太阳中心等面积显示图，两投影总原始 Y 一致。12 景各 20M 光线，CPU 4 workers 实测累计 54.147 秒；seed 为 null，不承诺 MC 重渲逐字节相同。
- 图 1 的单色光用伪彩区分族，同族四高度共用曝光；显示有单调拉伸与削顶，不用于族间亮度比较。所有取数直接读 raw XYZ 的 Y / emitted_energy，不经过显示曝光、阈值或额外 cos(纬度) 权重。现有 `sim.energy.pixel_energy` 接口只接收 8-bit sRGB，这里没有对 raw XYZ 再作该解码。
- 图 7 共用图 1 的 20° 柱晶数据；图面只看上切弧。完整上下像有两个切点，单独上弧有一个；更外的圈上出现两侧亮峰及连续弱光，不能说只剩两个光点。图面标解析几何上确界 50.06262°，掠射时透射趋零，不以有限 MC 最远像素或曝光阈值冒充可见截止。最远非零像素仅留在 `data/column_sky_evidence.json` 作证据；显示原始数据、曝光和上下支裁窗未改。

已有原始数组时离线重画（不会启动 Lumice）：

```bash
uv run python 10-radius-and-azimuth/code/fig_sky_comparison.py --replot --output /tmp/sky-comparison.png
uv run python 10-radius-and-azimuth/code/fig_column_sky.py --replot --output /tmp/column-sky.png
```

指定 `--output` 后派生 JSON 写在图片旁，不改章内图和默认派生元数据。去掉 `--replot` 会在缓存缺失或配置失配时补渲；`--render` 强制重渲。低成本探针入口是 `fig_sky_comparison.py --probe`（0.02° 日面），与正式配置分开记录。

```bash
uv run pytest 10-radius-and-azimuth/code -q
uv run python 10-radius-and-azimuth/code/check_parhelion.py
uv run python 10-radius-and-azimuth/code/check_parhelion_lumice.py
uv run python -m halo_notes.repo.layout check-tree
```

`test_prism_figures.py` 独立检查真实事件点、凸体半空间、两界面切向守恒及实际 Matplotlib 图元；`test_ch10_geometry.py` 读取实际四图 raster、独立 Rodrigues 转动及临界有效域。`test_*_revision.py` 检查本轮生成路径的临界闭包、可取带叠层、真实两种量角与聚焦轨迹。缺原始渲染的测试按 `local_data` 约定跳过，不能把 skip 写成 MC 已通过。

## 第十一批十图预览（仅图 5 待复审）

本批只局部返工图 5：保留单幅透视球面，增加球心 O 的两条半径与夹角双箭头，球面大圆退为辅助。9.1 八图与 ch10 其余九图保持作者认可的原文件哈希；拼版因图 5 改版而更新，不使未改图片的真实认可失效。图 8 已裁定省略。作者已自行删去「附录 F」回引；球面三角推导尚待作者写作，本任务不代写。图 5 新版未获视觉认可前不插正文图片、不进入代码评审或结项。

![ch10 十图拼版](img/compare_radius.png)

拼版只供整体比较；下面各图可打开原尺寸。`data/compare_radius.json` 由拼版脚本生成，记录逐图文件、SHA256 与图 8 省略状态；它不是作者签核表。作者原始裁定、当时图版和本轮最终状态记录在本任务 scratchpad 中。

### 图 1 · 同一光路，三种姿态族

![图 1](img/sky_comparison.png)

### 图 2 · 绕太阳转，角距离不变

![图 2](img/solar_circle.png)

### 图 3a · 光学定义域与等值线

![图 3a](img/terrain_domain.png)

### 图 3b · 随机取向可到达全局最低点

![图 3b](img/random_terrain.png)

### 图 3c · 片晶纬线与各自最低点

![图 3c](img/plate_terrain.png)

透视参数沿作者认可版：相机方位 310°、仰角 12°、距离 8；像素射线从同一相机点出发，与单位球求近交点得到真实 `u`；曲线按局部观察方向判遮挡，轮廓来自相机切线圈。全光学域在相机可见球面内。

### 图 3d · 柱晶可取带包含赤道

![图 3d](img/column_terrain.png)

### 图 4 · 沿棱守恒与水平截面

![图 4](img/bravais_prism.png)

### 图 5 · 角距离与方位差，两把尺子

![图 5](img/parhelion_rulers.png)

### 图 6 · 正穿、斜穿与切弧的不同半径

![图 6](img/tangent_direction.png)

### 图 7 · 同心角距圈与真实亮段

![图 7](img/column_sky.png)

## 外观入口

字体、底色和基础色板沿用 ch8 `_ch8_plot.py` / 系列 `P.PAL`。几何与定量图分别使用少量章级语义 token；文字、直接标签、线型和点型共同区分含义，不只靠颜色。图 3c 历史 `chalk` / `mineral` 变体仍可通过显式 `--output` 重生，但作者选择的是原版冰蓝，后续三幅底图不沿未选配色扩展；这些变体不是并列权威图版。
