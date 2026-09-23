# 互证结论与分歧记录（子任务 3 → 子任务 4 提纲素材）

产出方：`code/crosscheck_a.py`（逐点）、`code/crosscheck_b.py`（图级），单测 `code/tests/test_tape_halo_function.py`。
Tape 侧公式全部照抄 `../源笔记-Tape.md` 附录 A（TK1999 路线 + Tape 1980 路线），本系列侧只调 `halo_notes.math.signature.phi`。
两侧的唯一接口是 `code/crosscheck_bridge.py` 的 `wedge_orientation`（$u=Ru_0$）与 `light_point`（$\mathbf H=-R\Phi(-R^{-1}\mathbf S)$）。

## 1. 互证 A（逐点）：同一晕两种语言算同一个数

统计表见 `crosscheck_a_summary.md`，明细见三个 CSV。结论：

| 组 | 结果 |
|---|---|
| A60-12（`3-5`，$M=I$），1000 组 Haar 均匀 $R$ × $S^2$ 均匀 $\mathbf S$ | 可达判定 1000/1000 一致（161 可达）；最大角距离 $2.3\times10^{-14}$ rad，无超阈值样本 |
| A60-10（`3-4-5-7`，$M=R_{\mathbf c}(120°)$）片晶族，200 组 | $RMR^{-1}=\mathrm{zrot}(120°)$（$7\times10^{-16}$）；$\mathbf H_{3457}$（本系列）= $\mathrm{zrot}(120°)\mathbf H_{35}$（Tape + Rule 1），最大 $3\times10^{-15}$ rad |
| A60-10 柱晶族负例，同一组 200 个 $(\phi,\Sigma)$ + 自转 | $\angle(RMR^{-1}\mathbf k,\mathbf k)\equiv120°$；强行套 Rule 1 与真值差 17.5°–150.2°（均值 88°）；本系列共轭式 $RMR^{-1}\mathbf H_{35}=\mathbf H_{3457}$ 逐点成立（$3\times10^{-15}$ rad） |

排查链路：一次对齐，没有出现需要回查记号差异表的分歧。唯一的"表面分歧"是最初用 $\arccos(\mathbf a\cdot\mathbf b)$ 量角距离得到 $4\times10^{-8}$ rad，
换成 $2\arcsin(|\mathbf a-\mathbf b|/2)$ 后回到 $10^{-14}$——是量尺的浮点分辨率问题（learnings code-quality），不是两侧公式的差。

**可达判定为什么必然一致**（plan Step 4 风险要求写出的等价性论证）：TK1999 的 $\mathbf S\cdot\mathbf N\ge0$ 就是 `phi_batch` 的 $\mathbf d\cdot\mathbf n_a<0$
（$\mathbf d=-\mathbf S$）；第二次投影 $\mathrm{pr}(\mathbf T,\mathbf X,1)$ 的 $\mathbf T\cdot\mathbf X\ge0$ 且 $(\mathbf T\cdot\mathbf X)^2+1-n^2\ge0$
就是 `exit_ok` 的 $\hat{\mathbf d}_1\cdot\tilde{\mathbf n}_b\ge\cos\theta_c$（两边除以 $n^2$：$(\hat{\mathbf d}_1\cdot\tilde{\mathbf n}_b)^2\ge1-1/n^2=\cos^2\theta_c$）。
`entry_ok`（$-\hat{\mathbf d}_1\cdot\mathbf n_a\ge\cos\theta_c$）在 TK1999 没有对应判据，但对从外侧进入的光线它由 Snell 定律自动成立（内角 ≤ 临界角），
两边只在掠入射的浮点边界（$\mathbf S\cdot\mathbf N\to0^+$）上可能判不同——1000 组样本里没有碰到。

## 2. 互证 B（图级）：22° 幻日光点轨迹与内边

`crosscheck_b_locus_sigma{0,10,20,30}.csv`：片晶 $R=\mathrm{zrot}(\phi)$、361 个 $\phi$，两侧的 S-centered 坐标 $(\Delta,\tau)$ 逐点差 $<1.3\times10^{-13}$°，可达段完全一致。
$\tau\equiv-90°$（Σ=0 时）：`3-5` 的光点恒定落在太阳的同一侧，与 TK1999 p.32「Plate 3 5 / 3 7 是左 / 右 22° 幻日」的**分工**一致（`3-5` 与 `3-7` 分居两侧）。

⚠️ **左右的叫法按手性约定分开写**（作者 2026-09-23 裁定，正文已据此写）：本系列的侧面编号与 TK1999 / TM2006 手性相反，**同一个 `3-5`，本系列叫右幻日、Tape 文献叫左幻日**。本条原先直接写「`3-5` 是左幻日」是把 bearing 符号按 Tape 的约定读了，与 `docs/errata.md` #2（Lumice 取证：本仓编号下 `3-5` = 右幻日、ch1 已据此改正）冲突。两侧数值互证不受影响（$\tau$ 逐点相等，差 $<1.3\times10^{-13}$°），受影响的只是「左 / 右」这个名字。底层取证冲突（源笔记 §5 面编号行原判「完全一致」）尚未机械定案，见 errata #7。

`crosscheck_b_inner_edge.csv`：幻日内边角距，三条链路（TK1999 光点扫描 / Tape 1980 Bravais 链路 / 本系列光点扫描）在 $\Sigma=0,10,20,30$ 上一致到 $10^{-10}$°：

| $\Sigma$ | 内边（三链路） | A60-10 最内点 | 差 |
|---|---|---|---|
| 0° | 21.8393° | 141.8393° | 120.0000° |
| 10° | 22.1372° | 137.6551° | 115.52° |
| 20° | 23.0733° | 127.0555° | 103.98° |
| 30° | 24.7931° | 113.0092° | 88.22° |

Σ=0 时 A60-10 最内点 = $\Delta_m(60°)+120°=141.8393°$，与源笔记 §6.2「幻日转 120°」精确一致；Σ>0 时"+120°"只对方位成立、不对角距成立
（$\mathrm{zrot}(120°)$ 绕天顶转，到太阳的角距随 Σ 变），这正是 ch8 §6 说"142° 亮斑沿幻日环、在反日点附近"的几何来由。

### 141.84° vs ch8 §6 的 142.56°

ch8 图 6 报告的 142.56° 是 Lumice 渲染的**内侧半高点**（`08-wedge-times-fold/data/far_side_profile_numbers.txt`：sun 0°、太阳角径 0.5°、片晶 zenith σ=0.5°、
方位剖面 0.5° 桶线性插值、半高 = 峰值一半），本任务算的 141.84° 是零角径、零倾角、单条光路 `3-4-5-7` 的**锐边理论值**（最小偏折 = fold caustic 的位置）。
差 0.72° 来自定义不同：半高点必在锐边外侧（能量从零爬到半高需要有限宽度，ch8 记的"10%→半高 0.86°"就是这个爬升段），叠加 0.5° 桶宽与 0.25° 太阳半径 / 0.5° 倾角展宽。
方向一致（半高在锐边外侧）、量级一致（< 1°），本任务不重新推导半高定义、不改 ch8——源笔记 §7 第 8 条据此标为"已数值核对"。
ch8 表 7 各 $d$ 的"本格锐边"142.6°/142.2°/142.0°/141.5° 同理是半高口径；锐边理论值不依赖截面（$\Phi$ 不依赖 h/a、d），与该表"锐边几乎不变"的观察一致。

## 3. 分歧记录：古典法能说什么、说不出什么；矩阵法反之

直接引用源笔记 §4 对应表的判定（#13–16、#19–20、#24、#30），本任务只补一句"数值互证之后这些判断是否需要修正"：

**Tape 三篇（古典几何 / 光点法）能直接说的**：
- 单条纯折射光路的光点：$\mathbf H(u,\alpha,\mathbf S)$，两次平行投影（#1、#8）。数值互证证实它与本系列 $M=I$ 的 $\Phi$ **是同一个数**（互证 A 第 1 组、互证 B）——不需要修正。
- 22° / 46° 圆晕半径 $\Delta_m$（Eq. (41)）、幻日内边随太阳高度的曲线（Tape 1980 的 Bravais 链路）：本任务两条 Tape 自己的链路互相对齐、且与本系列对齐——不需要修正。
- caustic 位置的解析核公式（#13、#29）、最小偏折 ≠ caustic 的警示（#16）、contact / nonempty 定理（#24）：本任务未触及，判定不变。

**Tape 三篇说不出的**（数值证据在互证 A 第 2、3 组）：
- 折叠 $M$ 这一维（#19）：`wedge_orientation(crystal, M, 3, 7, R)` 把 `3-4-5-7` 翻译成 Tape 楔时，$M$ 只用来算展开出射面 $-M^{-1}\mathbf n_7=-\mathbf n_5$，
  得到的 $u$ 与 `3-5` 的 $u$ **完全相同**——Tape 的楔对象在翻译中丢掉了 $M$，`halo_point` 给出的是幻日光点 $\mathbf H_{35}$ 而不是 $\mathbf H_{3457}$。
  片晶族里靠 Rule 1 补回来（$RMR^{-1}\in Z$），柱晶族里补不回来（$RMR^{-1}\mathbf k$ 偏 $\mathbf k$ 120°，Rule 1 前提失效，强行套用误差 17°–150°）。
  "需要怎样补一个折叠才等价"：在楔对象之外追加一个**固定在晶体上**的正交算子 $M$，光点公式改为 $\mathbf H=RMR^{-1}\mathbf F(u\mathbf N_0,u\mathbf X_0,\mathbf S)$；
  互证 A 第 3 组的"共轭式"列就是这个公式，它逐点等于本系列的 $\Phi_{3457}$。TK1999 p.15 那句"一次反射 → 一整本新 atlas"说的正是这个缺口。
- 34 类的存在与格子之间的关系（#20）：A60-10 与 A60-12 是"同一个楔 × 不同折叠"，这层关系在 Tape 的 atlas 里表示为"两张无关的图"或干脆不存在（柱晶）。
- 姿态分布 $\rho$ 与强度（#17、#30）：本任务两侧都不算强度，判定不变；141.84° 与 142.56° 的差正是"几何锐边"与"带 $\rho$、角径的渲染半高"之间的距离。

**矩阵法说不出的**（本任务不触及、判定不变）：caustic 强度的解析度量之外的几何直觉工具——contact circle、Nonempty Halos Theorem、太阳高度变换规则（#24、#25）；
以及 atlas 这种按 $(\alpha,\text{pole})$ 连续组织的产品形态（#21）。

**一处需要子任务 4 注意的措辞**：本系列 `docs/framework.md` 定理 8 的 $\mathbf x=R\Phi_P(R^{-1}\mathbf s)$ 与代码的传播方向约定差两个负号（源笔记 §5、§7 第 7 条），
本任务在 `crosscheck_bridge.light_point` 里按严格写法 $-R\Phi(-R^{-1}\mathbf S)$ 实现并通过全部互证——这反过来是"framework 那行应改写"的数值证据，仍上抛、不在本任务改。
