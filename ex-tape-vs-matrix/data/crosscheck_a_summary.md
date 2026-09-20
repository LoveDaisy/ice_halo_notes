# 互证 A（逐点）统计

由 `code/crosscheck_a.py` 产出（种子 0，`HexPrism.from_ratio(1.0)`，$n=1.31$）。角距离用 $2\arcsin(|\mathbf a-\mathbf b|/2)$。

## 1. A60-12（`3-5`，$M=I$）：本系列 $-R\Phi(-R^{-1}\mathbf S)$ vs TK1999 $\mathbf H(Ru_0,60°,\mathbf S)$

| 项 | 值 |
|---|---|
| 样本数（Haar 均匀 $R$ × $S^2$ 均匀 $\mathbf S$） | 1000 |
| 本系列可达 / Tape 可达 | 161 / 161 |
| 可达判定一致（`None`↔"no ray"） | 1000 / 1000 = 100.0% |
| 两侧都可达时最大角距离 (rad) | 2.278e-14 |
| 两侧都可达时平均角距离 (rad) | 6.426e-16 |
| 超阈值（> 1e-06 rad）样本数 | 0 |

## 2. A60-10（`3-4-5-7`，$M=R_{\mathbf c}(120°)$）片晶族：$RMR^{-1}=\mathrm{zrot}(120°)$，Rule-1 恒等式

| 项 | 值 |
|---|---|
| 样本数（$\phi\in[0,360)$，$\Sigma\in[-30,80]$） | 200 |
| $\max\|RMR^{-1}-\mathrm{zrot}(120°)\|_\infty$ | 7.216e-16 |
| 可达判定一致（$\Phi_{3457}$ 定义域 = $\Phi_{35}$ 定义域） | 200 / 200 |
| 两侧都可达的样本数 | 31 |
| $\mathbf H_{3457}$（本系列）vs $\mathrm{zrot}(120°)\mathbf H_{35}$（Tape + Rule 1）最大角距离 (rad) | 3.003e-15 |

## 3. A60-10 柱晶族负例：$RMR^{-1}$ 不是绕竖直的旋转

| 项 | 值 |
|---|---|
| 样本数（同一组 $(\phi,\Sigma)$ + 绕 c 轴自转 $\theta_{\mathrm{roll}}$） | 200 |
| $\angle(RMR^{-1}\mathbf k,\mathbf k)$ 的范围 (°) | [120.000000, 120.000000] |
| 两侧都可达的样本数 | 35 |
| 强行套 Rule 1：$\mathrm{zrot}(120°)\mathbf H_{35}$ vs 本系列 $\mathbf H_{3457}$ 的角距离 (°) min / mean / max | 17.512 / 88.451 / 150.247 |
| 本系列自己的共轭式 $RMR^{-1}\mathbf H_{35}$ vs $\mathbf H_{3457}$ 最大角距离 (rad) | 2.993e-15 |

解读：柱晶姿态下 $R\mathbf k$ 水平，$RMR^{-1}$ 是绕水平轴转 120°，$\mathbf k$ 被转出 120°——它不在 TK1999 的 $Z$（绕竖直旋转群）里，
Rule 1 不适用，atlas 里没有对象承载它；本系列的 $\Phi_{3457}=M\circ\Phi_{35}$ 不依赖 Rule 1，共轭式逐点成立。
「需要怎样补一个折叠才等价」：在 TK1999 的楔对象上追加一个固定在**晶体**（而非楔）上的正交算子 $M$，
光点公式变为 $\mathbf H=RMR^{-1}\,\mathbf F(u\mathbf N_0,u\mathbf X_0,\mathbf S)$——这正是本系列 signature 的 $M$ 维。
