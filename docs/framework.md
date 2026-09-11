# 现代冰晕理论骨架

> 系列 7–11 章共用的理论底稿。起源于 2026-09-11 作者与另一 assistant 的讨论（原文 `scratchpad/DRAFT-discussion-on-roadmap.md`，不入 git），2026-09-12 经本仓核验、修正与扩展后定稿于此。章节安排见 [roadmap.md](roadmap.md)。
>
> 每条结论标注证据等级：**[算]** = 已由 `docs/checks/` 下脚本数值核验；**[推]** = 解析推导，未另作数值核验；**[猜]** = 结构性断言，待穷举或仿真确认。

## 0. 对象链

$$
\underbrace{\text{face word}}_{\text{组合}}
\;\xrightarrow{\;\rho\;}\;
\underbrace{(M,\ \mathbf n_a,\ M^{-1}\mathbf n_b)}_{\text{signature}}
\;\longrightarrow\;
\underbrace{\Phi_P : S^2 \to S^2}_{\text{方向映射（晶体系）}}
\;\xrightarrow{\;R\;}\;
\underbrace{F_P : Q \to S^2}_{\text{halo map}}
\;\xrightarrow{\;\rho(q)\,w_P(q)\;}\;
\underbrace{\mu_{\rm sky}=(F_P)_*[\rho\,w_P\,dq]}_{\text{天空测度}}
$$

四层，各自独立可研究，写作时每章只待在一层：

| 层 | 问题 | 工具 | 章 |
|---|---|---|---|
| 组合 / 拓扑 | 哪些光路存在 | 枚举、可达性 | 1–2，8–9 |
| 群作用 / 方向几何 | 它们产生什么 locus | $O(3)$、共轭、等变映射 | 3，7–8 |
| 奇点 / 姿态 | locus 在哪里亮、什么形状 | Jacobian、纤维化、$SO(3)$ 上的分布 | 10–11 |
| 辐射度学 / 晶体统计 | 实际多亮、看不看得见 | Fresnel、截面、$\rho$ 的物理族 | 4–6，11 |

$M$ 是**运动学充分统计量**：压缩了光路的全部方向变换信息，丢掉了辐射度学（可实现入射区域、TIR、Fresnel、偏振、光程、截面）。两条 $M$ 相同的光路方向映射相同，亮度可以完全不同。

## 1. 平行光路：群论层（ch7）

**设定。** 六棱柱 8 个面，镜面反射 $S_{\mathbf n}=I-2\mathbf n\mathbf n^T$，$S_{\mathbf n}=S_{-\mathbf n}$，故只有 4 个不同镜面：3 个侧面方向（$xy$ 平面内相距 60° 的三条反射轴）+ 1 个底面 $b=\mathrm{diag}(1,1,-1)$。

**定理 1（十二）[算]。** 4 个镜面生成的群 $G$ 恰有 12 个元素，$G\cong D_3\times C_2\cong D_{3h}$（$D_{6h}$ 的指数 2 子群）。字长 ≤ 3 即饱和（闭包增长 1, 5, 10, 12, 12, …）。ch3 工作笔记列出的 12 个矩阵正是 $G$ 的全部元素。推论：**无论内反射多少次，理想六棱柱的平行光路方向变换只有 12 种**——ch3 的「长度 ≤ 6」限制可以去掉。

**定理 2（六类）[算]。** ch3 发表的 6 类晕 = $G$ 的 6 个共轭类，逐一对应：

| $G$-共轭类 | 矩阵编号（ch3 笔记） | 柱晶 | 片晶 |
|---|---|---|---|
| $\{bs, brs, br^2s\}$ | 1, 7, 9 | 对日点弥散 | 映幻日环 |
| $\{s, rs, r^2s\}$ | 2, 8, 10 | 太阳弥散 | 幻日环 |
| $\{br, br^2\}$ | 3, 5 | 特里克尔弧 | 映 120° 幻日 |
| $\{r, r^2\}$ | 4, 6 | 映偕日弧 | 120° 幻日 |
| $\{b\}$ | 11 | 幻日环 | 映日 |
| $\{e\}$ | 12 | 太阳原像 | 太阳原像 |

**修正（特征值是歧路）[算]。** ch3 正文与存档提纲暗示「从特征值入手划分等价类」。按特征值 / Jordan 型只得 5 类：#11（底面反射）会并进 #2/8/10（侧面反射）——它们都是一次反射，在 $O(3)$ 中共轭。但物理上 #11 是幻日环、#2 是弥散。原因：特征值是 **$O(3)$ 共轭不变量**，而晕的形状只在**晶体对称群（更准确说是姿态分布的稳定子群）下的共轭**不变；把底面镜换成侧面镜的那个旋转不在晶体对称群里。这正面回答了 ch2/ch3 提纲里「需要引入进一步的对称性」是什么：**不变量必须是正确的那个群下的不变量。**

**定理 3（四锐两散）[算]。** 与 $R_z(\theta)$ 对易的元素恰为 $\{3,4,5,6,11,12\}$，即 $xy$ 分块为旋转（含单位）的元素；$xy$ 分块为反射的 $\{1,2,7,8,9,10\}$ 不对易。晕的维数
$$
\dim(\text{晕}) = \dim Q - \dim \mathrm{Stab}_Q(M),
$$
柱晶 $Q$ 二维：对易者得弧（特里克尔、映偕日、幻日环）或点，不对易者得二维弥散区；片晶 $Q$ 一维：对易者得点（120° 幻日、映日、太阳），不对易者得圆（幻日环、映幻日环）。这是 ch3 结尾「且听下回分解」的答案。

**几何意义 [推]。** $T=RMR^{-1}$ 是共轭作用：$M$ 是与坐标无关的光路本体，$R$ 是晶体姿态，天上看到的是 $M$ 的共轭轨道作用于太阳方向。特里克尔弧的 $\theta$ 消失 ⇔ $M\in C_G(SO(2)_z)$。

## 2. 非平行光路：等变分解（ch8）

**折射算子。** 用光学动量 $\mathbf p=n\hat{\mathbf r}$ 写 Snell：切向分量守恒，只改法向分量，$\mathbf p'=\mathbf p_\parallel+\sigma\sqrt{n_2^2-\|\mathbf p_\parallel\|^2}\,\mathbf n$（根号内负则 TIR）。ch3 工作笔记「推导一下楔角光路」是同一公式的单位向量形式。

**引理（旋转等变）[推]。** 对任意 $Q\in O(3)$，$\mathcal S_{Q\mathbf n}(Q\mathbf r)=Q\,\mathcal S_{\mathbf n}(\mathbf r)$。（公式只含内积与线性组合，显然。）

**定理 4（楔 × 折）[推]。** 从面 $a$ 入、内反射总矩阵 $M$、从面 $b$ 出的光路，方向映射
$$
\Phi_P=\mathcal S_{\mathbf n_b}\circ M\circ\mathcal S_{\mathbf n_a}
= M\circ\underbrace{\mathcal S_{M^{-1}\mathbf n_b}\circ\mathcal S_{\mathbf n_a}}_{W_{\mathbf n_a,\tilde{\mathbf n}_b}},
\qquad \tilde{\mathbf n}_b=M^{-1}\mathbf n_b .
$$
$\tilde{\mathbf n}_b$ 是把内反射全部展开后出射面在展开空间中的法向：**任意复杂光路 = 一个展开后的楔角折射 $W$ + 一个最终折叠 $M$**。Tricker 的万花筒展开与矩阵法在此合流；Tape 的 wedge theory（Tape & Können 1999）恰好是 $W$ 这一半。平行光路 = $\tilde{\mathbf n}_b=-\mathbf n_a$，$W=I$，$\Phi=M$，是一般理论的退化子类。ch3 笔记里的 $c_\theta=\mathbf n_N^T M\mathbf n_1$ 就是楔角余弦；当年「没什么卵用」是因为在化简公式，它的用处在分类。

**定理 5（三种楔）[算]。** $G$ 置换面法向集合，故 $\tilde{\mathbf n}_b$ 仍是 8 个面法向之一。遍历 $M\in G$ 与所有面对，$\langle\mathbf n_a,M^{-1}\mathbf n_b\rangle\in\{0,\pm\tfrac12,\pm1\}$，楔角 $A$（$\cos A=-\langle\mathbf n_a,\tilde{\mathbf n}_b\rangle$）$\in\{0°,60°,90°,120°,180°\}$；$n=1.31$ 下可透射上限 $2\arcsin(1/n)\approx99.5°$，有效楔只有 **0° / 60° / 90°**（平行、22° 族、46° 族），120° 全反射死角。故**六棱柱任意长度光路的方向映射 ⊆ 3 种楔 × 12 种折叠**，再商掉晶体对称与不可达组合。

**signature 与穷举 [猜]。** 两条光路方向映射相同 ⇐ $(M,\mathbf n_a,\tilde{\mathbf n}_b)$ 相同；商掉晶体对称后的规范型即 canonical signature。用 ch2 枚举器对每条可达光路算 signature，得到不同 $\Phi$ 的实际类数——这是 ch8 的计算交付，尚未做。逆命题（$\Phi$ 相同 ⇒ signature 相同）一般成立但未证。

## 3. 锥晶：结构 vs 巧合（ch9）

**设定 [算]。** ice $c/a=1.6288$，$\{10\bar11\}$ 锥面法向与 c 轴夹角 $\arctan\!\big(\tfrac{2}{\sqrt3}\tfrac{c}{a}\big)=62.0°$。20 个面 = 2 底 + 6 侧 + 12 锥；锥面成 ± 对，镜面方向共 1+3+6 = 10 个。

**定理 6（十二死了）[算]。** 镜面群闭包按字长增长：

| 字长 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| 柱晶 | 1 | 5 | 10 | 12 | 12 | 12 | 12 | 12 | 12 |
| 锥晶 | 1 | 11 | 70 | 372 | 1884 | 9444 | 47244 | 236244 | 1181244 |

锥晶群无限（有限反射群必须是 Coxeter 群，镜面夹角须为 $180°/m$；60°、90° 是，62° 不是）。**定理 1 是六棱柱的晶体学巧合，不是框架的定理。** 定理 4（分解）与 signature 不依赖群有限，幸存；方向映射类数的有限性改由**可达性**（TIR、几何相交对字长的封顶）保证，而非代数。

**定理 7（九种楔）[算]。** 同一公式扫 20 个面，可透射楔角恰 9 个：

| 楔角 | 0 | 28.0 | 52.4 | 56.0 | 60 | 62.0 | 63.8 | 80.2 | 90 |
|---|---|---|---|---|---|---|---|---|---|
| 晕 | 平行光路族 | 9° | 18° | 23° | 22° | 20° | 24° | 35° | 46° |

整个 odd-radius 晕家族由单参数 $c/a$ 决定；Tape *Atmospheric Halos and the Search for Angle x* 找的锥面角在此是一个参数。（不可透射：99.8, 116.2, 118, 120, 124, 127.6, 152, 180。）

## 4. 聚光：纤维化与两种机制（ch10）

**定理 8（半径归光路，方位归姿态）[推]。** 固定光路 $P$ 与太阳方向 $\mathbf s$。令 $\mathbf u=R^{-1}\mathbf s$（太阳在晶体系中的方向），$\{R: R\mathbf u=\mathbf s\}$ 是绕 $\mathbf s$ 的圆 $\mathrm{Rot}_{\mathbf s}(\theta)R_0(\mathbf u)$，于是 $SO(3)\cong$ 以 $S^2\ni\mathbf u$ 为底的主 $SO(2)$ 丛，Haar 测度 $=d\mathbf u\,d\theta$。代入 $\mathbf x=R\,\Phi_P(R^{-1}\mathbf s)$：
$$
\angle(\mathbf x,\mathbf s)=\angle(\Phi_P(\mathbf u),\mathbf u)=D_P(\mathbf u)\quad\text{与 }R\text{ 无关},
$$
$$
\mu_{\rm sky}=\int_{S^2}\!d\mathbf u\,w_P(\mathbf u)\int_0^{2\pi}\!d\theta\;\rho\big(\mathrm{Rot}_{\mathbf s}(\theta)R_0(\mathbf u)\big)\,\delta\big(\mathbf x-\mathrm{Rot}_{\mathbf s}(\theta)R_0(\mathbf u)\Phi_P(\mathbf u)\big).
$$
出射点到太阳的角距离只由晶体系内的偏折角决定；姿态分布只决定每个太阳同心圆在方位上的填充。ch10 讲径向因子 $D_P(\mathbf u)$，ch11 讲方位因子 $\rho$。

**两种机制 [推]。** 设 halo map $F_P:Q\to S^2$，$Q$ 为姿态族。

| | dimension collapse | Jacobian focusing |
|---|---|---|
| 条件 | $DF$ 沿某方向**恒**为零 | $DF$ 只在特殊姿态集合上降秩 |
| 来源 | 精确对称：$M\in C_G(\text{姿态子群})$ | 奇点：$\det DF\to0$ |
| 典型 | 平行光路（特里克尔弧的 $\theta$ 整维压扁） | 22° 晕：$D(i)\simeq D_{\min}+\tfrac12D''(i-i_0)^2$ |
| 局部律 | 整维贡献到同一位置 | $I(D)\sim\sum_{u:F(u)=D}\rho(u)/\lvert dD/du\rvert\sim 1/\sqrt{D-D_{\min}}$（fold） |
| 文献 | — | Tape 1980 *Analytic foundations*：caustic = halo function 奇点集的像；1983 fold / pleat |

非平行楔一般没有连续稳定子（$\mathbf n_1,\mathbf n_2,\mathbf n_1\times\mathbf n_2$ 已钉死朝向），所以 centralizer 语言只对平行光路有效，一般晕的聚光机制是奇点，不是对称。draft 早先把 centralizer 提得太重，此处已修正。发散被太阳 0.5° 角径、姿态扰动、晶面缺陷、波动光学卷积平滑。

**与 4–6 章的关系 [推]。** $\mu_{\rm sky}=(F_P)_*[\rho\,w_P\,dq]$ 就是 ch4 的渲染方程；ch6 的蒙特卡洛与直接积分是算这个 pushforward 的两条路。亮度的三个来源：大纤维（精确不变）、Jacobian 奇点、权重 $\rho\,w$（片晶偏好水平、有效截面、Fresnel、TIR）。

## 5. 姿态分布：方位因子与线性性（ch11）

**卷积比喻的精确版 [推]。** 定理 8 的内层积分：

- $\rho$ 均匀（Haar）：内层与 $\mathbf u$ 脱耦，天空图案 = 太阳盘 $*$ 带状核 $f(D)$（$D_P(\mathbf u)$ 的 pushforward）的**球面卷积**。比喻严格成立；22° 圆晕的径向剖面就是 $f$。
- $\rho$ 非均匀（片 / 柱 / Parry / Lowitz）：纤维化积分，**不是天空上的卷积**——每个半径圆被 $\rho$ 沿纤维切片式填充（片晶把 3-5 光路的 22° 圆只填两点 = 幻日；柱晶填上下两段 = 相切弧）。
- 真正的卷积核在 **$SO(3)$ 上**：$\rho=\rho_0 * k_\sigma$（理想族 $*$ 倾角扩散核，群卷积）。天空上的模糊是 $F$ 把它推过去的像，$DF$ 大处糊得多，$DF$ 降秩处（caustic）糊不动——这是 ch10/11 的接口。

**姿态族 [推]。** 随机（Haar，3 维）/ 片（c 轴竖直，1 维）/ 柱（c 轴水平，2 维）/ Parry（c 轴水平 + 一侧面水平，1 维）/ Lowitz，各带扩散 $\sigma$。同一光路 × 五族 = 五种晕（3-5：圆晕 / 幻日 / 相切弧 / Parry 弧 / Lowitz 弧）。$\dim(\text{晕})=\dim Q-\dim(\text{纤维})$ 是定理 3 的一般化。

**定理 9（线性）[推]。** 单次散射下 $\mu_{\rm sky}=\sum_P c_P\,\mathcal A_P[\rho]$，$\mathcal A_P$ 是从 $SO(3)$ 上的测度到 $S^2$ 上的测度的**线性算子**；全部非线性（Snell、Fresnel、可达性）在 $\Phi_P,w_P$ 内，不含 $\rho$。推论：

- 反向问题是**线性反问题**（Radon / 层析型），未知量 $(\rho, c_P)$。
- Hough 投票（ch12）= 伴随算子 $\mathcal A_P^{\top}$（backprojection）——Hough 与 Radon 的经典关系。
- 可微渲染（ch13）= 同一算子的正则化求解。
- 2 维图像反演 3 维 $\rho$ 欠定；正则化来自物理先验（$\rho$ 属于上述参数族）。参数化反演 vs 非参数投票，是第二部分的两条路。

**整体形状。** 正向理论是一张表：**行 = 光路类**（定理 1–7 给，有限），**列 = 姿态族**（本节给），格子形状由 $(F,DF)$ 裁定（第 4 节）。反向问题 = 给一张天空图，找哪些格子亮、亮多少。

## 6. 与文献的关系

| 路线 | 对象 | 备注 |
|---|---|---|
| Tricker 1973 *kaleidoscope* | 光线几何构造，展开 / 折叠 | 对应 $\tilde{\mathbf n}_b=M^{-1}\mathbf n_b$ 的展开空间 |
| Tape 1979 *Geometry of halo formation*；1980 *Analytic foundations* | 取向空间 → 光点空间的映射；caustic = 奇点集的像 | 对应 $F_P$ 与 $DF$（第 4 节） |
| Tape & Können 1999 *A general setting for halo theory* | 一般楔角的 wedge theory | 对应 $W$（定理 4 的一半） |
| Tape *Angle x* | 锥面角 | 对应参数 $c/a$（定理 7） |
| 本系列 | 先把 ray path 商成 $O(3)$ 算子，再研究群作用；把「光路是什么」与「晶体怎么摆」解耦 | $M$ 与 $R$ 分离；定理 8 是这一解耦的精确形式 |

古典几何擅长解释一个实例，现代代数擅长分类一个结构；冰晕兼有强几何直观与巨大组合空间，是后者的用武之地。

## 7. 未决

- [猜] 定理 4 signature 的完备性（$\Phi$ 相同 ⇒ signature 相同）。
- [猜] 六棱柱 / 锥晶在字长上限下不同 $\Phi$ 的实际类数（ch8 / ch9 的穷举交付）。
- [猜] 柱晶（$Q$ 二维、三维）下 22° 晕的奇点类型（fold / cusp / pleat）的数值确认。
- 锥晶的 $\Phi$ 类数是否随字长上限收敛，收敛速度——决定 ch9 穷举的截断。
- 姿态族 $Q$ 非光滑（Parry 与柱晶混合）时定理 8 内层积分的处理。

## 附：核验脚本

- `07-reflection-group/code/check_group.py` — 定理 1、2、3、5，及「特征值只得 5 类」。
- `docs/checks/check_pyramid.py` — 定理 6、7。

ch7 / ch9 bootstrap 时迁入各章 `code/`。
