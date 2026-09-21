---
type: directors-cut
status: outline
---
# 现代冰晕研究漫谈(番外): Tape 光点法与矩阵法

tags: [[halo]], [[Halo Notes]], [[math|数学]], [[optics|光学]], [[我的知乎专栏文章]],

> 本篇尚未动笔。番外不占主线章号，落在漫谈(8) 之后作过场；提纲 2026-09-20 草成（待作者 review）。主源三篇：Tape 1980 *Analytic foundations of halo theory*、Tape & Können 1999 *A general setting for halo theory*、Tape & Moilanen 2006 *Atmospheric Halos and the Search for Angle x*；另以 Tricker 1973 *The long hexagonal ice prism as a kaleidoscope* 作万花筒光路的一手历史源。逐页引注的源笔记见同目录 `源笔记-Tape.md`（下文 `[Tape1980 p.N]` 等页码沿其约定，指本机 PDF 页序号）；数值互证脚本 `code/tape_halo_function.py`（Tape 侧两条链路）、`code/crosscheck_bridge.py`（翻译层）、`code/crosscheck_a.py`（逐点）、`code/crosscheck_b.py`（图级），数据与结论在 `data/crosscheck_a_summary.md`、`data/crosscheck_b_inner_edge.csv`、`data/notes.md`。

> 本篇知识点（拟）：光点（light point）、楔与 pole、等变、楔 × 折叠

## 提纲

### 0. 开场：三块拼图，而不是三代人同算一只幻日

- 从 [[三种楔子-十二种折叠|漫谈(8)]] §1 那句接过来（原句）：「这串推导把几个概念串联在一起了，Tricker 的万花筒展开、漫谈(3) 中的矩阵法、Tape 和 Können 的 wedge theory，都联系在了一起。」新补入的 Tricker 1973 让这里不必再把三者硬写成「同算一个实例」，而可以拆成三个恰好互补的台阶。
- **第一块：只有折叠。** Tricker 让光从长六棱柱的底面进出，在侧面间连续全反射；平行底面的入、出折射等量，剩下的只是太阳方向关于各侧面的逐次镜像。他明确说这与简单万花筒相同 [Tricker1973 p.4]。用本系列语言，这是 $W=I,\ \Phi=M$。
- **第二块：只有楔。** 最普通的 22° 幻日 `3-5` 没有内反射，$M=I,\ \Phi=W$。Tape 的 1980 / 1999 两条链路与本系列算出同一条光点轨迹；太阳 0° 时内边为 21.8393°，三列一致到 $10^{-10}$°（`data/crosscheck_b_inner_edge.csv`）。
- **第三块：二者相乘。** A60-10（`3-4-5-7`）把与幻日相同的 60° 楔 $W$ 和一个 120° 折叠 $M$ 放在同一条光路里；这才是 $\Phi=M\circ W$ 相比两条古典路线多出的统一结构。
- 本篇的问题因此不是「谁对」，而是：Tricker 抓住 $M$、Tape 抓住 $W$ 与取向映射之后，为什么还需要把两者放进同一个对象里。

### 1. Tricker：万花筒是 $W=I$ 的纯折叠

- 一手材料现在已有：Tricker 1973 研究长六棱柱水平飘浮时的 heliacal / anthelic arcs。光从底面进入，经侧面若干次全反射后从另一底面射出，或再经后端面反射后从原底面射出 [Tricker1973 p.1, p.4]。
- 他的核心作图是把太阳方向逐次关于六个侧面反射：$S_1$ 是 $S_0$ 关于一个侧面的像，后续像再关于下一侧面反射；不同像代表一次、两次、三次反射后的光束方向 [Tricker1973 p.4, Fig. 4]。这正是矩阵法里把反射连乘成 $M$ 的几何版本。
- 侧面反射不改变光线对底面的入射角，只改变入射面的方位；两平行底面上的入、出折射大小相等。因此穿过晶体的原始方向保持不变，其余像落在以晶体轴为极、过太阳的小圆上；Tricker 随即明确将理论比作简单万花筒 [Tricker1973 p.4]。
- **对应关系要收窄**：这篇论文直接给出的是 $W=I$ 的平行光路，所以 $\Phi=M$；它不是一般 $M\circ W$ 分解的完整先例，也没有把所有反射序列商成 12 类。ch8 的「Tricker 万花筒展开与矩阵法合流」应理解为：逐次镜像合成为 $M$；非平行首尾面所需的 $W$ 是后续合流时补上的另一半。
- **已经可以写实的部分**：TM2006 Fig. 4.5 明确规定以介质折射率为半径画同心天球（图面截面即同心圆），入射、反射、折射光点沿界面法线共线；Fig. 4.8 再由 Snell 定律推出这套作图 [TM2006 p.48, p.51]。因此「同心圆作图」不是悬而未决的 Tricker 专属细节，而是可以直接据 Tape & Moilanen 介绍的标准几何折射法。
- **仍保留的一层谨慎**：Tricker 1973 说的是逐次镜像和天球上的 image / direction，并没有在本文使用可确认的 “light point” 术语。本机仍无 Tricker 1970 原书，故不能断言 1970 书采用了 TM2006 的同心圆图式或相同命名；两者属于同一古典几何传统是合理判断，但直接继承关系仍是推断。
- 图占位：① 改绘 Tricker1973 Fig. 4 的「侧面逐次镜像 → 一个 $M$」；② 标准同心球折射作图（改绘自 TM2006 Fig. 4.5）。两张图并列，正好把反射的 $M$ 与折射的 $W$ 分开；不要把第二张题作「Tricker 的作图」。

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
- 一句话把奇点 / caustic 语言留给后篇：Tape 1980 自陈「理论最显眼的缺陷是缺少 caustic 强度的简单解析度量」[Tape1980 p.16]；Können 1983 后来在五个理想化假设下给出了近晕角的解析强度分布与 halocaustic 形状 [Können1983 p.1, p.3, p.10]。任意姿态分布 $\rho$ 与光路权重下的统一 pushforward 仍是本系列多出的一层（源笔记 §4 #17、#30），留给 ch10，本篇不展开。

## 配图（拟）

| 图 | 类型 | 内容 / 读者必须能看出的东西 |
|---|---|---|
| 万花筒与同心球 | 几何示意（分别改绘 Tricker1973 Fig. 4、TM2006 Fig. 4.5） | 左：太阳方向关于六棱柱侧面逐次成像，镜像连乘就是 $M$；右：折射率决定同心球半径，法线投影就是 $W$。先把两块分开，随后才能看懂 $M\circ W$ |
| atlas 对照图（互证 B） | 图表（`code/crosscheck_b.py` 数据重画） | 左 22° 幻日光点轨迹随太阳高度 $\Sigma=0°/10°/20°/30°$ 四条（`data/crosscheck_b_locus_sigma{0,10,20,30}.csv`），Tape 侧与本系列侧叠画；旁附内边角距三链路对照表（`data/crosscheck_b_inner_edge.csv`）：**两种写法、四条曲线、同一组数** |
| `3-5` 双写示意 | 图表（`code/crosscheck_a.py` 数据重画） | 同一个姿态、同一个太阳方向，左边用 Tape 的两次平行投影（内球半径 1、外球半径 $n$）、右边用本系列 $-R\Phi(-R^{-1}\mathbf S)$ 各画一次光点（`data/crosscheck_a_A60-12.csv` 取一组可达样本）：**两套坐标系、两条公式，光点重合**；可加第三块：A60-10 在片晶（重合）与柱晶（Rule 1 偏 17°–150°）下的对照（`data/crosscheck_a_A60-10_plate.csv`、`data/crosscheck_a_A60-10_column_negative.csv`） |

## 文献核对状态

转写自 `源笔记-Tape.md` §7（条目与顺序不变；已解决项仍保留原编号，避免两份清单漂移）。

| # | 断言 | 来源状态 | 建议处置 |
|---|---|---|---|
| 1 | 两条几何支线已有各自的一手材料：同心圆 / 同心球折射作图由 TM2006 Figs. 4.5、4.8 直接确认 [TM2006 p.48, p.51]；万花筒式逐次镜像由 Tricker1973 p.4 / Fig. 4 直接确认。仍待核的是 Tricker 1970 是否把二者放在同一图式中、使用什么名字 | 方法均已核；Tricker 1970 原书仍缺。1973 文明确支持 $W=I$ 的纯折叠，不支持一般 $M\circ W$ | §1 分两图介绍，分别标来源；不把 TM2006 的同心圆图署给 Tricker，也不把 Tricker 1973 扩写成一般楔理论 |
| 2 | 「光点法」这个称呼是否 Tape 自己的用语：已核实 "light point" [TK1999 p.3]、"light point diagram" [TM2006 p.50] 是 Tape 的术语，Tape 1980 用 "point of light" [Tape1980 p.1, p.18 note 18]。待核对的只剩：Tricker 1970 是否也这么叫（同第 1 条）；ch2 正文引用 Tape 时用的原话是什么 | 已核页码（Tape 用语）；本机无文献（Tricker 部分） | 番外标题「光点法」可以用；作者顺手翻一下 ch2 正文引 Tape 的原话，若与 "light point" 不一致在 §2 开头加一句说明 |
| 3 | Tape 1994 *Atmospheric Halos*：TK1999 [11] 与 TM2006 [76] 多处引它（TK1999 p.35 Sturm 照片在 Ref. 11 p.92、p.39 MC 方法在 pp.132–133；TM2006 p.61、p.202）。1994 书里是否已有 pole / spin vector 的雏形（TM2006 p.147 说 pole 是 Können 1990 年代提出，1994 书应尚无），以及 Tricker 万花筒展开在 1994 书里的处理 | 本机无文献 | 番外若要说「Tape 1994 还没有 pole」需原书页码；否则本篇不提 1994 书 |
| 4 | fold / pleat 的文献链：Tape 1980 原文已经出现；Tape 1982 *Folds, pleats, and halos* 作科普展开；Tape 1983 *Halos and Singularities*（DOI `10.1364/MO.1983.FA4`）再作技术扩展 | 已核出版信息与正式摘要（1983 全文需订阅）；framework 已修正 | 本篇若提 fold / pleat，以 Tape 1980 页码为一手依据；1982/1983 留给 ch10 文献背景 |
| 5 | TM2006 [74] "Walter Tape, *The Deviation of Light in a Transparent Wedge*, To appear" [TM2006 p.241]；2008 正式发表 *Maximum deviation of light in a transparent wedge*, *Applied Optics* 47, H44–H51，DOI `10.1364/AO.47.000H44` | 已核正式摘要；全文需订阅，尚未逐式比对 | 本篇不引；ch10 可引 2008 正式出处，若复现 $\Delta_{\max}$ 分段式需再核全文 |
| 6 | Können 1983 在五个理想化假设下解析计算近晕角强度与 halocaustic 形状；Können 1998 主旨是 inner-edge polarization，不是一般 caustic 强度理论 | 已核两篇作者公开全文 [Können1983 p.1, p.3, p.10; Können1998 p.4] | 源笔记 §4 #30 已改「部分」；番外只用一句划界，完整处理后置 ch10 |
| 7 | **已修正（chore framework-fixes）**：本系列自身：framework §4 原写 $\mathbf x=R\Phi_P(R^{-1}\mathbf s)$，与 `signature.phi(d)`（`d` 为入射传播方向）的符号约定不一致（源笔记 §5「光线 vs 光点」行）。建议 framework 改写为 $\mathbf x=-R\Phi_P(-R^{-1}\mathbf s)$ 或明注「$\Phi$ 此处按光点约定理解」。子任务 3 已按严格写法实现 `crosscheck_bridge.light_point` 并通过全部互证（`data/notes.md` §1、§3） | 已数值核对（**framework 已改**：`chore-framework-fixes` 把定理 8 改为 $\mathbf x=-R\Phi_P(-R^{-1}\mathbf s)$，与本条建议一致） | 本篇 §3 写光点公式一律用 $-R\Phi(-R^{-1}\mathbf S)$；framework.md 定理 8 符号已修正 |
| 8 | ch8 §6 的「142.56°」是半高点，与 $21.8°+120°=141.8°$ 的锐边理论值差 0.7°——差值是否全部来自半高定义 + 太阳角径 + 截面权重。已用 `crosscheck_b.py` 数值验证：锐边理论值 141.8393° = $\Delta_m(60°)+120°$，与 142.56° 的差归因于半高定义 + 0.5° 桶 + 角径 / 倾角展宽（`data/notes.md` §2） | 已数值核对 | 本篇 §3 按 `notes.md` §2 的口径交代一句即可；ch8 不改 |
| 9 | Tape 1980 Eq. (32) 的 $\varphi$ 取值表里 "infralateral" 出现两次（$\varphi=-\alpha$ 与 $\varphi=\alpha$）[Tape1980 p.14]——按 $\lambda$ 只定义到 mod 180 [Tape1980 p.13] 应是 $\lambda=0$ 与 $\lambda=180$ 两个分支，不是笔误 | 已核页码（推断，未见原文明说） | 本篇不涉及 infralateral，不处理；ch10 若复现 infralateral 需两支都取 |
| 10 | TK1999 Fig. 55（22° pole diagram，p.66）与 Fig. 59（46°，p.71–72）的表格数值（$s_1,s_2,s,t$）源笔记未逐格抄录 | 已核页码（表格未抄录） | 本篇不用这些数值；若配图要标 Plate 3 5 的 $s_1,s_2$，作者回 p.66 抄 |
