# 系列路线图

> 2026-09-11 起草，2026-09-12 定下正向深化五章（7–11）；2026-09-20 ch7/ch8 发表，起 ch9 与番外「Tape 光点法 vs 矩阵法」的写作准备（scrum `ch9-prep` / `ex-tape-prep`）。章节内容由作者定，本文只固定结构与线索；「需要的能力」一列是 `halo_notes/` 的需求清单来源。理论骨架本身见 [framework.md](framework.md)。
> 状态：`published` / `draft`（正文已成、未发表）/ `outline` / `idea`（只有一句话）/ `todo`（已决定写、未起提纲）。

## 主线

整个系列分两部分：**正向问题**（给定冰晶与光路 → 天上出现什么）与**反向问题**（看到什么 → 反推冰晶与光路）。0–6 章是正向问题的第一遍叙述；写作时思路尚不成熟，几处没讲透。7–11 章用群论 / 等变映射 / 奇点 / 姿态分布的语言把正向问题重新提炼一遍，然后转入反向问题。

写法约定：**不写「框架阐述」章。** 每章锚定一个前几章已经埋下、尚未兑现的悬念，用一个具体结果把它收口；框架只作为结果的副产品浮现。每章配一份计算机核验（群论论证只给上界，可达性 / TIR / 亮度都在论证之外，穷举才把结论钉死）。

正向深化的三条主线说明（细节见 framework.md）：

1. **结构 vs 巧合**：六棱柱「无限多光路 → 12 个反射矩阵 → 6 类晕」是晶体学巧合（镜面夹角 60°/90° 恰是 Coxeter 角）；等变分解 $\Phi = M\circ W$、signature 分类、两种聚光机制才是结构。锥晶（ch9）是分辨二者的试金石。
2. **半径归光路，方位归姿态**：出射点到太阳的角距离只由晶体坐标系里的偏折角决定，姿态分布只决定每个太阳同心圆的方位填充。ch10 讲半径，ch11 讲方位。
3. **反问题是线性反问题**：前向模型对姿态测度 $\rho$ 线性，所有非线性都在光路侧。Hough 投票 = 伴随算子（backprojection），可微渲染 = 同一算子的正则化求解。这是 ch11 → 第二部分的过渡。

正向深化之所以先于反向问题，不只是叙事顺序：它把方向映射收成可控的假设空间——六棱柱是精确有限类（34），锥晶是「9 个直接楔家族 + 显式字长截断」——直接缩小反向问题的假设空间。

## 第一部分：正向问题

### 已发表（第一遍叙述）

| 章 | 目录 | 标题 | 核心内容 | 状态 |
|---|---|---|---|---|
| 0 | `00-introduction` | 风起青萍之末 | 动机：光路分类 | published |
| 1 | `01-symmetry` | 迷镜千幻不离宗 | 晶体对称性 → 光路等价类（C6 / D6） | published |
| 2 | `02-raypath-enumeration` | 计算机遍历、搜索、优化 | 枚举所有光路，几何可行性判定 | published |
| 3 | `03-parallel-raypaths` | 平行光路的各种弧和晕 | 内反射矩阵、12 种矩阵 → 6 类晕 | published |
| 4 | `04-render-equation` | 冰晕模拟仿真的朴素思路 | 仿真 = 渲染方程的积分 | published |
| 5 | `05-rotation-3d` | 三维旋转 | SO(3)、四元数、球面均匀采样 | published |
| 6 | `06-monte-carlo-vs-integration` | 蒙特卡洛 vs. 直接积分 | 采样与直接积分两条路 | published |

### 正向问题深化（7–11）

| 章 | 目录（拟） | 标题（拟） | 锚定的悬念 | 核心结果 | 计算机核验交付 | 需要的能力 | 状态 |
|---|---|---|---|---|---|---|---|
| 7 | `07-reflection-group` | 为什么恰好是十二个 | ch3 结尾「这些结果和整体变换矩阵有什么联系？且听下回分解」 | 12 = 六棱柱镜面生成群 $D_{3h}$；6 类 = 该群下的共轭类（特征值 / Jordan 型是 O(3) 共轭不变量，太粗：#11 会并进 #2）；4 锐 2 散 ⇔ 是否与 $R_z$ 对易；$\dim(\text{晕})=\dim Q-\dim\mathrm{Stab}$。定理假设（镜面夹角 60°/90°）要写明，给 ch9 埋线 | 群闭包 + 共轭类 + 对易判据（`07-reflection-group/code/check_group.py` 已通过） | `math.group`：$D_{3h}$ 作用与共轭类 | published（2026-09-14，发表题「十二种矩阵背后的数学结构」） |
| 8 | `08-wedge-times-fold` | 三种楔子、十二种折叠 | ch2/ch3「进一步的对称性」；ch3 楔角光路图；ch3 工作笔记「推导一下楔角光路」 | $\Phi_P = M\circ W_{\mathbf n_a,\,M^{-1}\mathbf n_b}$（Snell 的旋转等变性）；$M^{-1}\mathbf n_b$ 仍是面法向 ⇒ 六棱柱任意长度光路 = {0°, 60°, 90°} 三种有效楔 × 12 种折叠（120° 楔全反射死角）；平行光路 = $W=I$ 退化；与 Tape 的 wedge theory / Tricker 1973 万花筒式逐次镜像合流（Tricker 直接对应 $W=I,\Phi=M$，一般 $M\circ W$ 是本章的合成）；signature $[M,\mathbf n_a,M^{-1}\mathbf n_b]/\text{对称}$ 做穷举分类；商掉 $D_{6h}$ 后方向映射至多 34 类（0°/60°/90° 族 6/12/16，`check_signature.py` 已通过）；A60-10（`3-4-5-7`）渲染出带 142° 锐边的宽鼓包 = 楔角机制（与 22° 幻日同类，当年叫「142° 幻日」没叫错东西）；Liljequist 幻日特指其外侧的窄峰 = A0-02 平行光路机制（`3-5-6-7-3`，与 `1-3-2` 同 Φ 定义域窄），对截面形状敏感（锐边不动、窄峰摊平；为什么留后篇） | 上界：signature 类数（已通过）；下界：枚举器给可达类数（已通过：$h/a\ge0.5$ 时 34 类全可达，片晶 28，`data/signature_table.md`）；ch3 ground truth 93 条对表（已通过，`data/ground_truth_signature.md`） | `signature`：规范型（已交付 `halo_notes.math.signature`）；ch2 枚举器 python 复活（已交付，现由 `lumice_integral.geometry.enumerate` 提供） | published（2026-09-20，发表题「楔角光路」） |
| 9 | `09-pyramid` | 锥晶：结构还是巧合 | ch7 定理的假设 | 锥面法向与 c 轴夹 62.0°（由 $c/a=1.6288$ 算出）；10 个镜面两两夹角 {28.0, 52.4, 56.0, 60, 62.0, 63.8, 80.2, 90} 六个不在三维有限反射群（$A_3/B_3/H_3$）允许集 {36, 45, 60, 72, 90} 内 ⇒ 镜面群无限（严格，对 $c/a$ 舍入不敏感），矩阵数随字长爆炸（1, 11, 70, 372, 1884, …）；$\Phi=M\circ W$ 与 signature 幸存，但有限性**没有回来**（TIR、几何可达性都不封顶，见后）；三层对象要分清：直接楔（$M=I$，两个物理面）给 9 个直接楔角 = 9 个经典半径；折叠楔（$M\ne I$）的楔角与精确 $\Phi$ 类无限（六棱柱的折叠楔角不跑出直接楔角表，锥晶的会）；实际口径是 $L^\ast=6$、±0.5° 归族下 9 族的可达性与能量；同一公式 $\cos A=-\langle\mathbf n_a,\mathbf n_b\rangle$ 扫 20 个面得 9 个可透射楔角 0/28.0/52.4/56.0/60/62.0/63.8/80.2/90 ⇔ 平行、9°、18°、20°、22°、23°、24°、35°、46° 晕；Tape 的「Angle x」在此只是参数 $c/a$。**篇幅卡在四样交付**：增长对照表、9 个楔角推导、加字长上限的 signature 计数、一两个 odd-radius 晕实例；完整目录不进正文。精确 $\Phi$ 类数随字长不收敛（2° 网格 $L=2..7$：13/76/328/925/2247/4980），「全类表」改为「9 族可达性 + 代表光路表」并声明截断 $L^\ast=6$（定理 7′） | 增长表 + 楔角表（`09-pyramid/code/check_pyramid.py` 已通过）；加字长上限的 9 族可达性表（`09-pyramid/code/enumerate_signatures.py` → `data/signature_table.md` 已通过，四档 9 族全可达）+ Lumice `analyze` 能量互证（`code/analyze_energy.py` → `data/energy_table.md`，族级 0 违反） | `geometry.polyhedron`：一般凸多面体的面相交可达性（已交付，`lumice_integral.geometry.Pyramid`）；`sim`：锥晶 config（已交付，`halo_notes.sim.config.pyramid_crystal_from_geometry`，面编号 / 单位换算已实测钉死） | outline（2026-09-20 提纲待作者 review；scrum `ch9-prep` 子任务 odd-radius 实例手选 blocked，待作者裁定） |
| 10 | `10-two-focusing-mechanisms` | 两种聚光 | ch3「明亮凝聚」的说法不严谨 | 纤维化定理：$SO(3)\cong$ 以「太阳在晶体系中的方向 $\mathbf u$」为底的圆丛，$\angle(\mathbf x,\mathbf s)=D_P(\mathbf u)$ 与姿态无关（两章共用接口）；径向部分：dimension collapse（$DF$ 沿某方向恒为零，对称性）vs Jacobian focusing（$DF$ 只在特殊姿态降秩，奇点）；最小偏折 = fold caustic，$I\sim 1/\sqrt{D-D_{\min}}$；Tape 1980 的 halo function 奇点语言；Können 1983 在五个理想化假设下已有近晕角解析强度与 halocaustic 形状，本章新增的是把它放回任意 $\rho$ 与光路权重的统一 pushforward；$\mu_{\rm sky}=F_*[\rho\,w\,dq]$ 就是 ch4 的渲染方程，ch6 是算它的两条路 | 22° 晕的 $F$、$DF$ 数值 + 仿真径向剖面对照 | `math`：$D_P(\mathbf u)$ 及其 Jacobian | todo |
| 11 | `11-orientation-to-halo` | 姿态给方位 | ch5 的 SO(3) / 四元数至此才有用武之地；draft 里「离散冲激被姿态展开成弧」的比喻 | 方位部分：$\rho$ 均匀时天空图案 = 太阳盘与带状核 $f(D)$ 的球面卷积（比喻严格成立）；非均匀时是纤维化积分，不是天空上的卷积；真正的卷积核在 $SO(3)$ 上（$\rho=\rho_0 * k_\sigma$），天空上的模糊是 $F$ 推过去的像，$DF$ 大处糊得多；五个标准姿态族（随机 / 片 / 柱 / Parry / Lowitz）作为 $SO(3)$ 子流形，同一光路 × 五族 = 五种晕；$\dim(\text{晕})=\dim Q-\dim(\text{纤维})$ 是 ch7 稳定子公式的一般化。**结尾**：前向模型对 $\rho$ 线性 ⇒ 反问题是线性反问题，Hough = 伴随算子，参数化反演 vs 非参数投票两条路预告 | 同一条 3-5 光路 × 五个姿态族的仿真并排；倾角扩散与 $DF$ 的模糊对照 | `math`：$SO(3)$ 上的分布族与群卷积；`sim`：姿态族参数化 | todo |

**核心交付物是一张表：行 = 光路类（ch7–9 给），列 = 姿态族（ch11 给），格子里的形状由 $(F, DF)$ 裁定（ch10）。** 锥晶版的第一列已有探针数据（explore `pyramid-orientation-boost`，2026-09-20：默认档 × {plate, column, Parry} × 太阳 {10°, 30°} 的 9 族 + 族外能量表与冒头类渲染，`scratchpad/explore-pyramid-orientation-boost/data/`，不入 git）；结论：姿态改变的是族内的塌陷而非族外的放大，plate 10° 下一条 60.7° 楔角的族外光路（`18-16-25-23`）压过 18°/23° 两族——ch9 尾声留一句钩子，ch10/11 起章时接手。 反向问题就是「给一张天空图，找哪些格子亮、亮多少」。

## 第二部分：反向问题

| 章 | 目录 | 标题 | 核心内容 | 需要的能力 | 状态 |
|---|---|---|---|---|---|
| 12 | `12-halo-detection` | 变换法探测冰晕 | Hough 思路：亮区 → 姿态空间投票 → 高密度区 = 可能姿态。ch11 已给出其数学身份：线性算子 $\mathcal A_P$ 的伴随（backprojection） | 正向仿真的 python 接口（姿态 → 出射方向）；姿态空间离散化（番外「球面网格」）；峰值检测；实拍照片输入 | outline |
| 13 | | 可微渲染（拟） | 同一线性反问题的正则化求解：参数化姿态族 + 梯度优化；与 Hough 投票对比。原「Differentiable Render」占位名下的想法 | 可微的正向模型；姿态族参数化（ch11） | idea |

## 番外

番外不占主线章号。落点：工具类番外放在 ch11 与 ch12 之间（反向问题的姿态空间离散化正好需要它们）；历史番外放在 ch8 之后当过场。

| 标题（拟） | 来源 | 核心内容 | 需要的能力 | 落点 | 状态 |
|---|---|---|---|---|---|
| 球面上的分布 | ch5 存档提纲 | 球面均匀分布按面积算、经纬参数化的奇点、最近邻距离分布、大指数的数值稳定性、球面高斯；ch11 之后升级为 $SO(3)$ 上的分布族 | S² / S³ 采样、解析 pdf | ch11 → ch12 之间 | idea |
| 球面网格系统 | ch5 存档提纲「单独开一篇？」 | 球面 / 姿态空间离散化方案 | 与 ch12 的姿态空间离散化共用 | ch11 → ch12 之间 | idea |
| Tape 光点法 vs 矩阵法 | 2026-09-11 draft 讨论；2026-09-21 讨论板改口径 | 三块拼图：Tricker 1973 万花筒只有折叠（$W=I,\Phi=M$）→ Tape 的 22° 幻日只有楔（$M=I,\Phi=W$，取向 → 光点映射与 atlas）→ 本系列 A60-10 楔 × 折叠（$\Phi=M\circ W$）。核心命题：Tape 按「楔 + 取向」组织纯折射晕，本系列按「楔 $W$ + 折叠 $M$」组织完整光路；`3-5` 只是翻译校准，A60-10 的片晶正例 / 柱晶反例才是主角。双出口：主出口 ch9（直接楔有限，加入折叠 $M$ 后怎样），次出口 ch10（Tape 1980 → 1982/1983 → Können 1983 的 caustic / 强度文献链，本篇不展开）。写法：锚具体实例双写，不写成综述；Tricker 只做历史前情（一张镜像图 + 一句翻译 + 一句边界）；文献忠实度由作者把关 | 数值互证脚本 `ex-tape-vs-matrix/code/`：`tape_halo_function.py`（Tape 侧两条链路）、`crosscheck_bridge.py`（翻译层）、`crosscheck_a.py`（逐点）、`crosscheck_b.py`（图级） | ch8 之后（2026-09-20 裁定：先于 ch9 动笔） | outline（提纲待作者 review） |
| ~~锥晶晕目录~~ | ch9 溢出 | 已并入 ch9 `data/` 附录（`09-pyramid/data/signature_table.md` 9 族汇总 + `signature_table_<tier>.csv` / `raypaths_<tier>.csv` 逐类逐光路清单），不另立番外；穷举不收敛（定理 6 / 7′），「完整目录」本身不是良定义的有限目标 | — | — | absorbed（2026-09-20） |
| ~~Jordan 型是条歧路~~ | ch3 工作笔记 | 已被 ch7 §1「相同的特征值，不同的晕」整段吸收（#2 vs #11 特征值相同、晕不同；用错群不变量就合并东西），不再单立 | — | — | absorbed（2026-09-20） |

## 章号与目录名

- 目录名 `NN-slug` 的 `NN` = **发表顺序**。正向深化五章占 07–11，`07-halo-detection` 已在 ch7 bootstrap 时改名为 `12-halo-detection`（只改目录名不动 md 文件名，wikilink 不受影响）。
- 番外目录名用 `ex-<slug>`（2026-09-20 起用：`ex-tape-vs-matrix`）。

## `halo_notes/` 需求汇总（由各章「需要的能力」列聚合）

| 模块 | 能力 | 来源 |
|---|---|---|
| `draw` | 统一风格的晶体示意图：3D 线框 / 2D 截面 / 光路 / 面编号 / 高亮 / 展开幽灵晶体 / 坐标轴与旋转弧 / 注释 / 球面网格 / gif。风格分四层：配色板（多主题）→ 语义-样式映射 → 具体几何风格（锥体箭头等）→ 场合预设 | 旧图重制（20 张 A1 类）+ ch7–9（对称操作图解、楔角展开图） |
| `sim` | Lumice CLI 胶水：写 config → 跑 → 读图；单光路过滤；光线数控制；姿态族参数化——六棱柱与锥晶 config（`pyramid_crystal_from_geometry`）、`analyze` 光路分析胶水**已交付** | 旧图重制（5 张 B 类）+ ch8/9（已用）+ ch10/11 + 反向问题正向模型 |
| `math.group` | 镜面生成群闭包、共轭类、与旋转子群的对易判据（`07-reflection-group/code/check_group.py` 是原型） | ch7 |
| `signature` | $(M,\mathbf n_a,M^{-1}\mathbf n_b)$ 的规范型（商掉晶体对称）——**已交付** `halo_notes.math.signature`（规范型 / 带定义域的 $\Phi$ 指纹 / 六棱柱全类表，面法向从传入的多面体取，锥晶可直接用） | ch8、ch9 |
| `geometry.polyhedron` | 一般凸多面体晶体的面法向、面相交可达性、光路枚举（ch2 枚举器的 python 复活，从硬编码六棱柱升级）——**已交付**，现由 `lumice_integral.geometry` 提供（`Polyhedron`/`HexPrism`/`Pyramid`、`feasibility`、`enumerate`；本仓 2026-09-18 起以 path 依赖引入并删除本地副本；ch8 已用它出可达性表，锥晶只跑过 smoke） | ch8、ch9（最贵的前置） |
| `math` | SO(3) / S² / S³ 采样与分布；$SO(3)$ 上的分布族与群卷积；$D_P(\mathbf u)$ 及 Jacobian；姿态空间离散化 | ch5 / ch6 重制、ch10、ch11、反向问题、番外 |
| （不在本仓） | **直接积分**：独立项目 Lumice Integral（`~/Codes/Lumice Integral`），与 Ice Halo 并列；**本仓将直接依赖它**（task 16 `geometry-depend-on-lumice-integral`：几何单一权威迁过去、本仓副本删除）。它按本表的需求排近期计划（其 `docs/roadmap.md` §3.5）：每像素成本 → 缺陷②（晶体高径比约定 + 尾段）→ 光路类为渲染单位（ch7–9）→ Phase II 晕图 $D_P$/$DF$/caustic（ch10）→ 姿态密度族（ch11）；ch6 的 6.4 用其 figure-data v3（W2），6.5 条带等缺陷②修完重渲 | ch6 重制（后排）、ch10、ch11 |

重制插图的逐张盘点在 `scratchpad/figures-manifest.md`（不入 git）。
