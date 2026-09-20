---
type: directors-cut
status: outline
---
# 现代冰晕研究漫谈(番外): Tape 光点法与矩阵法

tags: [[halo]], [[Halo Notes]], [[math|数学]], [[optics|光学]], [[我的知乎专栏文章]],

> 本篇尚未动笔。番外不占主线章号，落在漫谈(8) 之后作过场；提纲 2026-09-20 草成（待作者 review）。主源三篇：Tape 1980 *Analytic foundations of halo theory*、Tape & Können 1999 *A general setting for halo theory*、Tape & Moilanen 2006 *Atmospheric Halos and the Search for Angle x*；逐页引注的源笔记见同目录 `源笔记-Tape.md`（下文 `[Tape1980 p.N]` 等页码沿其约定，指本机 PDF 页序号）；数值互证脚本 `code/tape_halo_function.py`（Tape 侧两条链路）、`code/crosscheck_bridge.py`（翻译层）、`code/crosscheck_a.py`（逐点）、`code/crosscheck_b.py`（图级），数据与结论在 `data/crosscheck_a_summary.md`、`data/crosscheck_b_inner_edge.csv`、`data/notes.md`。

> 本篇知识点（拟）：光点（light point）、楔与 pole、等变、楔 × 折叠

## 提纲

### 0. 开场：同一个幻日，三代人各算一遍

- 从 [[三种楔子-十二种折叠|漫谈(8)]] §1 那句接过来（原句）：「这串推导把几个概念串联在一起了，Tricker 的万花筒展开、漫谈(3) 中的矩阵法、Tape 和 Können 的 wedge theory，都联系在了一起。」ch8 写到这里只是点了名，没说这三条路各自长什么样、算出来的东西一样不一样。
- 钩子：就拿最普通的 22° 幻日（`3-5`，片晶）当靶子，三代人各算一遍——Tricker 用尺规式的光线几何构造，Tape 把「取向 → 天上的光点」写成一个映射，本系列把内反射商掉成一个 O(3) 算子再看群作用。结论先剧透：太阳 0° 时幻日内边到太阳 21.84°，Tape 的两条链路与本系列三条路算出同一个数（`data/crosscheck_b_inner_edge.csv` 第一行三列一致到 $10^{-10}$°）。
- 本篇的问题不是「谁对」，而是「同一个数之外，各自还能说什么、说不出什么」。

### 1. Tricker：光线的几何构造（骨架，待作者核对）

- 只列骨架，本机无 Tricker 1970 原书，以下全是转述：Tape 1980 开篇说自己的结果「类似 Tricker 的」，引 Tricker 1970 / 1972 / 1979 [Tape1980 p.1, p.18 refs 1, 2, 14]；TK1999 说「最接近的先驱是 Tricker [2]（1979）」[TK1999 p.2]；TM2006 把几何形式的折射定律溯到 Hamilton、MacCullagh（1837）[TM2006 p.51]，没提 Tricker（源笔记 §7 第 1 条）。
- 一句话定位（暂按上面三处转述写，措辞待作者核对）：Tricker 那一代的做法是**光线几何构造**——给定取向族，用作图把出射方向画到天球上；「万花筒展开」是 ch8 §1 已经给他贴过的标签，本篇沿用，不再多说。
- **待作者核对**（作者补，runner 不编）：① Tricker 1970 书里的构造是否就是「两个同心圆」的光点作图，他用的名字是什么（"point of light"？别的？）；② Tricker 的构造与 Tape 光点法在几何上是否等同（若等同，§2 开头可以说「Tape 把 Tricker 的作图写成了公式」；若不等同，此处只写「几何构造」四个字，不引原话）。
- 图占位：无（不能凭转述画 Tricker 的图）。

### 2. Tape：取向空间到光点空间的映射

- 「光点」是什么：光线的反向在天球上的那个点，「应该被点亮的那个点」[TM2006 p.43]；折射定律的几何形式——把天球半径取成折射率，入射、折射光线的光点在一条垂直于界面的直线上 [TM2006 p.48]。ch8 §1 那句「古典几何路线的光点法，内外两个同心圆，做的就是这件事」说的就是它（源笔记 §4 #8）。
- 取向 → 光点的映射，两种写法、一个东西（源笔记 §2.7）：
  - 1980 版 halo function $F(\theta,\mu,\beta)=R_\beta\big(A(\theta,D(\theta,\mu))\big)$ [Tape1980 p.4, Eq. (20)]，太阳钉在 $u$ 轴上，用 Bravais 定律显式写；
  - 1999 版两次平行投影 $\mathbf H=\mathrm{pr}\big[\mathrm{pr}(\mathbf S,\mathbf N,n),\mathbf X,1\big]$ [TK1999 p.3, Eq. (7)]，并且明说「Bravais 定律对我们只有历史兴趣」[TK1999 p.9]。
  - 两版共同的边界：只有一个楔、只有折射，晶体形状只以楔角 $\alpha$ 进入 [Tape1980 p.1, p.13; TK1999 p.15]。
- 限制到取向子集得到晕：generating set 是开集 / 曲面 / 曲线 ⇒ 三维 / 二维 / 一维晕 [Tape1980 p.13]；圆晕是全体取向，幻日是一条水平直线 $\beta=90,\ \theta=90-\Sigma$ [Tape1980 p.16]。奇点得 caustic：caustic = $F|_{\mathcal N}$ 奇点集的像，「相对多的取向点亮天球一小块」[Tape1980 p.1]；圆晕的 caustic 就是内圆边，半径 21.8° [Tape1980 p.5]（源笔记 §1.4）。
- wedge 框架把「所有可能的折射晕」列成图集：每个晕由 $(\alpha,\mathbf P_u,\psi)$ 决定，每个 $\Sigma$ 一张 [TK1999 p.42]；atlas 的每页是一张 pole 球面的 Bravais 坐标网，晕的仿真图放在它的 pole 处 [TK1999 p.6]（源笔记 §2.4）。**注意**这里的 pole 球面不是天球，是「空间方向在楔系里的样子」——与本系列定理 8 的底 $S^2\ni\mathbf u=R^{-1}\mathbf s$ 是同一个球面（源笔记 §4 #3、#22）。
- **用 `3-5` 把他的公式算一遍**（互证 B，`code/crosscheck_b.py`）：
  - 在 atlas 里它叫 Plate 3 5，左 22° 幻日，pole $\mathbf P_u=(0,\pm1,0)$，spin vector 平行于楔棱 [TK1999 p.6, p.32]；Fig. 33 中 $(0,1,0)$ 处那张「可能看着眼熟——它是右 22° 幻日」[TK1999 p.7]。
  - 算出来的数（`data/crosscheck_b_inner_edge.csv`，1980 Bravais 链路与 1999 投影链路两列）：幻日内边到太阳的角距随太阳高度 $\Sigma=0°/10°/20°/30°$ 为 21.8393° / 22.1372° / 23.0733° / 24.7931°；两条 Tape 自己的链路一致到 $10^{-10}$°。
  - $\Sigma=0$ 时的完整光点轨迹（`data/crosscheck_b_locus_sigma0.csv`）：bearing $\tau\equiv-90°$，确认 `3-5` 是**左**幻日，与 TK1999 p.32 的 Plate 3 5 / 3 7 = 左 / 右一致（`data/notes.md` §2）。
- 图占位：atlas 对照图（见文末配图表）。

### 3. 矩阵法：先商成 O(3) 算子，再看群作用

- 本系列的做法一句话：$\Phi=M\circ W$——展开空间里的一个楔 $W$，再一个内反射折叠 $M$（ch8 §1 等变分解，不重推）；天球上 $T=R\,\Phi\,R^{-1}$。Tape 也有这条等变引理 $\mathbf F(w\mathbf N,w\mathbf X,w\mathbf S)=w\mathbf F(\mathbf N,\mathbf X,\mathbf S)$ [TK1999 p.4, Eqs. (12)–(13)]，但只拿它做变换规则与 pole；本系列拿它把 $M$ 从两次折射中间提到最外面——**同一个引理，用途不同**（源笔记 §4 #9）。
- **同一个 `3-5` 再算一遍，同一个数**（互证 A 第一组，`data/crosscheck_a_summary.md` §1，明细 `data/crosscheck_a_A60-12.csv`）：1000 组 Haar 均匀姿态 × 均匀太阳方向，本系列 $-R\Phi(-R^{-1}\mathbf S)$ 与 TK1999 $\mathbf H(Ru_0,60°,\mathbf S)$：可达判定 1000/1000 一致（两侧各 161 组可达），两侧都可达时最大角距离 $2.278\times10^{-14}$ rad。§2 报过的内边曲线，本系列那一列（`crosscheck_b_inner_edge.csv` 第三列）与 Tape 两列同样一致到 $10^{-10}$°。到这里为止，两种语言在 $M=I$ 的光路上是**同一个数**，本系列没有多说任何东西。
- **拿 A60-10 问古典法**（`3-4-5-7`，同一个 60° 楔 + 一个 120° 折叠，ch8 §6 的「142° 幻日」）：Tape 的楔由**物理**入射面、出射面定义 [TK1999 p.27]，翻译层 `code/crosscheck_bridge.py` 把 `3-4-5-7` 翻成 Tape 楔时，$M$ 只用来算展开出射面 $M^{-1}\mathbf n_7=\mathbf n_5$，得到的楔与 `3-5` 完全相同——**$M$ 在翻译中丢了**，Tape 侧算出的是幻日 $\mathbf H_{35}$，不是 $\mathbf H_{3457}$（`data/notes.md` §3）。两个方向都要如实写：
  - **片晶族：能**。片晶姿态下 $RMR^{-1}=\mathrm{zrot}(120°)$（200 组样本，恒等式误差最大 $7.216\times10^{-16}$），恰好落进 TK1999 的方位不变性 Rule 1 [TK1999 p.22, Eq. (67)]，于是 A60-10 = 「把 Plate 3 5 幻日整体绕竖直转 120°」：两侧都可达的 31 组样本，$\mathbf H_{3457}$ 与 $\mathrm{zrot}(120°)\mathbf H_{35}$ 最大角距离 $3.003\times10^{-15}$ rad（`crosscheck_a_summary.md` §2，明细 `crosscheck_a_A60-10_plate.csv`）。$\Sigma=0$ 时最内点 $=21.8393°+120°=141.8393°$（`crosscheck_b_inner_edge.csv` 第四列）；$\Sigma>0$ 时「+120°」只对方位成立、不对角距成立——$\Sigma=10°/20°/30°$ 最内点 137.6551° / 127.0555° / 113.0092°（与幻日内边差 115.52° / 103.98° / 88.22°），这就是 ch8 §6 说亮斑「沿幻日环、在反日点附近」的几何来由（`data/notes.md` §2）。
  - **柱晶族：不能**。柱晶姿态下 $R\mathbf k$ 水平，$RMR^{-1}$ 是绕水平轴的 120° 旋转，$\angle(RMR^{-1}\mathbf k,\mathbf k)\equiv120°$，不在 TK1999 的 $Z$（绕竖直旋转群）里，Rule 1 前提失效：两侧都可达的 35 组样本，强行套 Rule 1 得到的 $\mathrm{zrot}(120°)\mathbf H_{35}$ 与真值 $\mathbf H_{3457}$ 差 min / mean / max = 17.512° / 88.451° / 150.247°（`crosscheck_a_summary.md` §3，明细 `crosscheck_a_A60-10_column_negative.csv`）。同一批样本上本系列自己的共轭式 $RMR^{-1}\mathbf H_{35}=\mathbf H_{3457}$ 仍逐点成立（最大 $2.993\times10^{-15}$ rad）。
  - 落点：TK1999 自己说过，加一次内反射「会得到一整本新 atlas，任何其它新光路同样如此」[TK1999 p.15]；他们缺的对象正是一个固定在**晶体**上（而不是楔上）的正交算子 $M$，光点公式补成 $\mathbf H=RMR^{-1}\,\mathbf F(u\mathbf N_0,u\mathbf X_0,\mathbf S)$ 就是本系列 signature 的 $M$ 那一维（`data/notes.md` §3；源笔记 §4 #19、#20）。片晶族能表示 A60-10，唯一的原因是 $M$ 恰好是绕 spin vector 的旋转（源笔记 §6.2）——是巧合，不是结构。
- 顺手交代 ch8 §6 的 142.56° 与这里 141.84° 的 0.72° 差：前者是 Lumice 渲染（太阳角径 0.5°、倾角 0.5°、0.5° 桶）的内侧**半高点**，后者是零角径、零倾角、单条光路的**锐边理论值**；半高必在锐边外侧、量级 < 1°，方向与大小都对得上，ch8 不改（`data/notes.md` §2）。
- 图占位：`3-5` 双写示意（见配图表）。

### 4. 收束：解释一个实例，还是分类一个结构

- 「古典几何解释一个实例，现代代数分类一个结构」——不是谁对谁错，是问的问题不同：Tape 问「给定楔与取向族，光点落在哪」，本系列问「六棱柱一共能给出多少种 $\Phi$，它们之间什么关系」。A60-10 与 A60-12 是「同一个楔 × 不同折叠」，这层关系在 atlas 里是两张无关的图（片晶）或干脆不存在（柱晶）（源笔记 §4 #20、#21）。
- 反过来也要说清本系列没有的：caustic 的解析处理——显式 Jacobian 核公式与奇点集方程 [Tape1980 p.5, p.15]（源笔记 §4 #29）；「最小偏折轨迹 ≠ caustic」的警示，只对切弧 / 幻日 / 圆晕成立 [Tape1980 p.15]（#16）；contact circle、Nonempty Halos 定理这些几何直觉工具（#24）。
- 一句话把 Tape 1980 的奇点 / caustic 语言留给后篇：Tape 自陈「理论最显眼的缺陷是缺少 caustic 强度的简单解析度量」[Tape1980 p.16]（源笔记 §4 #30）——强度要靠姿态分布 $\rho$，那是三篇里都没有的对象（#17），留给 ch10 讲亮度时接手，本篇不展开。

## 配图（拟）

| 图 | 类型 | 内容 / 读者必须能看出的东西 |
|---|---|---|
| atlas 对照图（互证 B） | 图表（`code/crosscheck_b.py` 数据重画） | 左 22° 幻日光点轨迹随太阳高度 $\Sigma=0°/10°/20°/30°$ 四条（`data/crosscheck_b_locus_sigma{0,10,20,30}.csv`），Tape 侧与本系列侧叠画；旁附内边角距三链路对照表（`data/crosscheck_b_inner_edge.csv`）：**两种写法、四条曲线、同一组数** |
| `3-5` 双写示意 | 图表（`code/crosscheck_a.py` 数据重画） | 同一个姿态、同一个太阳方向，左边用 Tape 的两次平行投影（内球半径 1、外球半径 $n$）、右边用本系列 $-R\Phi(-R^{-1}\mathbf S)$ 各画一次光点（`data/crosscheck_a_A60-12.csv` 取一组可达样本）：**两套坐标系、两条公式，光点重合**；可加第三块：A60-10 在片晶（重合）与柱晶（Rule 1 偏 17°–150°）下的对照（`data/crosscheck_a_A60-10_plate.csv`、`data/crosscheck_a_A60-10_column_negative.csv`） |

## 待作者核对

转写自 `源笔记-Tape.md` §7（条目与顺序不变，只换列名：来源状态取值以 {本机无文献 / 已核页码 / 已数值核对} 为基础枚举，单条断言涉及多个子点时用分号列出各子点各自的取值，如「已核页码（Tape 用语）；本机无文献（Tricker 部分）」）。

| # | 断言 | 来源状态 | 建议处置 |
|---|---|---|---|
| 1 | Tricker 1970 *Introduction to Meteorological Optics* 的构造法是否就是「光点」/ 两个同心圆的几何作图；Tricker 用的名字是什么（"point of light"? 别的?）。现有依据只有转述：Tape 1980 说其结果「类似 Tricker 的」并引 Tricker 1970/1972/1979 [Tape1980 p.1, p.18 refs 1, 2, 14]；TK1999「最接近的先驱是 Tricker [2]（1979）」[TK1999 p.2]；TM2006 溯到 Hamilton、MacCullagh 1837 [TM2006 p.51]，没提 Tricker | 本机无文献（转述已核页码） | 作者查 Tricker 1970 原书后补 §1 的措辞与是否等同 Tape 光点法的判断；查不到则 §1 只写「几何构造」，不引原话 |
| 2 | 「光点法」这个称呼是否 Tape 自己的用语：已核实 "light point" [TK1999 p.3]、"light point diagram" [TM2006 p.50] 是 Tape 的术语，Tape 1980 用 "point of light" [Tape1980 p.1, p.18 note 18]。待核对的只剩：Tricker 1970 是否也这么叫（同第 1 条）；ch2 正文引用 Tape 时用的原话是什么 | 已核页码（Tape 用语）；本机无文献（Tricker 部分） | 番外标题「光点法」可以用；作者顺手翻一下 ch2 正文引 Tape 的原话，若与 "light point" 不一致在 §2 开头加一句说明 |
| 3 | Tape 1994 *Atmospheric Halos*：TK1999 [11] 与 TM2006 [76] 多处引它（TK1999 p.35 Sturm 照片在 Ref. 11 p.92、p.39 MC 方法在 pp.132–133；TM2006 p.61、p.202）。1994 书里是否已有 pole / spin vector 的雏形（TM2006 p.147 说 pole 是 Können 1990 年代提出，1994 书应尚无），以及 Tricker 万花筒展开在 1994 书里的处理 | 本机无文献 | 番外若要说「Tape 1994 还没有 pole」需原书页码；否则本篇不提 1994 书 |
| 4 | framework.md §4 表里「Tape 1980：caustic = halo function 奇点集的像；**1983 fold / pleat**」——fold / pleat 在 Tape 1980 p.14 已经出现（引 Whitney / Callahan 1974）；「1983」指哪篇（可能是 Können 1983 *Polarization and intensity distributions of refraction halos*，TK1999 ref 10 [TK1999 p.74]，或 Tape 另一篇） | 本机无文献 | 作者裁定 framework.md 该行是否改；本篇 §4 引 fold / pleat 时只写 Tape 1980 p.14，不写 1983 |
| 5 | TM2006 [74] "Walter Tape, *The Deviation of Light in a Transparent Wedge*, To appear" [TM2006 p.241]——是否已发表、是否含比 Tape 1980 更完整的 $\Delta_{\max}$ 解析（TM2006 p.89 引它给 $\Delta_{\max}$ 分段公式） | 本机无文献 | 本篇不引；ch10 若要引最大偏折再查正式出处 |
| 6 | Können 1983（TK1999 ref 10 [TK1999 p.74]）与 Können 1998（ref 9）：inner edge polarization——是否含 caustic 强度的解析处理（Tape 1980 自陈缺口 [Tape1980 p.16]） | 本机无文献 | 本篇 §4 「caustic 强度没有简单解析度量」只写成 Tape 1980 的自陈，不写成「文献里没有」；若 Können 1983 已做，源笔记 §4 #30 判定改「部分」 |
| 7 | **已修正（chore framework-fixes）**：本系列自身：framework §4 原写 $\mathbf x=R\Phi_P(R^{-1}\mathbf s)$，与 `signature.phi(d)`（`d` 为入射传播方向）的符号约定不一致（源笔记 §5「光线 vs 光点」行）。建议 framework 改写为 $\mathbf x=-R\Phi_P(-R^{-1}\mathbf s)$ 或明注「$\Phi$ 此处按光点约定理解」。子任务 3 已按严格写法实现 `crosscheck_bridge.light_point` 并通过全部互证（`data/notes.md` §1、§3） | 已数值核对（**framework 已改**：`chore-framework-fixes` 把定理 8 改为 $\mathbf x=-R\Phi_P(-R^{-1}\mathbf s)$，与本条建议一致） | 本篇 §3 写光点公式一律用 $-R\Phi(-R^{-1}\mathbf S)$；framework.md 定理 8 符号已修正 |
| 8 | ch8 §6 的「142.56°」是半高点，与 $21.8°+120°=141.8°$ 的锐边理论值差 0.7°——差值是否全部来自半高定义 + 太阳角径 + 截面权重。已用 `crosscheck_b.py` 数值验证：锐边理论值 141.8393° = $\Delta_m(60°)+120°$，与 142.56° 的差归因于半高定义 + 0.5° 桶 + 角径 / 倾角展宽（`data/notes.md` §2） | 已数值核对 | 本篇 §3 按 `notes.md` §2 的口径交代一句即可；ch8 不改 |
| 9 | Tape 1980 Eq. (32) 的 $\varphi$ 取值表里 "infralateral" 出现两次（$\varphi=-\alpha$ 与 $\varphi=\alpha$）[Tape1980 p.14]——按 $\lambda$ 只定义到 mod 180 [Tape1980 p.13] 应是 $\lambda=0$ 与 $\lambda=180$ 两个分支，不是笔误 | 已核页码（推断，未见原文明说） | 本篇不涉及 infralateral，不处理；ch10 若复现 infralateral 需两支都取 |
| 10 | TK1999 Fig. 55（22° pole diagram，p.66）与 Fig. 59（46°，p.71–72）的表格数值（$s_1,s_2,s,t$）源笔记未逐格抄录 | 已核页码（表格未抄录） | 本篇不用这些数值；若配图要标 Plate 3 5 的 $s_1,s_2$，作者回 p.66 抄 |
