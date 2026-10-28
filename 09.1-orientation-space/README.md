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

画的是与带面号柱晶姿态一一对应的**参数环面**，不是轴角球中的欧氏嵌入，也不以环面的欧氏面积表示 Haar 面积。图面已标明这一口径。表面与线条在同一射线命中点着色，避免背面透线；物理姿态仍由 `column_attitude` 唯一实现提供。静态几何，不使用 MC。

作者已允许沿实体几何方向继续；配色尚未定稿。`fig_column_torus.py` 默认保留上方原图；`--style chalk`（暖灰轻明暗、疏网格）与 `--style mineral`（青灰轻明暗、疏网格）各提供一个比较版本。非默认版本必须显式给出 `--output <本地 PNG 路径>`，例如：

```bash
uv run python 09.1-orientation-space/code/fig_column_torus.py --style chalk --output scratchpad/task-draw-ch9p1-ch10-figs/variants/column_chalk.png
```

未选变体仅留本地；同一相机、同一几何、同一强调圈，测试逐点核对命中位置一致。蓝/橙仍是原有的两种转动，降低的是背景面与网格的视觉权重，不以增加渐变或高光代替审美判断。

## 图 3 局部候选（待作者审看）

![图 3 候选：Parry 共享圈的局部邻域](img/parry_neighborhood.png)

上半部只画 **Parry 圈附近的局部参数邻域**，不是两张完整环面在轴角球里的嵌入。坐标为 `R(φ,a,b)=Rz(φ)Ry(−90°+a)Rz(b)`：`a=0` 是柱晶带、`b=0` 是 Lowitz 带，`a=b=0` 是共享 Parry 圈。径向代表 `a`、竖向代表 `b`；它们不是晶体在物理空间里的平移，也不表示姿态距离。

片晶不在这个小邻域中，因此另用下半部的**整圈索引**交代：Lowitz 全摆幅 `t` 的 `0°` 是片晶圈、`−90°` 是 Parry 圈、`+90°` 是原始点集中的另一交圈，`−180°` 和 `+180°` 接回同一翻转片晶圈。roll 锁 0 的半环 `t∈[−180°,0°]` 只交出 Parry 一圈；商 D₆ 后两交圈属于同一物理 Parry 族。上图局部的 `a=t+90°`，不能把整个索引强行嵌进那条窄带。

`test_parry_neighborhood.py` 以独立体轴约束、局部 Jacobian 满秩、D₆ 群元素及实际成图命中点反解参数核验。此方案是“局部相交 + 全摆幅索引”的拆分候选，是否足以代替原图题要求的全局直觉仍交作者判断，尚未插入正文。
