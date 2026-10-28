---
type: note
---

# 09.1-orientation-space：重生成说明

本章只跟踪正文、被 Markdown 引用的图、代码及小体积文本；其他产物按根目录 `AGENTS.md` 的划界规则留在本地。

## 重生成入口

```bash
uv sync
uv run python 09.1-orientation-space/code/regen.py --dry-run
uv run python 09.1-orientation-space/code/regen.py
uv run pytest 09.1-orientation-space/code -q
```

步骤顺序与默认开关的唯一权威是 `code/regen.py`。`--only NAME …` 指定步骤，`--with-optional` 包含全篇核验及历史构图对照。脚本按 `__file__` 定位，均可用 `--output <PNG>` 隔离出图；不依赖 Lumice。

## 第六批：8 张图版，全部待重新审看

![第六批比较版](img/compare_orientation.png)

本批按作者第六轮意见改版：1a/b 合并为图 1；所有当前三维图改用真实透视；2a/b 各一张环面；3 保留 B 错层但重标 Parry；4a 只留点云；5a 五帧；5b 换为局部辅助候选。**旧版本意见不是新图版签核，当前全部 pending**。正文只同步获授权的图题/编号，不插入尚未签核图片；作者原有两行论述补丁保持未提交。

| 图号 | 原尺寸图 | 核心语义与证据 |
|---|---|---|
| 1 | [轴角球与姿态](img/axis_angle_ball.png) | 一条直径逐点对应五个晶体；±180° 的旋转矩阵与带面号顶点一致；跨边界时实际旋转连续 |
| 2a | [柱晶环面](img/column_torus.png) | 两个周期自由度，突出一个 Parry 原始圈，不声称另一个原始圈不存在 |
| 2b | [Lowitz 环面](img/plate_lowitz.png) | 同一镜头与图 3 参数化；片晶在外赤道，Parry 的两个原始圈在上下；被面遮挡的圈以明确虚线补示 |
| 3 | [B 错层剖切](img/tori_section.png) | 两母圆交点绕轴产生两原始交圈；下圈 Parry，上圈经晶体对称与之对应 |
| 4a | [方向点云](img/euler_sampling.png) | 两边各 1440 个 c 轴方向，同点大小/视角，只显示方向而非整个 SO(3) |
| 4b | [相对密度](img/euler_density.png) | `2/(π sinβ)`，不将无穷大截成有限峰；本批保留原图 |
| 5a | [绕太阳转](img/sun_rotation.png) | 五帧世界系与晶体系逐列对应；世界左乘旋转、体坐标太阳方向不变 |
| 5b | [参考起点坏点：局部候选](img/angle_fibers.png) | 沿两条经线趋近反向点，最短参考姿态的极限相差绕太阳轴 90°；两者的 u 完全相同 |

![图 1](img/axis_angle_ball.png)

![图 2a](img/column_torus.png)

![图 2b](img/plate_lowitz.png)

![图 3](img/tori_section.png)

![图 4a](img/euler_sampling.png)

![图 4b](img/euler_density.png)

![图 5a](img/sun_rotation.png)

![图 5b 局部辅助候选](img/angle_fibers.png)

### 图 5b 的待裁定边界

上一版“球面挂小钟 + 卷绕曲线”没有帮助作者理解。本批不在旧图上堆注释，改为一个具体反例：沿 A/B 两路趋近同一个反向点，参考晶体姿态没有共同极限。它**只解释最短转动选法为何出问题**，不冒充“任何选法都不能全局光滑”的证明，也不声称已交付旧占位要求的整个纤维丛/卷绕图。

建议作者选择：保留这个局部辅助图并另行确认图题；或删图，以正文一句话和附录代替。当前未代作决定，正文图 5b 占位原样保留。卷绕数 +2 仍由 `reference_loop`、既有核验脚本和独立测试核对，但不是本图画面所证明的内容。

可选图 **4c** 同样未裁定：未画、未删占位。真实墨卡托纬线并非等距，不能按占位画假地图；去留与文字处置交作者。

## 相机、配色与验证

- 当前空间图复用 `halo_notes.draw.projection.Camera` 的位置/投影约定。球面轮廓由透视切线锥决定；可见性使用每点指向相机的向量。环面表面由同一相机点发散射线求最近命中，不是最终二维缩放。ch10 图 3c 同根因同步改正。
- 图 2a/b/3 是参数与集合关系示意，**不是整个 SO(3) 在三维欧氏空间里的忠实嵌入**，也不用表面的面积表示 Haar 测度。2b 的虚线是明确的遮挡线；3 的虚线只补切口处完整交圈，不透画背面。
- 图 3 两显示母圆的半径为 1，中心半径为 2.5 / 1.7，交圈半径为 2.1、高度 `±sqrt(0.84)`。显示母圆角经重参数化映到物理角；独立旋转约束验证 Lowitz 的 `R e₂` 水平、柱晶的 `R e₃` 水平，交集为 `R e₁=±e_z`。
- 图 4a Haar 样本种子 `20261028`；欧拉网格 α 步长 9°、β 中点步长 5°。图 4b 另由数值 Jacobian 和极冠积分验证。
- 图 5a 的唯一绕太阳动作在 `_sun_rotation.py`；ch10 后续薄调用，不重复实现。太阳箭头是方向示意，不是真实光路。
- 颜色仍来自 `_ch8_plot.PAL` / 系列 `PRESETS`。概念图的 `INK/BLUE/ORANGE/EDGE/SURFACE` 在 `_orientation_fig.py`；环面材质与强调圈在环面渲染脚本的少量语义参数中配置。晶体沿用系列 `ice_filled`，曲面沿用作者偏好的冰蓝 mesh；不引入全仓第二套配色系统。
- `test_concept_figures.py` 核验真实成图面板/晶体姿态以及深度缩放、球面切线与可见性；环面测试以独立四次方程全部实根对照射线遮挡，不能只比较生成器自己的声明。
- `make_compare.py` 从本章 PNG 生成比较版和 `data/compare_orientation.json`；SHA256 仅绑定本次版本，**不是作者签核**。图改后重新生成 compare，不复用旧 hash。

## 非当前交付的历史构图

以下仅供回看设计演变，默认 regen 不生成，不在本批 8 图清单中。图 3 唯一主候选仍为 B 错层。

![历史局部邻域构图](img/parry_neighborhood.png)

![开窗构图对照](img/intersecting_tori.png)

局部邻域图描述 `R(φ,a,b)=Rz(φ)Ry(−90°+a)Rz(b)`，不是完整环面；它是旧版历史参照，不作为本批透视图交付。开窗版与主图共用曲面/物理姿态及透视射线实现。若需回看平齐切口，用 `fig_tori_section.py --variant aligned --output <PNG>`，不覆盖 B 主图。
