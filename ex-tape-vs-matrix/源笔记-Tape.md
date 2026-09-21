---
type: note
---
# 源笔记：Tape 三篇主源 ↔ 本系列对象

> 番外「Tape 光点法与矩阵法」的文献源笔记（scrum `ex-tape-prep` 子任务 2）。子任务 3（数值互证）**只能按本笔记抄下来的公式实现**，子任务 4（提纲）只能引用本笔记里带页码的断言。不在本机的文献（Tape 1994、Tricker 1970）一律进 §7 清单，正文不写；作者后来补入的 Tricker 1973 作为历史一手源，单列 §T。
>
> **引注约定**：`[Tape1980 p.N]` / `[TK1999 p.N]` / `[TM2006 p.N]` / `[Tricker1973 p.N]` / `[Können1983 p.N]` / `[Können1998 p.N]` 的 N 一律是**本机 PDF 的页序号**（共享目录 `scratchpad/refs/`，旧路径 `scratchpad/scrum-ex-tape-prep/refs/` 是 symlink；均不入 git）。换算：Tape1980 期刊页 = 1174 + N（JOSA 70, 1175–1192）；TK1999 期刊页 = 1551 + N（Appl. Opt. 38, 1552–1625）；TM2006 书页 = N − 10（第 1 章起于 PDF p.11 = 书页 1）；Tricker1973 期刊页 = 648 + N；Können1983 期刊页 = 1628 + N；Können1998 期刊页 = 1449 + N。引文里的公式编号（Eq. (20)、Eq. (8.1) 等）是原文编号。
>
> **本系列记号**（以 `docs/framework.md` 与 ch8 正文为准）：$\mathbf n_a$ 入射面外法向、$\mathbf n_b$ 出射面外法向、$M$ 内反射总矩阵、$\tilde{\mathbf n}_b=M^{-1}\mathbf n_b$ 展开后的出射面法向、$W=\mathcal S_{\tilde{\mathbf n}_b}\circ\mathcal S_{\mathbf n_a}$ 楔角折射、$\Phi_P=M\circ W$ 方向映射、楔角 $A$ 满足 $\cos A=-\langle\mathbf n_a,\tilde{\mathbf n}_b\rangle$（= 180° − 两外法线夹角，**只用「楔角」一个词**）、$R\in SO(3)$ 晶体姿态、$F_P:Q\to S^2$ halo map、$\mathbf u=R^{-1}\mathbf s$ 太阳在晶体系中的方向、$D_P(\mathbf u)=\angle(\Phi_P(\mathbf u),\mathbf u)$ 偏折角、$\rho$ 姿态分布。面编号：底面 1（+z）、2（−z），侧面 3–8 从 +x 起逆时针（`lumice_integral.geometry.HexPrism`：$\mathbf n_3=(1,0,0)$、$\mathbf n_4=(\tfrac12,\tfrac{\sqrt3}{2},0)$、…）。

## 0. 三篇文献各自在做什么（一句话定位）

- **Tape 1980**：把「天球上的光点作为晶体取向的函数」写成一个显式的解析映射 $F$（halo function），用微分拓扑的语言（Jacobian 的核、奇点集、fold/pleat）算晕的 caustic。对象是**单个楔（两次折射，无内反射）**，晶体形状从头到尾只以楔角 $\alpha$ 出现 [Tape1980 p.1]。
- **Tape & Können 1999**：不预设楔角与取向，把「所有可能的折射晕」组织成一本 atlas；每个晕由三个参数决定：楔角 $\alpha$、spin vector 的天顶角 $\psi$、spin vector 在楔坐标系里的表达 $\mathbf P_u$（pole）[TK1999 p.1]。核心技巧是「骑在楔子上」看世界（zenith locus / sun locus）。同样只处理**纯折射**光路 [TK1999 p.15]。
- **Tape & Moilanen 2006**：面向普通读者的成熟版：光点图（light point diagram）讲折射定律 [TM2006 p.48–50]，spin vector / halo pole 讲取向 [TM2006 p.143, p.147]，主线是锥晶的 Angle x [TM2006 p.7, p.123]。理论上没有超出 1999，但术语与几何直觉更成熟，且把 1999 的 pole 概念归于 Können [TM2006 p.147]。

三篇合起来 = 本系列 $\Phi_P=M\circ W$ 里 **$W$ 那一半** + 「取向空间 → 光点」这个映射的奇点分析；**折叠 $M$ 的分类在三篇里都不存在**（详见 §4、§6）。

## T. Tricker 1973：长六棱柱作为万花筒

- **范围**：论文研究长六棱柱水平飘浮时的 heliacal / anthelic arcs。光从一个底面进入，在侧面间多次全反射后，从另一底面射出，或再经后端面反射后从原底面射出 [Tricker1973 p.1, p.4]。它不计算 22° 幻日，也不建立一般楔理论。
- **万花筒构造是一手原文**：Tricker 把六个侧面延长为过晶体轴的反射平面，令 $S_1$ 为太阳方向 $S_0$ 关于其中一面的像，$S_4$ 等为继续关于下一面反射所得的像；一次、两次、三次侧面反射分别对应这些逐次镜像后的出射方向 [Tricker1973 p.4, Fig. 4]。原文随后明确说这套理论与简单万花筒相同 [Tricker1973 p.4]。
- **折射为什么能退出问题**：侧面反射不改变光线对底面的入射角，只旋转入射面；从平行的另一底面射出时，出射折射与入射折射大小相等、方向相反 [Tricker1973 p.4]。所以 $S_0$ 方向保持不变，其余像落在以晶体轴 $R$ 为极、过太阳的小圆上 [Tricker1973 p.4]。
- **用本系列语言翻译**：逐次镜像就是逐次乘反射，合成为 $M$；两底面平行且入、出折射抵消，故展开楔为 $0°$、$W=I$，最终 $\Phi=M$。这给 ch3 的平行光路与 ch7 的反射矩阵提供了非常贴切的历史先例。
- **边界必须写明**：Tricker 1973 直接支持的是 $W=I$ 的「纯折叠」一半，而不是任意首尾面的 $\Phi=M\circ W$ 分解，也没有 signature / 群商分类。ch8 所说「Tricker 的万花筒展开与矩阵法合流」可以保留，但精确含义应是：Tricker 的逐次镜像在矩阵语言里合成为 $M$；一般非平行光路再由本系列补上 $W$。
- **与 Tape 光点术语的关系**：Tricker 在天球上谈太阳的 images 与光束的 origin / direction，没有在这篇论文中使用可确认的 “light point” / “light point diagram” 术语。因此它不能解决 Tricker 1970 是否采用同心圆作图或如何命名的问题。

## 1. Tape 1980 *Analytic foundations of halo theory*

### 1.1 设定与记号（§I）

- 忽略反射光线与衍射，问题归结为「光在一个楔（wedge）里的折射」[Tape1980 p.1]。记号（原文逐条，p.1–2）：
  - $n$：折射率（$n>1$，图中取 1.31）；normal plane：同时垂直楔两面的平面 [Tape1980 p.1]。
  - $\hat{\mathbf N}$：入射面**外**法向；$\hat{\mathbf N}_1$：入射面**内**法向；$\hat{\mathbf N}_2$：出射面**外**法向 [Tape1980 p.1]。
  - axial vector $\hat{\mathbf P}$：$\hat{\mathbf N}_1\times\hat{\mathbf N}_2$ 方向的单位向量；normal plane 内所有角的符号由 $\hat{\mathbf P}$ 按右手定则决定 [Tape1980 p.1]。
  - refracting angle $\alpha$：从 $\hat{\mathbf N}_1$ 到 $\hat{\mathbf N}_2$ 的角，$0<\alpha<180$，最重要的值是 60 与 90 [Tape1980 p.1]。所有角度用度 [Tape1980 p.2]。
  - $\hat{\mathbf I}$：入射光线方向单位向量；$\hat{\mathbf R}$：出射（两次折射后）光线方向单位向量；$\mathbf I_p,\mathbf R_p$：二者在 normal plane 上的投影 [Tape1980 p.2]。
  - $\mu$：从 $\mathbf I_p$ 到 $\hat{\mathbf N}_1$ 的角（投影入射角）；$r$：入射面处投影折射线到 $\hat{\mathbf N}_1$ 的角；$\mu'$：出射面处投影入射线到 $\hat{\mathbf N}_2$ 的角；$r'$：从 $\mathbf R_p$ 到 $\hat{\mathbf N}_2$ 的角；$D$：从 $\mathbf I_p$ 到 $\mathbf R_p$ 的角（normal plane 内的偏折）；$\Delta$：$\hat{\mathbf I}$ 与 $\hat{\mathbf R}$ 的夹角（真实偏折），$0\le\Delta\le180$；$\theta$：$\hat{\mathbf P}$ 与 $-\hat{\mathbf I}$ 的夹角，$0\le\theta\le180$；$n'=(n^2-\cos^2\theta)^{1/2}/\sin\theta$：Bravais 折射率 [Tape1980 p.2]。
- Bravais 定律（Snell 的推论）把三维折射化为 normal plane 内的折射：(b1) $\hat{\mathbf P}$ 与 $\hat{\mathbf I}$ 的夹角等于 $\hat{\mathbf P}$ 与 $\hat{\mathbf R}$ 的夹角；(b2) 三条投影光线像在折射率为 $n'$ 的介质里折射一样 [Tape1980 p.2]。
- normal-plane 偏折 $D(\theta,\mu)$ 的计算链 [Tape1980 p.2, Eqs. (1)–(4)]：
  $$\sin r=\frac{\sin\mu}{n'},\qquad \mu'=r+\alpha,\qquad \sin r'=n'\sin\mu',\qquad D=\alpha+\mu-r'.$$
- $D$ 的定义域 [Tape1980 p.2, Eqs. (5)–(6)]：
  $$\overline{\mathcal D}=\{(\theta,\mu)\mid \theta_{\min}\le\theta\le180-\theta_{\min},\ -90\le\mu\le\mu_L(\theta)\},$$
  $$\sin\mu_L(\theta)=\cos\alpha-(n^2-1)^{1/2}\frac{\sin\alpha}{\sin\theta},\qquad \sin\theta_{\min}=(n^2-1)^{1/2}\tan(\alpha/2).$$
  $\mu=-90$ 是掠入射，$\mu=\mu_L(\theta)$ 是掠出射；由 (6) 得光能通过楔的条件 $\sin(\alpha/2)\le n^{-1}$ [Tape1980 p.2]。
- 固定 $\theta$ 时 $D$ 的极值：$\partial D/\partial\mu=0\iff\mu=\mu_M(\theta)$，$\sin\mu_M(\theta)=-n'(\theta)\sin(\alpha/2)$ [Tape1980 p.2, Eq. (10)]；$D_{\min}(\theta)=\alpha+2\mu_M(\theta)$、$D_{\max}(\theta)=\alpha+\mu_L(\theta)-90$，且 $-180<D<0$（$D$ 恒负，"minimum" 指 $|D|$ 的最小，见 note 17）[Tape1980 p.2, Eqs. (11)–(12); p.18 note 17]。
- 真实偏折与投影偏折的关系 [Tape1980 p.3, Eq. (15)]：
  $$\sin(\Delta/2)=-\sin\theta\,\sin(D/2).$$
  Proposition 1：$\Delta$ 的最小值**只**在 $(\theta,\mu)=(90,\mu_M(90))$ 取到，即 $\Delta_{\min}=-D_{\min}(90)$；最大值在 $(\theta_{\min},-90)$、$(180-\theta_{\min},-90)$ 或 $(90,-90)$、$(90,\mu_L(90))$ 取到，取决于 $\alpha$ 与 $n$ [Tape1980 p.3; 证明 p.16]。

### 1.2 halo function：定义域、值域、显式公式（§IV, §VII）

- **值域**：单位天球。太阳放在 $(\cos\Sigma,0,\sin\Sigma)$，$\Sigma$ 是太阳高度；把 $xyz$ 轴绕 $y$ 轴转 $-\Sigma$ 得 $uvw$ 轴，此后向量都用 $uvw$ 坐标，太阳成为 $\hat{\mathbf S}=(1,0,0)$ [Tape1980 p.4]。
- **取向坐标** $(\theta,\mu,\beta)$：取 $0\le\theta\le180$，$\hat{\mathbf P}=(\cos\theta,\sin\theta,0)$ 在 $uv$ 平面右半；$\mathbf B$ 是 $\hat{\mathbf S}$ 在 $\hat{\mathbf P}$ 上的投影，$\mathbf{BA}$ 由 $\mathbf{BS}$ 绕 $\hat{\mathbf P}$ 转 $\gamma$ 得到，则 [Tape1980 p.4, Eq. (19)]
  $$A(\theta,\gamma)=\begin{pmatrix}\cos^2\theta+\cos\gamma\sin^2\theta\\ (1-\cos\gamma)\cos\theta\sin\theta\\ -\sin\gamma\sin\theta\end{pmatrix}.$$
  轴向量为 $\hat{\mathbf P}=(\cos\theta,\sin\theta,0)$、投影入射角为 $\mu$ 的取向，其光点是 $A(\theta,D(\theta,\mu))$（由 Bravais 定律，note 18）[Tape1980 p.4; p.18 note 18]。再把轴向量所在半平面绕 $u$ 轴转 $\beta$，得**halo function** [Tape1980 p.4, Eq. (20)]：
  $$F(\theta,\mu,\beta)=R_\beta\big(A(\theta,D(\theta,\mu))\big),\qquad R_\beta=\text{绕 }u\text{ 轴转 }\beta.$$
- **定义域**：$\mathcal T$ 为实数 mod 360，$\overline{\mathcal F}=\overline{\mathcal D}\times\mathcal T=\{(\theta,\mu,\beta)\mid\theta_{\min}\le\theta\le180-\theta_{\min},\ -90\le\mu\le\mu_L(\theta)\}$；$F$ 在 $\overline{\mathcal F}$ 上连续，在内部 $\mathcal F=\mathcal D\times\mathcal T$ 上可微 [Tape1980 p.4]。
- 定义域是 $SO(3)$ 的子集：$\mathcal G$ = 全部取向 = special orthogonal group；$\overline{\mathcal F}\subset\mathcal G$ 是「能按 Fig. 1 通光」的那些元素；$\mathcal G$ 的元素可看成正交向量对 $(\hat{\mathbf P},\hat{\mathbf N})$（轴向量，入射面外法向）[Tape1980 p.12]。**所以 Tape 的定义域是 $SO(3)$ 的一个开子集（带边界），不是商空间**；对称性 $\beta\mapsto\beta+c$ 是显式坐标，不商掉。
- 两套自然坐标 [Tape1980 p.12]：$(\theta,\mu,\beta)$ 相对入射光自然（Bravais 定律形式简单）；晶体下落时对齐的是重力而非太阳，约束宜相对竖直方向写。$\theta,\beta$ 就是 $\hat{\mathbf P}$ 关于 $uvw$ 轴（$u$ 为极轴）的球坐标：$u=\cos\theta,\ v=\sin\theta\cos\beta,\ w=\sin\theta\sin\beta$ [Tape1980 p.12]。$\Sigma=90$ 时 $u^\circ v^\circ w^\circ$ 恰是 $z,y,-x$；两系关系 [Tape1980 p.12, Eq. (23)]：$u^\circ=u\sin\Sigma+w\cos\Sigma,\ v^\circ=v,\ w^\circ=-u\cos\Sigma+w\sin\Sigma$。
- $(\hat{\mathbf P},\hat{\mathbf N})$ 的 $uvw$ 坐标 [Tape1980 p.12, Eq. (24)]（$\hat{\mathbf N}=\mathbf{BA}$ 由 $-\mathbf I_p=\mathbf{BS}$ 绕 $\hat{\mathbf P}$ 转 $\mu$ 得到）：
  $$\hat{\mathbf P}=(\cos\theta,\ \sin\theta\cos\beta,\ \sin\theta\sin\beta),$$
  $$\hat{\mathbf N}=(\cos\mu\sin\theta,\ -\cos\mu\cos\theta\cos\beta+\sin\mu\sin\beta,\ -\cos\mu\cos\theta\sin\beta-\sin\mu\cos\beta).$$
  换到竖直系 $(z,y,-x)$ [Tape1980 p.13, Eqs. (25)–(30)]：
  $$z_P=\cos\theta\sin\Sigma+\sin\theta\sin\beta\cos\Sigma,\quad y_P=\sin\theta\cos\beta,\quad -x_P=-\cos\theta\cos\Sigma+\sin\theta\sin\beta\sin\Sigma,$$
  $$z_N=\cos\mu\sin\theta\sin\Sigma+(-\cos\mu\cos\theta\sin\beta-\sin\mu\cos\beta)\cos\Sigma,$$
  $$y_N=-\cos\mu\cos\theta\cos\beta+\sin\mu\sin\beta,$$
  $$-x_N=-\cos\mu\sin\theta\cos\Sigma+(-\cos\mu\cos\theta\sin\beta-\sin\mu\cos\beta)\sin\Sigma.$$
  若 $\hat{\mathbf M}$ 是 normal plane 内由 $-\hat{\mathbf I}_p$ 绕 $\hat{\mathbf P}$ 转 $\gamma$ 得到的单位向量，则 (28)–(30) 把 $\hat{\mathbf N}$ 换成 $\hat{\mathbf M}$、$\mu$ 换成 $\gamma$ 仍成立 [Tape1980 p.13]。
- 光点的符号约定：光点 $=-\hat{\mathbf R}$（note 18："Let $\hat{\mathbf P}=-\hat{\mathbf R}$ be the point of light on the celestial sphere determined by $\theta$ and $\mu$"，此处 $\hat{\mathbf P}$ 是 note 内临时记号，不是轴向量）；$\hat{\mathbf S}=-\hat{\mathbf I}$ [Tape1980 p.18 note 18]。
- $F$ 只依赖 $\alpha$ 与 $n$；选定二者后，把 $F$ 限制到定义域的不同子集就得到不同的晕 [Tape1980 p.1; p.13; p.16 §X]。

**本系列记号重写**（结构对照，不是逐字翻译）：
- $\hat{\mathbf N}_1=-\mathbf n_a$，$\hat{\mathbf N}_2=\tilde{\mathbf n}_b$（Tape 只有一个楔，$M=I$，$\tilde{\mathbf n}_b=\mathbf n_b$）。于是 $\cos\alpha=\langle\hat{\mathbf N}_1,\hat{\mathbf N}_2\rangle=-\langle\mathbf n_a,\mathbf n_b\rangle=\cos A$：**Tape 的 refracting angle $\alpha$ = 本系列楔角 $A$**。
- $\hat{\mathbf P}\parallel\hat{\mathbf N}_1\times\hat{\mathbf N}_2=-\mathbf n_a\times\mathbf n_b$：楔棱方向。
- $(\theta,\mu)$ 是太阳方向在楔坐标系里的球坐标：$\theta$ = 太阳方向 $\hat{\mathbf S}=-\hat{\mathbf I}$ 与楔棱 $\hat{\mathbf P}$ 的夹角，$\mu$ = 绕楔棱、从 $\hat{\mathbf N}_1$ 量起的方位。即 $(\theta,\mu)\leftrightarrow\mathbf u=R^{-1}\mathbf s\in S^2$。
- $\beta$ 是绕太阳方向 $\hat{\mathbf S}$（$u$ 轴）的旋转 = **定理 8 纤维化的纤维坐标** $\mathrm{Rot}_{\mathbf s}(\theta)$。Eq. (20) 的形状 $F=R_\beta\circ A\circ(\mathrm{id},D)$ 就是 $F_P(R)=\mathrm{Rot}_{\mathbf s}(\beta)\,\big[\text{只依赖 }\mathbf u\text{ 的部分}\big]$；Eq. (15) 说 $\Delta$ 只依赖 $(\theta,\mu)$ 不依赖 $\beta$ = 定理 8 的「$\angle(\mathbf x,\mathbf s)=D_P(\mathbf u)$ 与 $R$ 无关」。**定理 8 的纤维化在 Tape 1980 §IV 里已经以坐标形式存在**（Tape 的动机是「利用 Bravais 定律 + 把圆晕表示为旋转过的上切弧的叠加」[Tape1980 p.4]，不是姿态分布）。
- $\Delta(\theta,\mu)=D_P(\mathbf u)$；$D(\theta,\mu)$ 是它在 normal plane 上的投影版本（本系列没有对应物，是 Bravais 定律的产物）。

### 1.3 「限制到取向子集得到不同的晕」怎么说（§VII–IX）

- **generating set**：晕的 generating set $\overline{\mathcal N}$ = $\overline{\mathcal F}$ 中产生该晕的取向集合；$\mathcal N=\overline{\mathcal N}\cap\mathcal F$。为了用微积分算 caustic，**理想化为晶体不偏离其优先取向**：$\mathcal N$ 是 $\mathcal F$ 的子流形——开集、光滑曲面或光滑曲线，据此把晕分为三维、二维、一维晕 [Tape1980 p.13]。
- 三维晕 = 圆晕，$\mathcal N=\mathcal F$（所有取向）[Tape1980 p.13]；$F$ 在连通紧集 $\overline{\mathcal F}$ 上连续且关于 $\beta$ 旋转对称，像必是整个天球、以太阳或反日点为心的闭圆盘、或以太阳为心的闭环带；由 $0<\Delta<180$ 排除前两种，故圆晕是环带 [Tape1980 p.5]。
- 二维晕（$\mathcal N$ 为曲面）实例与约束方程 [Tape1980 p.13–14]：
  - 上/下切弧：$\hat{\mathbf P}$ 水平（Fig. 17，$\alpha=60$；46° 切弧 $\alpha=90$），由 (25) 得 $\cos\theta\sin\Sigma+\sin\theta\sin\beta\cos\Sigma=0$ [Eq. (31)]。
  - side arc：某个固定在晶体上、位于 normal plane 内的向量 $\hat{\mathbf M}$ 水平；$\gamma$ 是 $-\hat{\mathbf I}_p$ 到 $\hat{\mathbf M}$ 的角，$\lambda$ 是 $\hat{\mathbf M}$ 到 $\hat{\mathbf N}$ 的固定角，$\gamma=\mu-\lambda$；generating set 为 $\cos\gamma(\sin\theta\sin\Sigma-\cos\theta\sin\beta\cos\Sigma)-\sin\gamma\cos\beta\cos\Sigma=0$ [Tape1980 p.13]。
  - infralateral / supralateral：水平六方柱，$\alpha=90$；infralateral 底面进侧面出，$\hat{\mathbf N}$ 水平，$\lambda=0$；supralateral 侧面进底面出，$\hat{\mathbf N}_2$ 水平，$\lambda=90$ [Tape1980 p.13–14]。
  - Lowitz 弧：六方片晶绕六边形一条长对角线自旋（Tricker 提出，Mueller 等研究），自旋轴充当 $\hat{\mathbf M}$，$\alpha=60$；下 Lowitz $\lambda=30$，上 Lowitz $\lambda=90$，第三 Lowitz $\lambda=150$ [Tape1980 p.14]。
  - 统一形式：$\varphi=\lambda-90$（$\hat{\mathbf P}\times\hat{\mathbf M}$ 到 $\hat{\mathbf N}$ 的角），
    $$G(\theta,\mu,\beta)=a\sin(\mu-\varphi)+b\cos(\mu-\varphi)=0,\quad a=\sin\theta\sin\Sigma-\cos\theta\sin\beta\cos\Sigma,\ b=\cos\Sigma\cos\beta,$$
    $\varphi=-\alpha$（下 Lowitz、infralateral）、$0$（上 Lowitz、supralateral）、$\alpha$（第三 Lowitz、infralateral）[Tape1980 p.14, Eq. (32)]。
  - 画法：用 $(\theta,\mu)$ 参数化曲面 $\overline{\mathcal N}$，解出 $\beta=\beta(\theta,\mu)$（多值），$F(\theta,\mu,\beta(\theta,\mu))$ 扫出晕；Figs. 9–14 为立体投影 [Tape1980 p.14]。note 22：若想用像点疏密粗估强度，$\theta,\mu$ 不是好参数，因为等距的 $\theta,\mu$ 坐标线并不近似取向的均匀分布 [Tape1980 p.18 note 22]。
- 一维晕（$\mathcal N$ 为曲线）[Tape1980 p.16]：幻日假定来自 $\hat{\mathbf P}$ 竖直的晶体，由 (26)(27) 得 $\sin\theta\cos\beta=0$、$-\cos\theta\cos\Sigma+\sin\theta\sin\beta\sin\Sigma=0$，即水平线 $\beta=90,\ \theta=90-\Sigma$（左幻日，$y<0$）或 $\beta=-90,\ \theta=90+\Sigma$（右幻日）。上切弧是平面 $\beta=0$ 的像，每段圆弧对应固定 $\theta$；左幻日 = 上切弧 $\theta=90-\Sigma$ 那段转 90°。环天顶弧、环地平弧、各种 Parry 弧：$\hat{\mathbf P}$ 水平且入射面外法向与竖直方向成固定角 $\varphi$，同时满足 (31) 与 (32)；CZA：$\alpha=90,\varphi=0$；CHA：$\alpha=90,\varphi=-90$ [Tape1980 p.16]。
- 「圆晕是幻日的叠加」（Bravais）：$\overline{\mathcal F}$ 中每条线段 $\{(\theta_0,\mu,\beta_0)\mid-90\le\mu\le\mu_L(\theta_0)\}$ 是晶体绕固定轴向量的旋转，其像是一个「幻日」[Tape1980 p.12]。「圆晕是旋转过的上切弧的叠加」[Tape1980 p.4, p.12]。

**本系列对照**：generating set $\mathcal N$ = 姿态族 $Q$（ch11 的片/柱/Parry/Lowitz），$F|_{\mathcal N}=F_P|_Q$；三维/二维/一维晕 = $\dim Q$ = 3/2/1。Tape 说的「同一个 $F$、不同子集、不同的晕」[Tape1980 p.1, p.16] = framework §5「同一光路 × 五族 = 五种晕」。Tape 的理想化「不偏离优先取向」= 本系列 $\sigma\to0$；他明确没有 $\rho$（见 §4）。

### 1.4 奇点集、Jacobian 的核、caustic（§V–VI, §VIII）

- 定义：$f$ 是从 $r$ 维流形到 $s$ 维流形的可微映射，$X$ 是奇点若 Jacobian $Jf$ 在 $X$ 的秩小于 $\min(r,s)$；此时 $\ker Jf$ 比正常大，$f$ 在 $X$ 附近有异常的「bunching or collapsing」。若 $\mathcal N\subset\overline{\mathcal F}$、$f=F|_{\mathcal N}$，晕的 **caustic = $f$ 的奇点集的像**，是「相对多的取向点亮天球一小块」的地方，是多数晕的主导特征 [Tape1980 p.1]。
- Proposition 2（$JF$ 的核）[Tape1980 p.5, Eqs. (21)–(22)]：令 $\mathcal S=\{(90,\mu_M(90),\beta)\mid\beta\in\mathcal T\}$，$X=(\theta,\mu,\beta)\in\mathcal F$。(1) $X\notin\mathcal S$ 时 $\ker JF$ 一维，由
  $$\begin{pmatrix}\dfrac{\partial D}{\partial\mu}\cos\dfrac D2\sin\theta\\[6pt] -2\sin\dfrac D2\cos\theta-\dfrac{\partial D}{\partial\theta}\cos\dfrac D2\sin\theta\\[6pt] \dfrac{\partial D}{\partial\mu}\sin\dfrac D2\end{pmatrix}$$
  张成；(2) $X\in\mathcal S$ 时二维，由 $(0,1,0)^{\mathsf T}$ 与 $(\cos\frac D2,0,\sin\frac D2)^{\mathsf T}$ 张成。其中 [Tape1980 p.2, Eqs. (7)–(9)]
  $$\frac{dn'}{d\theta}=\frac{-(n^2-1)\cos\theta}{n'\sin^3\theta},\qquad \frac{\partial D}{\partial\theta}=\frac{-dn'/d\theta\ \sin\alpha}{\cos r\cos r'},\qquad \frac{\partial D}{\partial\mu}=\frac{\cos r'\cos r-\cos\mu'\cos\mu}{\cos r'\cos r}.$$
  核与 $\beta$ 无关 [Tape1980 p.5 Fig. 8 caption]。
- 圆晕的 caustic：$\mathcal S$ 是 $F$ 的奇点集，故 caustic $=F(\mathcal S)$；由 Prop. 1，$F(\mathcal S)$ 是晕的内圆边界，半径 $-D_{\min}(90)$（$\alpha=60$ 时 21.8，$\alpha=90$ 时 45.7）[Tape1980 p.5]。
- 纤维：在 $\mathcal F$ 上 $F$ 是三维流形到二维流形的可微映射；隐函数定理（局部淹没定理，note 20）说 $X\in\mathcal F-\mathcal S$ 处 $F$ 局部像投影 $(x_1,x_2,x_3)\mapsto(x_1,x_2)$，$Y$ 的原像是 $\mathcal F-\mathcal S$ 中的光滑曲线（原像定理，note 21）；**$\mathcal F-\mathcal S$ 是曲线的并，每条曲线上无穷多取向点亮同一点**，切向量在 $\ker JF$ 内；$Y$ 在 caustic 上时 $F^{-1}(Y)$ 恰一个取向 [Tape1980 p.5, p.12; p.18 notes 20–21]。
- 圆晕与最小偏折的关系：仅知 $\Delta$ 在 $(90,\mu_M(90))$ 取最小，只能得 $F(\mathcal S)$ 在 caustic 里，不能排除「caustic 是几个同心圆」——需要 Prop. 2。三维 generating set 需要**两个**塌缩方向（$\dim\ker JF=2$）才得到相对集中的光；$\mathcal F$ 每点至少有一个塌缩方向。物理图像：任意取向 $X\in\mathcal F$ 都能找到某种转动方式使出射光不变（$X\notin\mathcal S$）或只作无穷小改变（$X\in\mathcal S$），所以「绕轴旋转时出射光在最小偏折附近停留很久」这一观察**不**解释圆晕；关键是 $\mathcal S$ 上有两个这样的方向 [Tape1980 p.12]。
- 二维晕的 caustic 判据 [Tape1980 p.14]：$X\in\mathcal N$ 是 $F|_{\mathcal N}$ 的奇点 ⇔ $\ker J(F|_{\mathcal N})\ne0$ ⇔ $\ker JF$ 在 $X$ 含一个与曲面 $\mathcal N$ 相切的非零向量。Case (i) $X\in\mathcal S$：核二维，与切平面交非零，必是奇点；对应晕点同时在该晕与圆晕 caustic 上。Case (ii) $X\notin\mathcal S$：核一维，奇点 ⇔ 核向量垂直于 $\mathcal N$ 的法向量。对 side arc，$\mathcal N$ 的法向量是 $\nabla G$ [Tape1980 p.15, Eq. (33)]，caustic 由联立 $\nabla G\cdot\ker JF=0$ 与 $G=0$ 再作用 $F$ 得到 [Tape1980 p.15, Eq. (34)]；已数值求解并画进 Figs. 9–13，caustic 勾勒出 fold 与 pleat [Tape1980 p.15]。
- Whitney 定理：曲面到曲面的光滑映射，除罕见例外至多出现 fold 或 pleat；Figs. 9–13 的 fold 显眼，Figs. 11–12 可见 pleat；note 24：未解析核验这些奇点满足 fold/pleat 的技术条件 [Tape1980 p.14; p.18 note 24]。
- 最小偏折轨迹 ≠ caustic：曲线 $\theta\mapsto F(\theta,\mu_M(\theta),\beta)$ 是 minimum deviation locus；对上/下切弧（及一维的幻日）它在 caustic 上，过去其它晕的最小偏折轨迹曾被误认为 caustic；Figs. 9–13 中二者明显不同，这一区别 Tricker 已指出。对 side arc，最小偏折轨迹上「正确」的点只能是两个幻日 caustic 点或与圆晕 caustic 的切点 [Tape1980 p.15]。
- 一维晕的 caustic：$\mathcal N$ 的切向量落在 $\ker JF$ 里；左幻日的 caustic 是单点 $F(90-\Sigma,\mu_M(90-\Sigma),90)$，幻日最内点 [Tape1980 p.16]。
- 「pleat 真实吗」：上 Lowitz 的 pleat 来自近掠出射区域，应极弱；下 Lowitz 的 pleat 按 Mueller 仿真也不足以被看见 [Tape1980 p.15]。
- 自陈缺口 [Tape1980 p.16 §X]："Perhaps the most conspicuous deficiency in the theory is the lack of a simple analytic measure of the strength of the caustic"，理想上还应给出 caustic 对 generating set 扰动的稳定性。

**本系列对照**：奇点 = framework §4「Jacobian focusing：$DF$ 只在特殊姿态集合上降秩」；$\mathcal S$ = 22° 晕 $D(i)\simeq D_{\min}+\frac12D''(i-i_0)^2$ 的那条奇点线；Tape 的「二维晕 case (ii)」= $DF|_Q$ 降秩判据的显式版本。Tape 1980 自陈缺的「caustic 强度」，Können 1983 已经**部分补上**：在忽略 Fresnel 系数变化与晶体遮挡、视线方向晶体数相等、只取几何光学、优先取向完全实现这五个假设下，令 $I\propto dN/d\omega$，用近晕角 Taylor 展开得到简单解析强度分布，并解析描述 halo / halocaustic 的近晕角形状 [Können1983 p.1, p.3, p.10]。它仍不是任意姿态分布 $\rho$ 与光路权重 $w_P$ 下的一般 pushforward；framework §4 的 fold 局部律与 §5 的 $SO(3)$ 群卷积覆盖的是后一层。Tape 的「dimension collapse」不存在：他的 collapse 都是奇点型（非平行楔没有连续稳定子，framework §4 已注）。

### 1.5 文中给出的实例（晕、楔）

| 晕 | $\alpha$ | generating set | 页 |
|---|---|---|---|
| 圆晕（22°/46°） | 60 / 90 | $\mathcal N=\mathcal F$ | [Tape1980 p.5] |
| 上/下切弧 | 60（46° 切弧 90） | Eq. (31)，$\hat{\mathbf P}$ 水平，Fig. 17 | [Tape1980 p.13] |
| infralateral / supralateral | 90 | side arc，$\lambda=0$ / $90$，Fig. 18 | [Tape1980 p.13–14] |
| 下 / 上 / 第三 Lowitz | 60 | side arc，$\lambda=30/90/150$，Fig. 19 | [Tape1980 p.14] |
| 幻日 | 60 | $\beta=\pm90$，$\theta=90\mp\Sigma$ | [Tape1980 p.16] |
| CZA / CHA / Parry 族 | 90 / 90 / — | (31)∧(32)，$\varphi=0$ / $-90$ | [Tape1980 p.16] |

图：Fig. 3 上切弧（$\Sigma=0$）[p.3]；Fig. 8 $\overline{\mathcal F}$ 与纤维曲线 [p.5]；Fig. 9 infralateral 四个 $\Sigma$ [p.6–7]；Fig. 10 supralateral、Fig. 11 下 Lowitz [p.8]；Fig. 12 上 Lowitz、Fig. 13 第三 Lowitz [p.9]；Fig. 14 切弧 $\Sigma=20,50$ [p.10]；Figs. 15–16 奇点集与 caustic 单独画 [p.11]。

### 1.6 Tape 1980 的边界（他自己划的）

- 只有折射，无反射、无衍射 [Tape1980 p.1]；只有一个楔，晶体形状只以 $\alpha$ 进入 [Tape1980 p.13 "The halo function F depends only on the refracting angle and the index of refraction"]。
- 无强度：参数「取随机或加权值」会得到 Greenler 式的仿真，本文不做 [Tape1980 p.1]；note 4 承认 Greenler 的仿真给出强度信息 [Tape1980 p.18 note 4]。
- 取向理想化（不偏离优先取向）[Tape1980 p.13]。

## 2. Tape & Können 1999 *A general setting for halo theory*

### 2.1 wedge、楔角、wedge frame、取向矩阵（§1.C–1.E）

- 每个晕来自一个由两个半平面围成的理想化冰楔；跟踪太阳光穿过取各种规定取向的楔，画出**与出射光线方向相反**的天球点 [TK1999 p.2]。
- 记号：$\mathbf N$ 入射面**外**法向，$\mathbf X$ 出射面**内**法向（"N for eNtry, X for eXit"）[TK1999 p.3]。
- **wedge frame** [TK1999 p.3, Eq. (8)]：
  $$\mathbf A=\frac{\mathbf N+\mathbf X}{\|\mathbf N+\mathbf X\|},\quad \mathbf B=\frac{\mathbf N\times\mathbf X}{\|\mathbf N\times\mathbf X\|},\quad \mathbf C=\frac{\mathbf N-\mathbf X}{\|\mathbf N-\mathbf X\|},$$
  固定在楔上；$\mathbf B$ 沿折射棱（入射面与出射面的交线），$\mathbf C$ 垂直于棱并平分两面夹角，$\mathbf A$ 补齐右手系。入射面与出射面**事先指定**，光只准从指定入射面进 [TK1999 p.4]。
- **standard orientation**：$\mathbf A,\mathbf B,\mathbf C$ 与 $\mathbf i,\mathbf j,\mathbf k$ 重合（Fig. 5：棱沿 $y$ 轴，楔尖朝上、开口朝下，$\mathbf N$ 朝前右上、$\mathbf X$ 朝后左上）。**取向矩阵** $u$：行列式为 1 的正交矩阵，视为「从 standard orientation 出发把楔转到目标取向」，$u\mathbf i=\mathbf A,\ u\mathbf j=\mathbf B,\ u\mathbf k=\mathbf C$，即 $u$ 的列就是 $\mathbf A,\mathbf B,\mathbf C$——$u$ 就是 wedge frame 本身。每个晕对应一个楔取向集合 $U$，单位阵 $e$ 未必在 $U$ 中 [TK1999 p.4]。
- 标准取向下的法向 [TK1999 p.4, Eq. (10)]：
  $$\mathbf N_0(\alpha)=[\cos(\alpha/2),0,\sin(\alpha/2)],\qquad \mathbf X_0(\alpha)=[\cos(-\alpha/2),0,\sin(-\alpha/2)],$$
  **楔角 $\alpha$ = 入射面与出射面的夹角** [TK1999 p.4]。由 (10)，$\mathbf N_0\cdot\mathbf X_0=\cos\alpha$。
- 楔角上限：$\alpha_{\max}$ 由 Eq. (48) 令 $\theta_0=90$ 得，$n=1.31$ 时 $\alpha_{\max}=99.5$；更大的楔完全不通光 [TK1999 p.11]。

**本系列对照**：$\mathbf N=\mathbf n_a$，$\mathbf X=-\tilde{\mathbf n}_b$（内法向）。于是 $\cos\alpha=\mathbf N\cdot\mathbf X=-\langle\mathbf n_a,\tilde{\mathbf n}_b\rangle=\cos A$：**TK1999 的 $\alpha$ = 本系列楔角 $A$**，与 Tape 1980 的 $\alpha$ 一致。$\mathbf B\parallel\mathbf n_a\times(-\tilde{\mathbf n}_b)=-\mathbf n_a\times\tilde{\mathbf n}_b$，与 Tape 1980 的 $\hat{\mathbf P}\parallel\hat{\mathbf N}_1\times\hat{\mathbf N}_2=-\mathbf n_a\times\tilde{\mathbf n}_b$ **同向**：1980 的轴向量 $\hat{\mathbf P}$ = 1999 的 $\mathbf B$（1999 把字母 $\mathbf P$ 让给了 spin vector）。$\alpha_{\max}=99.5$ = 定理 5 的 $2\arcsin(1/n)\approx99.5°$。

### 2.2 Snell 定律 = 平行投影：halo point 公式（§1.C）

- 对正数 $n_1,n_2$ 与长度为 $n_1$、1 的向量 $\mathbf S,\mathbf N$ [TK1999 p.2, Eqs. (2)–(3)]：
  $$\mathrm{pr}(\mathbf S,\mathbf N,n_2)=\mathbf S+\lambda\mathbf N,\qquad \lambda(\mathbf S,\mathbf N,n_2)=\big[(\mathbf S\cdot\mathbf N)^2+n_2^2-n_1^2\big]^{1/2}-\mathbf S\cdot\mathbf N,$$
  即把 $\mathbf S$ 沿 $\mathbf N$ 方向平行投影到半径 $n_2$ 的球上（"$\mathbf N$-projection"）。
- 入射线 $\mathbf I$、折射线 $\mathbf J$ 长度取各自介质折射率，$\mathbf N$ 为从第二介质指向第一介质的单位法向，则 $\mathbf J=\mathrm{pr}(\mathbf I,-\mathbf N,n_2)$ [TK1999 p.3, Eq. (4)]。**光点**（light point）：光线的负向量，是该光线看上去点亮的天球点；$\mathbf S=-\mathbf I$、$\mathbf T=-\mathbf J$ 则 $\mathbf T=\mathrm{pr}(\mathbf S,\mathbf N,n_2)$ [Eq. (5)]，定义条件 $\mathbf S\cdot\mathbf N\ge0$（确实从要求的一侧入射）且 $\lambda$ 为实（有透射光）[TK1999 p.3]。
- 楔（$n_1=1,n_2=n$）：楔内光点 $\mathbf T=\mathrm{pr}(\mathbf S,\mathbf N,n)$ [Eq. (6)]；出射光点 [TK1999 p.3, Eq. (7)]
  $$\mathbf H=\mathbf F(\mathbf N,\mathbf X,\mathbf S)=\mathrm{pr}(\mathbf T,\mathbf X,1)=\mathrm{pr}\big[\mathrm{pr}(\mathbf S,\mathbf N,n),\mathbf X,1\big].$$
  $\mathbf S$ 是太阳时 $\mathbf H$ 是 **halo point**；$\mathbf S\to\mathbf H$ 只是两次投影的复合（Fig. 3：内球半径 1、外球半径 $n$）。全文取 $n=1.31$ [TK1999 p.3]。
- halo point 作为取向的函数 [TK1999 p.4, Eqs. (9), (11)]：
  $$\mathbf H=\mathbf F(u\mathbf N_0,u\mathbf X_0,\mathbf S)=:\mathbf H(u,\alpha,\mathbf S),$$
  右端无定义（光不能按规定方向穿过）时记为 "no ray" [TK1999 p.4]。
- **等变性**：对任意正交矩阵 $w$ [TK1999 p.4, Eqs. (12)–(13)]
  $$\mathbf F(w\mathbf N,w\mathbf X,w\mathbf S)=w\mathbf F(\mathbf N,\mathbf X,\mathbf S),\qquad \mathbf H(wu,\alpha,w\mathbf S)=w\mathbf H(u,\alpha,\mathbf S).$$
  $\det w=-1$ 时定义 $w'(u)=wu\cdot\mathrm{yref}$（$\mathrm{yref}$ 为 $y=0$ 平面反射；$\det w=1$ 时 $w'(u)=wu$），则 $\mathbf H[w'(u),\alpha,w\mathbf S]=w\mathbf H(u,\alpha,\mathbf S)$ [TK1999 p.4, Eqs. (14)–(17)]。
- **「晕是什么」**：晕独立于任何一个太阳位置存在，由 $U$ 与 $\alpha$ 决定；正式定义是函数 $\mathbf S\mapsto\mathbf H(U,\alpha,\mathbf S)=\{\mathbf H(u,\alpha,\mathbf S):u\in U,\ \ne\text{"no ray"}\}$ [TK1999 p.5, Eqs. (18)–(19)]；$U=SO(3)$ 时是圆晕，$\alpha=60$ 给 22° 圆晕，$\alpha=90$ 给 46° [TK1999 p.5]。
- 楔坐标与空间坐标 [TK1999 p.5, Eqs. (20)–(24)]：$\mathbf V_u=(\mathbf V\cdot\mathbf A,\mathbf V\cdot\mathbf B,\mathbf V\cdot\mathbf C)$ 是 $\mathbf V$ 在楔坐标系里的样子，$\mathbf V=u\mathbf V_u$，即 $\mathbf V_u=u^{-1}\mathbf V$；space vectors（$\mathbf i,\mathbf j,\mathbf k,\mathbf S$）固定在空间，wedge vectors（$\mathbf A,\mathbf B,\mathbf C,\mathbf N,\mathbf X,\mathbf P$）固定在楔上；$\mathbf N_u=\mathbf N_0$ [TK1999 p.5–6]。
- 与 1980 Bravais 定律的关系：经典做法先证 $\mathbf H\cdot\mathbf B=\mathbf S\cdot\mathbf B$，故 $\mathbf S,\mathbf H$ 相差一个绕 $\mathbf B$ 的旋转 $\delta$（投影到 normal plane 的偏折）；Bravais 定律（投影后按 $n'=(n^2-\cos^2\theta)^{1/2}/\sin\theta$ 折射）可从 Fig. 9 看出，"But for us Bravais' law is of historical interest only" [TK1999 p.9]。真实偏折 $\cos\Delta=\mathbf S\cdot\mathbf H$ [Eq. (40)]；最小偏折 $\sin[(\alpha+\Delta_m)/2]=n\sin(\alpha/2)$ [TK1999 p.9, Eq. (41)]，此时 $\mathbf T=n\mathbf A$；最小偏折入/出光点 $\mathbf D_u=[\cos(-\Delta_m/2),0,\sin(-\Delta_m/2)]$、$\mathbf E_u=[\cos(\Delta_m/2),0,\sin(\Delta_m/2)]$ [TK1999 p.10, Eqs. (43)–(44)]。
- 入射区 / 出射区（entry / exit region）：能按规定方式穿楔的光线，入射前光点的集合 / 出射后光点的集合；$\mathbf S\mapsto\mathbf H$ 是二者间的 1–1 对应 [TK1999 p.9]。边界参数化 [TK1999 p.10–11, Eqs. (46)–(50)]：出射区上边界（掠出射）$\mathbf T_x(\theta)=u\mathbf B(\theta,\alpha/2-90)+(n^2-1)^{1/2}\mathbf X$，$\theta_0\le\theta\le180-\theta_0$，$\sin\theta_0=(n^2-1)^{1/2}\tan(\alpha/2)$；入射区上边界 $\mathbf S_x(\theta)=\mathrm{pr}(\mathbf T_x(\theta),\mathbf N,1)$；下边界（掠入射）$\mathbf S_n(\theta)=u\mathbf B(\theta,-\alpha/2+90)$。

**本系列对照**：$\mathrm{pr}$ 是折射算子 $\mathcal S_{\mathbf n}$ 的**光点版**（作用在 $-$光线方向上，且向量长度带折射率），$\mathbf F(\mathbf N,\mathbf X,\cdot)$ 就是 $W$；Eq. (12) 就是 ch8 §1 的旋转等变引理 $\mathcal S_{Q\mathbf n}(Q\mathbf r)=Q\mathcal S_{\mathbf n}(\mathbf r)$（TK1999 多说了一句：对 $\det w=-1$ 也成立，本系列引理写的是 $Q\in O(3)$，一致）；Eq. (13) 就是 $T=R\Phi R^{-1}$。Eq. (48) 的 $\theta_0$ 与 Tape 1980 Eq. (6) 的 $\theta_{\min}$ 是同一个量。TK1999 的 entry region ⊂ $S^2$ = 本系列 $\Phi$ 的定义域（`signature.phi` 的 `None` 之外），也就是定理 5′ 所说「定义域是 $\Phi$ 身份的一部分」的那个集合。

### 2.3 对取向的两级假设（§2.A, §1.B, §1.G）

- **弱假设（azimuth invariance）**：不预设 Spin Vector Assumption，只假设「楔的所有方位角等可能」：$u$ 在晕的取向集里则 $\mathrm{zrot}(\phi)\cdot u$ 也在，对所有 $\phi$；满足此条件的 $U$ 称 **halo-making set**（Eq. (29)）。作者承认这定义「显然不现实，因为它把太多取向集算作 halo-making set」，但真实晕的取向集都满足 [TK1999 p.7]。令 $Z$ 为绕 $z$ 轴旋转子群，条件即 $ZU\subseteq U$；陪集 $Zu=\{zu\}$；halo-making set 恰是陪集的并 [TK1999 p.7, Eqs. (30)–(31)]。
- **zenith locus**：$\mathbf k_u=u^{-1}\mathbf k$ 是天顶在楔坐标系里的样子；$U$ 的 zenith locus $K=\{\mathbf k_u:u\in U\}$，是楔上的骑手看到的天顶轨迹；同理 sun locus $\mathcal S=\{\mathbf S_u\}$ [TK1999 p.7]。
- 定理（halo-making set 的刻画）：对球面任意子集 $K$，$U(K)=\{u:\mathbf k_u\in K\}$ 是 halo-making set，其 zenith locus 是 $K$，$K\mapsto U(K)$ 是球面子集与 halo-making set 的 1–1 对应，保并、交、包含 [TK1999 p.8, Eqs. (32)–(38)]。证明用 $p:SO(3)\to S^2$，$p(u)=\mathbf k_u$ [TK1999 p.8]。note 3 的图像：$SO(3)$ 的一半 = 上半球每点竖一根头发（陪集），「brush haircut」，halo-making set 不劈开任何一根头发 [TK1999 p.73 note 3]。
- **Spin Vector Assumption（强假设）** [TK1999 p.2, Eq. (1)]：存在固定在楔上的单位向量 $\mathbf P$（spin vector），其天顶角 $\psi$ 恒定：$\mathbf P\cdot\mathbf k=\cos\psi$；楔可绕 $\mathbf P$ 自由转，$\mathbf P$ 可绕竖直自由转，其它不限。"may seem narrow and contrived, but it is satisfied approximately by all known halos arising in preferentially oriented crystals"；已知晕只需 $\psi=0$ 或 180（**point halo**）与 $\psi=90$（**great circle halo**），图示只画这两类 [TK1999 p.2]。
- **pole** $\mathbf P_u$：spin vector 在楔坐标系的表达；$u\in U\iff u\mathbf P_u\cdot\mathbf k=\cos\psi$，故 $U$ 由 $\psi$ 与 $\mathbf P_u$ 决定；晕由 $(\psi,\mathbf P_u,\alpha)$ 决定；固定 $\psi,\alpha$ 后所有晕由球面上一点表示 [TK1999 p.6, Eq. (25)]。$\mathbf P$ 平行棱时 $\mathbf P_u=(0,\pm1,0)$；垂直棱时在大圆 $y=0$ 上 [TK1999 p.6]。
- 定理（SVA 下的 halo-making set）：由 $\psi,\mathbf P_u$ 决定的取向集是 $U[K(\psi,\mathbf P_u)]$，$K(\psi,\mathbf P_u)$ 是以 $\mathbf P_u$ 为心、角半径 $\psi$ 的圆；point halo 的 zenith locus 是一点，great circle halo 的是一个大圆；「在所有球面子集中 SVA 只留下圆」[TK1999 p.8]。陪集是最小的非空 halo-making set，是 point halo 的取向集；每个晕都是 point halo 的并 [TK1999 p.9]。
- 两个定理都不涉及 $\alpha$，纯粹是关于取向的陈述 [TK1999 p.8]。
- 强度：全文不做强度计算，所有光线等权，忽略面间遮挡；不与 Monte Carlo（Pattloch & Tränkle）比真实性，而是补充概念洞见 [TK1999 p.1]。

**本系列对照**：弱假设 = 「$\rho$ 的支撑在 $Z$ 的左作用下不变」，只约束**支撑集**，不含权重；$p:SO(3)\to S^2$，$u\mapsto u^{-1}\mathbf k$ 是**另一个纤维化**——底是天顶方向在楔系里的位置、纤维是绕竖直的旋转 $Z$（陪集）——与定理 8 的纤维化（底 = 太阳方向在晶体系 $\mathbf u$、纤维 = 绕太阳的旋转）互为「姿态适配」与「径向适配」的两种切法。SVA 的 point / great circle halo = ch11 姿态族的片(Parry)/柱(Lowitz)：$\dim U=1$ / 2，对应 framework §5 的 $\dim(\text{晕})=\dim Q-\dim(\text{纤维})$。$\rho$：TK1999 **没有**（见 §4 逐条判断）。

### 2.4 atlas 的坐标与组织方式（§1.H–1.J, App. A, App. B）

- **Bravais 坐标**（pole 球面上）[TK1999 p.6, Eq. (26)]：
  $$\mathbf B(\theta,\delta)=(\sin\theta\cos\delta,\ \cos\theta,\ -\sin\theta\sin\delta),$$
  以 $(0,1,0)$（即楔向量 $\mathbf B$，折射棱方向）为极的球坐标，$\theta$ 是 Bravais 余纬、$\delta$ 是 Bravais 经度；$\theta=\theta_0$ 是 Bravais circle，$\delta=\delta_0$ 是 Bravais meridian（Fig. 7）。楔向量 $\mathbf V$ 的 Bravais 坐标指 $\mathbf V_u=\mathbf B(\theta,\delta)$，即 $\mathbf V=(\sin\theta\cos\delta)\mathbf A+(\cos\theta)\mathbf B-(\sin\theta\sin\delta)\mathbf C$，坐标随楔移动 [TK1999 p.6, Eqs. (27)–(28)]。**注意 Eq. (26) 第三分量带负号**。
- atlas 的画法：Appendix A 每张图是一个 Bravais 坐标网，每个晕的仿真图放在它的 pole $\mathbf P_u$ 处；pole 网用从 $(-1,0,0)$ 出发的立体投影画前半球 $x\ge0$（Fig. 7 右）[TK1999 p.6]。Fig. 33：point halos，$\alpha=60$，$\Sigma=0$，前半球 27 个代表 pole；$(0,1,0)$ 处的那个是右 22° 幻日 [TK1999 p.7]；Figs. 34–36 换 $\Sigma$（20, 50, 80），Figs. 38–41 换 $\alpha$（28, 52.4, 80.2, 90），Fig. 37 后半球 [TK1999 p.7; 图在 p.43–51]。Figs. 42–49 是 great circle halos，$(0,\pm1,0)$ 处是 22° 上下切弧；great circle halo 的 $\mathbf P_u$ 与 $-\mathbf P_u$ 给同一个晕，前半球足够 [TK1999 p.7; 图在 p.52–59]。Figs. 50–51 是按 mmm 对称拼合的 composite [TK1999 p.39, 图 p.60–61]。「完整 atlas 会含每个满足 SVA 的晕，每个 $(\psi,\mathbf P_u,\alpha)$ 一个，对每个 $\Sigma$ 画一张；本附录只画 $\psi=0,90$ 与选定的值」[TK1999 p.42]。
- 单张晕图的坐标：从天球内部正对太阳看（Fig. 16 右）；**S-centered 坐标** $(\Delta,\tau)$：$\Delta$ 是到太阳的角距，$\tau$ 是从太阳量起的 bearing，从天球内部看顺时针为正、12:00 为 0 [TK1999 p.16–17, Eq. (53)]；圆晕以内圆为准画在每张晕图里，幻日环作为太阳高度提示 [TK1999 p.43 Fig. 33 caption]。
- **D-centered 坐标** $(s,t)$（pole 球面上，以最小偏折入射向量 $\mathbf D_u$ 为心）：$s$ 是到 $\mathbf D_u$ 的角距，$t$ 是从 $\mathbf D_u$ 量起的 bearing，顺时针为正；$\mathbf D(s,t)=\mathrm{rot}(-t,\mathbf D_u)\cdot\mathbf D(s,0)$ [TK1999 p.17, Eq. (52)]。作者说 $\mathbf D,\mathbf B,\mathbf D\times\mathbf B$ 这个系比 $\mathbf A,\mathbf B,\mathbf C$ 更适合研究 contact point [TK1999 p.22]。
- **Appendix B pole diagrams**（Figs. 52–59，p.63–72）：对 Fig. 28 的锥晶，每个楔角一张图，给出 plate / Parry / AP 三类 spin vector 关于各楔的 pole，用 Bravais 坐标列表；同 pole 的楔分在一组（同一 point halo），对径 pole 的楔排同一行（互为 x-rotation，若是 great circle halo 则同一个晕）；表还给 $s_1,s_2$（Nonempty Halos Theorem 用）与 $(s,t)$（Contact Point Theorem 用）；图上的粗曲线是入射区边界，"×" 是 $\mathbf D_u$ [TK1999 p.62]。Fig. 55 是 22° 弧（$\alpha=60$）的 pole diagram [TK1999 p.66]，Fig. 59 是 46° 弧 [TK1999 p.71–72]。

**本系列对照**：atlas 的两层坐标要分开对：(a) **pole 球面**（Bravais / D-centered）是「空间方向在楔系里的样子」的球面——与本系列定理 8 的底 $S^2\ni\mathbf u=R^{-1}\mathbf s$ 是**同一个球面**（差一个楔系↔晶体系的固定旋转 $u_0$），sun locus $\mathbf S_u$ 就是 $\mathbf u$；(b) **单张晕图**的 $(\Delta,\tau)$ 才是天球坐标，$\Delta=D_P(\mathbf u)$、$\tau$ = 本系列图里沿幻日环量的方位（ch8 §6 的「方位 142°」是绕天顶的方位角，不是绕太阳的 bearing，换算时要注意——见 §5）。本系列没有 atlas 这个产品形态；最近的对应是 ch8 的 34 类 $\Phi$ 表（按 $(M,\text{楔角})$ 组织）与 ch11「行 = 光路类、列 = 姿态族」那张表：TK1999 的 atlas 是「行 = $\alpha$、列 = $\mathbf P_u\in S^2$（连续）、页 = $\psi\in\{0,90\}$ 与 $\Sigma$」，没有折叠 $M$ 这一维。

### 2.5 骑在楔子上：sun locus、halo point locus、contact（§2.B–2.G）

- 楔上视角 [TK1999 p.12, Eq. (51)]：$\mathbf H_u=\mathbf F(\mathbf N_u,\mathbf X_u,\mathbf S_u)$，楔系里 $\mathbf N_u,\mathbf X_u$ 固定、$\mathbf S_u$ 变；point halo 的 $\mathbf k_u$ 固定，$\sigma=90-\Sigma$ 为太阳天顶角，则 sun locus 是以 $\mathbf k_u$ 为心、半径 $\sigma$ 的圆（Fig. 11）；$\mathbf S_u$ 落在入射区外时无 $\mathbf H_u$，落在入射区内的那段扫出 halo point locus $\mathcal H$ [TK1999 p.12–13]。
- 三角形 $\mathbf k\mathbf S\mathbf H$ 与 $\mathbf k_u\mathbf S_u\mathbf H_u$ 全等（同三点，不同视角）：$\mathbf S_u,\mathbf H_u$ 的角距 $\Delta$ 就是真实偏折，$\mathbf k_u,\mathbf H_u$ 的角距 $h$ 是晕点天顶角，$\tau$ 是晕点从太阳量的 bearing [TK1999 p.13]。据此不用计算就能推断晕的形状（U 形、朝向、$\tau_{\mathrm{var}}$ 大小）[TK1999 p.13–14]。晕的构造逐点进行，「没有单个旋转把曲线 $\mathcal H$ 变成晕」[TK1999 p.13]。
- 空晕 / Nonempty Halos Theorem [TK1999 p.15–16]：$s_1,s_2$ 为 $\mathbf P_u$ 到入射区最近/最远点的角距；point halo 非空 ⇔ $s_1\le\sigma\le s_2$；great circle halo：$s_1\le90\le s_2$（$K$ 穿过入射区）时永不空，否则非空 ⇔ $-s_2\le\Sigma\le s_2$。
- contact circle 与 Criterion for Contact [TK1999 p.17–19]：最小偏折取向 $u(t)=\mathrm{rot}(t,\mathbf S)u_0$，$\mathbf k_{u(t)}=\mathbf D(\sigma,t)$ 扫出以 $\mathbf D_u$ 为心、半径 $\sigma$ 的 **contact circle** $\mathcal C(\alpha,\sigma)$（最小偏折取向集的 zenith locus，但它本身不是 halo-making set 除非 $\mathbf S=\pm\mathbf k$）[TK1999 p.18]；$\mathbf H[u(t)]=\mathbf S(\Delta_m,t)$ 扫出圆晕 [Eq. (59)]。Criterion：zenith locus 为 $K$ 的晕在 $\mathbf S(t)$ 处接触圆晕内边界 ⇔ $K$ 与 contact circle 交于 $\mathbf D(t)$，$t$ 在两个圆上是同一个角坐标 [TK1999 p.19]。SVA 下 contact 条件 $\cos s\cos\sigma+\sin s\sin\sigma\cos(t-\tau)=\cos\psi$，$\tau=t\pm\Delta t$，$\Delta t=\arccos[(\cos\psi-\cos s\cos\sigma)/(\sin s\sin\sigma)]$ [TK1999 p.19–20, Eqs. (64)–(66)]；Contact Point Theorem [TK1999 p.22]。
- Halo Transformation Rules [TK1999 p.22–26]：Rule 1（方位变化，Eq. (67)）$\mathbf H[U(K),\mathrm{zrot}(\phi)\mathbf S]=\mathrm{zrot}(\phi)\mathbf H[U(K),\mathbf S]$，逻辑上依赖 halo-making set 的方位不变性；Rule 2（x-rotation，$K\to-K$）；Rule 3（y-reflection，$K\to\mathrm{yref}K$）；Rule 4（z-reflection，$K\to\mathrm{yrot}K$）；定理：满足 $w\mathbf k=\pm\mathbf k$ 的正交 $w$ 恰给出这四条，别无其它（Table 1）[TK1999 p.25–26]；Face Interchange Rule：$K$ 绕 $z$ 转 180° ⇔ 交换入射面与出射面，但「我们不知道简单的办法用原晕的形状描述其 face interchange 的形状」[TK1999 p.26]。每个 pole 有 8 个相关的晕 (i)–(viii) [TK1999 p.26]。

**本系列对照**：sun locus = $\mathbf u$ 在 $S^2$ 上随 $R$ 的轨迹（片晶：绕 $\mathbf k_u$ 的圆）；$\Delta=D_P(\mathbf u)$。Rule 1 = 定理 3 里「与 $R_z$ 对易」那一族的等变性在天球上的表述（对纯折射晕 $W$ 的版本）。Face interchange 的「形状无简单关系」= 本系列 ch8 §3「正向 / 反向配对」（60° 的 12 类有 2 对和 8 个自对偶，90° 的 16 类有 8 对）：本系列在 $\Phi$ 类的层面也没有把一对合并，与 TK1999 一致。

### 2.6 从「所有可能的折射晕」回到真实冰晶（§3）

- 六方柱面编号：底面 1、2，侧面 3–8，看着面 1 时逆时针；面 $i$ 的外法向 $\mathbf N_i$，晶体系向量 $\mathbf N_3,\mathbf N_1\times\mathbf N_3,\mathbf N_1$；$\mathbf N_4=\cos60\,\mathbf N_3+\sin60\,\mathbf N_1\times\mathbf N_3$，… [TK1999 p.27, Eq. (78)]。**与本系列 `HexPrism` 的编号与方向完全一致**（本笔记开头核对过）。
- **wedge $ij$**：入射面 $i$、出射面 $j$，$\mathbf N=\mathbf N_i$，$\mathbf X=-\mathbf N_j$ [TK1999 p.27]。pole 的非正式求法：把晶体转到使楔 $ij$ 处于 standard orientation，spin vector 落在哪里就是 $\mathbf P_u$；正式求法用 (8) 与 (21) [TK1999 p.27–28]。
- 六个晶体取向类（Table 2）[TK1999 p.28]：Plate（$\mathbf N_1=\mathbf k$，$\mathbf P=\mathbf N_1,\psi=0$）、Par（$\mathbf N_3=\mathbf k$，$\mathbf P=\mathbf N_3,\psi=0$）、AP（alternate Parry，$\mathbf N_1\times\mathbf N_3=\mathbf k$，$\psi=0$）、Col（$\mathbf N_1$ 水平，$\mathbf P=\mathbf N_1,\psi=90$）、Low（$\mathbf N_1\times\mathbf N_3$ 水平，$\psi=90$）、AL（$\mathbf N_3$ 水平，$\psi=90$）。「只有 plate、Parry、column 的存在是确凿的」，Lowitz 有 1994 芬兰照片暗示，AP 证据稀少，AL 完全没有；仍纳入是为了平衡与完整 [TK1999 p.28]。旋转不必在每个晶体上实现，只需在总体上实现 [TK1999 p.28]。
- 六方柱只考虑 $\alpha=90$ 与 60 的楔（$>\alpha_{\max}=99.5$ 的不通光）；$\alpha=90$ 的晕称 46° arcs，$\alpha=60$ 的称 22° arcs；「arc」不暗示形状 [TK1999 p.28]。
- 「哪些楔做同一个晕」：$\alpha=90$ 共 24 个楔；两个晕相同 ⇔ 楔角相同且取向集相同 ⇔ zenith locus 相同 ⇔ $\psi$ 相同且 pole 相同，或 $\psi_1+\psi_2=180$ 且 pole 对径；Fig. 59 的表就是按 $(\alpha,\text{pole})$ 对楔做的计算机排序 [TK1999 p.29–30]。例：环天顶弧 Par 3 1 的 pole $=(1/\sqrt2,0,1/\sqrt2)=\mathbf B(90,-45)$；六个楔 1 3, …, 1 8 都做环天顶弧（Plate 1 3）[TK1999 p.29]。
- 22° arcs [TK1999 p.32]：**Plate 3 5 与 Plate 3 7 是熟悉的左、右 22° 幻日**，在幻日环上，互为 face interchange 与左右镜像；Col 3 5 是 22° 上下切弧（zenith locus 是 Bravais 赤道 $y=0$，所有太阳高度都在太阳竖直线上与 22° 晕接触）；Par 8 4 / 5 7 上下 sunvex Parry，Par 3 5 / 4 6 上下 suncave Parry；Low 4 6, 6 8, 5 7 三个 Lowitz 弧；「22° arcs 出奇地简单——pole 全在 Bravais 赤道 $y=0$ 或 Bravais 极 $(0,\pm1,0)$ 上」，经典晕理论家「抓了一手好牌」[TK1999 p.32–33]。
- 圆晕不满足 SVA、没有 pole；若按 zenith locus 表示则是「sphere halo」，zenith locus 为整个球面 [TK1999 p.31]。
- 命名缺陷：Col 3 5 低太阳时是上、下切弧两段，高太阳时是外接晕，本文观点下只是一个晕 [TK1999 p.33]。
- 锥晶 [TK1999 p.33]：锥面 13–18、23–28；假定 Miller 指数 $\{1,0,\bar1,1\}$、$c/a=1.63$，锥面与主轴倾角 28°；$\mathbf N_{13}=\cos28\,\mathbf N_3+\sin28\,\mathbf N_1$ 等 [Eq. (79)]；Table 3 给 8 个楔角与圆晕半径：28.0→9.0，52.4→18.3，56.0→19.9，60.0→21.8，62.0→22.9，63.8→23.8，80.2→34.9，90.0→45.7 [TK1999 p.33]。
- Wedge Change Rule [TK1999 p.36, Eqs. (80)–(81)]：同一晶体上两个全等楔，$w$ 是把第一个楔带到第二个楔的正交变换之一，$v$ 是第一个楔的 frame，则 $\mathbf P_{w'(v)}=w_v^{-1}\mathbf P_v$（$\det w=1$）或 $\mathrm{yref}\,w_v^{-1}\mathbf P_v$（$\det w=-1$），$w_v=v^{-1}wv$。推论：$w\mathbf P=\pm\mathbf P$ 的晶体对称诱导 pole 对称 $e,-e,\mathrm{yref},-\mathrm{yref}$，进而给出晕的 x-rotation / y-reflection / z-reflection 对称 [TK1999 p.36–37]；pole diagram 的 mmm 对称 [TK1999 p.37–38]。
- §3 的自评：「Section 3 几乎不是关于晕的；它是关于晶体的几何……给定固定在晶体上的向量 $\mathbf P$ 和晶体上的一个楔，$\mathbf P$ 从楔上看是什么样子？就这些」[TK1999 p.41]。
- Können 的总结：pole 球面（"halo sphere"）与 halo poles；已知晶体形状 + 已知取向类 ⇒ 离散的 pole 集；真实显示是 atlas 里若干晕的 composite；三条延伸：理论能组织含反射的光路、可作系统命名的基础、为反演问题提供工具 [TK1999 p.42]。

**本系列对照**：TK1999 的「按 $(\alpha,\text{pole})$ 排序楔」= 本系列 signature 商掉对称的**局部版本**——他们在**给定取向类**下判「哪些楔做同一个晕」，本系列是在**不看取向**、商掉 $D_{6h}$ 下判「哪些 $(M,\mathbf n_a,\tilde{\mathbf n}_b)$ 给同一个 $\Phi$」。Wedge Change Rule 的 $w_v=v^{-1}wv$ 是本系列 `canonical_signature` 里 $(gMg^{\mathsf T},g\mathbf n_a,g\mathbf n_b)$ 那一步的楔系写法。TK1999 Table 3 的 8 个楔角 + 0° = framework 定理 7 的 9 个（数值逐一相同）。

### 2.7 与 Tape 1980 halo function 的关系

- **TK1999 的参考文献里没有 Tape 1980**（refs 1–20：Pattloch & Tränkle、Tricker 1979、Visser、Tape 1994、Greenler、Können、Kobayashi 等）[TK1999 p.73–74]。两文之间的关系是对象层面的：
  - 1980 的 $F(\theta,\mu,\beta)$ 与 1999 的 $\mathbf H(u,\alpha,\mathbf S)$ 是**同一个映射**（单楔纯折射，取向 → 光点），前者用 Bravais 定律 + 太阳系球坐标显式写出，后者用两次平行投影 + 取向矩阵写出；1999 明确把 Bravais 定律降为「历史兴趣」[TK1999 p.9]。
  - 1980 的 generating set $\mathcal N$ ↔ 1999 的 $U$；1980 只在**竖直系**里用 (25)–(30) 写约束方程，1999 引入 $Z$-不变性 + zenith locus 把「约束」结构化为球面子集 $K$。
  - 1980 的核心是 caustic（Jacobian 的核）；**1999 完全没有 Jacobian / 奇点 / caustic**（全文只用 contact point、entry region 边界、level curves of $\Delta$ 定性推断形状 [TK1999 p.13–14]）。两文互补：1980 = 微分（局部、强度骨架），1999 = 组合/群（全局、分类）。
  - 1999 的 "halo" 定义（$U,\alpha$ 决定、独立于太阳位置 [TK1999 p.5]）在 1980 里没有对应——1980 的 $F$ 把太阳固定在 $u$ 轴上，$\Sigma$ 只进入约束方程。

### 2.8 TK1999 明确排除或搁置的东西

- 内反射光路：「本文考虑的光路从入射面进、直接从出射面出，无中间内反射。但方法可以扩展到某些含内反射的光路」，例：subparhelia、Wegener 弧、Hastings 弧有一次在垂直于入、出射面的平面上的反射；这会把楔系里的 $\mathbf H_u$ 与 $\mathcal H$ **关于 Bravais 赤道 $y=0$ 反射**，空间里的晕则「以不那么透明的方式」改变；「现有 atlas 的每个晕都会有一个新晕……会得到一整本新 atlas；任何其它新光路同样如此」[TK1999 p.15 §2.E]。**这就是本系列的折叠 $M$**，他们只给了一个 $M$（在 normal plane 内的一次反射）的定性说明，没有分类。
- 强度、遮挡 [TK1999 p.1]；晶体倾角扩散 [TK1999 p.39 说 Fig. 31 的 MC 假定取向完美]。

## 3. Tape & Moilanen 2006 *Atmospheric Halos and the Search for Angle x*（只读目标章节）

### 3.1 光点与光点图（ch4, ch8）——「光点法」这个词的出处

- 「光点」定义：「The light point of the ray is the point on the celestial sphere in the direction opposite to the ray. It is the point that appears to be lit, should the ray reach the eye of an observer」[TM2006 p.43]。出射光的光点即 halo point [TM2006 p.44]。
- 「只需考虑单个晶体」：天空充满平行阳光与同形同向晶体时，总有一个晶体的出射光到达观察者，且光路逐段平行于原光路 [TM2006 p.44]。
- 晕的定义（普通话版）："a halo is the locus of the halo point of a specified ray path as a crystal takes on orientations in the given orientation class. Change the ray path and you (usually) get a new halo" [TM2006 p.47]。光路记为面编号序列，面编号：底面 1、2，侧面 3–8 看着面 1 逆时针 [TM2006 p.47; Fig. 6.1 p.62]。例外：光路 1 与 326 都给 subsun；35 与 46 都给左幻日，「区别是表面的，本质上是面编号的偶然」[TM2006 p.48]。
- **反射与折射定律的几何形式**：把天球半径取为所在介质的折射率（每个折射率一个天球，诸球同心；二维截面就是通常所说的「同心圆作图」）；入射、反射、折射光线的光点 $\mathbf S,\mathbf S',\mathbf R$ 在一条**垂直于界面的直线上**（Fig. 4.5）[TM2006 p.48]。Fig. 4.8 又从 $n_1\sin\theta_1=n_2\sin\theta_2$ 推出这条几何折射定律 [TM2006 p.51]。因此同心圆 / 同心球作图本身已有可直接引用的一手说明，并不是必须等 Tricker 1970 才能确认的专属方法。subsun 的例子：$\mathbf H$ 在 $\mathbf S$ 正下方 [TM2006 p.48]；环天顶弧的例子：先沿入射面法向把 $\mathbf S$ 投到外球得 $\mathbf R$，再沿出射面法向投回内球得 $\mathbf H$，CZA 是水平面与天球的交 [TM2006 p.50]。
- **"light point diagrams"**：Figs. 4.6、4.7 这类图的名字；「对很多其它晕我们只能依赖仿真或 'pole theory'……不是光点图不对，而是它们太复杂、不够启发……第 8 章之后不再出现光点图」[TM2006 p.50–51]。几何形式的折射定律「至少可追溯到 Hamilton [23] 与 MacCullagh [44]，19 世纪」[TM2006 p.51；文献 p.238–239]。
- 圆晕的光点图（ch8）：normal vee（$\mathbf R\mathbf S$、$\mathbf R\mathbf H$ 两段，顶角 $=\alpha$）；最小偏折 ⇔ vee 等腰且 central（vee 平面过球心）⇔ 光路在 normal plane 内且对称；正弦定理给 Eq. (8.1) [TM2006 p.88–89]。「一般问题（非平面光路）Uhler [81] 与 Tape [75] 用解析法处理过，本书用几何法；看一眼解析处理就明白几何法的吸引力」[TM2006 p.88]。
- 强度：光点图不含强度；ch14 末尾说本章结论依赖晶体倾角很小，「实践中小倾角是例外而非常规」，倾角中等以上时非接触弧在很宽的太阳高度范围内都接触圆晕、弧趋于圆形 [TM2006 p.153]。

**结论（对方法与称呼分开处理）**：同心圆作图所表达的几何折射法可直接据 TM2006 Figs. 4.5、4.8 介绍和改绘；「光点」（light point）与「光点图」（light point diagram）则是 Tape 文献中可核实的术语，TK1999 p.3 已用 "light point"，TM2006 p.43/p.50 给出定义与命名，番外可放心把 Tape 这一路叫「光点法」。尚无法由本机材料确认的，只是 Tricker 1970 是否采用完全相同的图式、又怎样称呼它（→ §7）。作者判断两者大概率是同一种标准折射作图；在取得原书前，这应标为几何上的推断，而不是 Tricker 原文事实。

### 3.2 楔角、圆晕半径、锥晶楔角表（ch8, ch9）

- $\sin\dfrac{\alpha+\Delta_{\min}}{2}=n\sin\dfrac\alpha2$（$n=1.31$）[TM2006 p.86, Eq. (8.1)]；$\alpha=60\Rightarrow\Delta_{\min}=21.8$，$\alpha=90\Rightarrow45.7$；$n\sin(\alpha_{\max}/2)=1$ [Eq. (8.2)]，$\alpha_{\max}=99.5$，最大可能半径 80.5°；六方柱三个楔角 60、90、120，120 超过 $\alpha_{\max}$，故六方柱只有 22° 与 46° 圆晕 [TM2006 p.86–87]。
- 楔角公式 [TM2006 p.102, Eq. (9.1)]：
  $$\cos\alpha=-\frac{\mathbf N_i\cdot\mathbf N_j}{|\mathbf N_i||\mathbf N_j|},$$
  $\mathbf N_i,\mathbf N_j$ 是两面的**外**法向；楔角是外法向夹角的补角，等于 $-\mathbf N_3$ 与 $\mathbf N_5$ 的夹角 [TM2006 p.101–102, Fig. 9.1]。**逐字就是本系列 $\cos A=-\langle\mathbf n_a,\tilde{\mathbf n}_b\rangle$（$M=I$ 情形）**。
- 锥面法向 $\mathbf N_{13}=(\cos t\cos x,\sin t\cos x,\sin x)$，$\mathbf N_{14}$ 方位加 60°，楔 13 14 的 $\cos\alpha=-\frac12(\cos^2x+2\sin^2x)=\frac14(-3+\cos2x)$ [TM2006 p.102–103, Eqs. (9.2)–(9.4)]；其余楔角类推，列于 Table 9.1 [TM2006 p.102]。
- Angle x 由 Miller 指数与 $c/a$ 决定 [TM2006 p.108, Eqs. (9.6)–(9.7)]：
  $$\tan x=\frac{\sqrt3}{2}\,\frac ac\,\Big|\frac lh\Big|\ (k=0,\ \text{一阶面}),\qquad \tan x=\frac12\,\frac ac\,\Big|\frac lh\Big|\ (h=k,\ \text{二阶面}).$$
  Steinmetz & Weickmann：$c/a=1.63$、$h=l=1$ ⇒ $x=28°$，配合 Table 9.1 给 Table 8.1 的楔角；「简言之，Table 8.1 的楔角是由冰的 $c/a$ 比、假设锥面为 $\{1,0,\bar1,1\}$ 面算出来的」[TM2006 p.108]。

### 3.3 spin vector 与 halo pole 的成熟表述（ch12–14, App. F）：与 1980 / 1999 的异同

- 术语：**refraction halos** = 光路只含折射的晕（22° 晕、幻日、切弧是；幻日环、120° 幻日、subparhelia 不是）[TM2006 p.139]；随机取向 → 圆晕，优先取向 → 每个圆晕对应一族弧；片晶下楔 35 给左幻日、楔 37 给右幻日——「随机取向时做同一个晕的两个楔，现在做不同的晕」[TM2006 p.140]；分类矩阵 Fig. 12.1：列 = 楔角、行 = 取向类（plate / Parry / column / Lowitz / random）[TM2006 p.141]。楔角给「离太阳多远」，spin vector 给形状与方向 [TM2006 p.142]。
- spin vector（Table 13.1）：plate $\mathbf N_1$ 竖直、Parry $\mathbf N_3$ 竖直、column $\mathbf N_1$ 水平、Lowitz $\mathbf N_1\times\mathbf N_3$ 水平 [TM2006 p.143–145]。**contact arcs / non-contact arcs**：$\mathbf P$ 水平 / 竖直（列弧、Lowitz 弧 / 片弧、Parry 弧），「所有 contact arcs 行为相似，所有 non-contact arcs 行为相似」[TM2006 p.145]。
- halo pole：「pole 就是从做晕的楔上看到的 spin vector」[TM2006 p.147]；「Können 在 1990 年代提出了这个概念」，逻辑细节见 Tape & Können [77] [TM2006 p.147]。standard orientation：入、出射面关于 $x=0$ 平面对称，入射面朝前、出射面朝后、楔开口朝下 [TM2006 p.148]（与 TK1999 Fig. 5 一致）。例：Parry 环天顶弧（楔 31）pole 在子午线 $y=0$ 上、赤道上方 45°（因楔角 90°）[TM2006 p.148]；**右幻日的 pole 是 $(0,1,0)$**（把钉子挪到面 1）[TM2006 p.150]。
- 非接触弧的定性规则 [TM2006 p.150–152]：$\mathbf D_u$ 在子午线上、赤道下 $\Delta_{\min}/2$；弧相对太阳的方向 ≈ pole 相对 $\mathbf D_u$ 的方向；pole 在左/右半球 → 左/右弧，在 $y=0$ 上 → 左右对称；上/下弧的分界是过 $\mathbf D_u$ 与 $(0,\pm1,0)$ 的大圆（不是赤道）；pole 远离 $\pm\mathbf D_u$ → sunvex（U 形、凸向太阳），靠近 → suncave；只在 $\sigma=s$（$s$ = $\mathbf D_u$ 到 $\mathbf P_u$ 的角距）这一个太阳天顶角接触圆晕，接触点方向 = $\mathbf P_u$ 相对 $\mathbf D_u$ 的方向 [TM2006 p.152]。
- Appendix F 是 TK1999 §2 的白话版：$\mathbf k,\mathbf S,\mathbf H,\mathbf D,\mathbf E,\mathbf P$；$\mathbf V_u$ = 把向量与楔刚性连起来一起转到 standard orientation 后 $\mathbf V$ 落到的位置 [TM2006 p.229–230]；非接触弧 zenith locus $=\{\mathbf P_u\}$，接触弧 zenith locus = 以 $\mathbf P_u$ 为心的大圆 [TM2006 p.230–231]；contact circle 以 $\mathbf D_u$ 为心、半径 $\sigma$；Criterion for contact [TM2006 p.231]；证明用三角形 $\mathbf k\mathbf S\mathbf H\cong\mathbf k_u\mathbf S_u\mathbf H_u$ [TM2006 p.233–235]；脚注 1：「若某楔取向可取，则它绕竖直轴转过的取向也可取——这个很弱的假设被所有常见取向类满足，更一般地被任何由 spin vector 刻画的取向类满足」[TM2006 p.235]（= TK1999 Eq. (29)）。
- **与 1980 / 1999 的异同小结**：
  - 术语变化：1980「point of light」「halo function」「generating set」「caustic」→ 1999「light point」「halo point $\mathbf H(u,\alpha,\mathbf S)$」「halo-making set」「zenith locus」「pole」→ 2006「light point」「light point diagram」「spin vector」「halo pole」「contact / non-contact arcs」「refraction halos」。1980 的 caustic / 奇点语言在 1999、2006 里**消失**（2006 只在 p.88 引 [75] 说它是解析处理）。 [Tape1980 p.1, p.13; TK1999 p.3–4, p.6–7; TM2006 p.43, p.50, p.139, p.143, p.145, p.147]
  - 图集组织：1999 按 $(\alpha,\mathbf P_u,\psi,\Sigma)$ 的 atlas + 按楔角的 pole diagrams；2006 改为按圆晕半径分章（9°、18°、20°、22°、23°、24°、35° 各一族，ch15–17 按 plate / column / Parry 组织），pole 只作定性工具（ch14「用户指南」），不再印完整 atlas [TM2006 p.5 目录; TK1999 p.42]。
  - 2006 ch14 的「上/下弧分界是过 $\mathbf D_u$ 的大圆」「sunvex / suncave 由 pole 到 $\mathbf D_u$ 的距离决定」是 1999 §2.D 定性推断的提炼；1999 的 D-centered 坐标 $(s,t)$ 在 2006 里只保留 $s$ [TM2006 p.152]。

### 3.4 「Angle x」的原始提法，与 roadmap ch9 那句话的对照

- 定义："The shape of these crystals is determined by the so-called angle x. The search for angle x is the effort to discover what the crystals look like" [TM2006 p.7 Preface]；「angle x——锥面对 c 轴的倾角——不能由对称性推出，而它对晕理论至关重要，因为它决定晶体上的楔角、从而决定圆晕半径。所以理解 odd radius 晕的努力大部分花在找 x 最合理的值上」[TM2006 p.123]。ch9 开头："First, on a pyramidal crystal the angle of inclination x of the pyramid faces to the crystal axis determines all of the wedge angles on the crystal. Second, the most likely value of x is 28°" [TM2006 p.101]。
- 历史脉络（ch11）：Mariotte $x=30°$、Venturi 60°、Galle 60.32°（楔 13 23 的 $\alpha=180-2x=59.35°$）[TM2006 p.124]；Bravais 1847 由 Clarke 测得的菱面体面间角 120° 算出 $x=\tan^{-1}\sqrt2=54.7°$，此值统治 odd radius 理论一个多世纪 [TM2006 p.126–127]；「Rational Tangents Principle」（$\tan x/\tan x_0=v/u$）是「党的路线」（party line），可以不知道 $c/a$、不知道 Miller 指数就生成候选 $x$ [TM2006 p.128–129]；Besson 用测得的晕半径反推 $x\approx25°$ 或 $28°$，选了 25° [TM2006 p.129–131]；Humphreys 用 Dennison 的 X 射线 $c/a=1.62$ 乘 4/3 得 24.8°——「我们认为 Humphreys 犯了错」[TM2006 p.132]；**Steinmetz & Weickmann 1947 取 Barnes 的 $c/a=1.63$、假定 $\{1,0,\bar1,1\}$ 面，算出 $x=28°$，「我们认为他们做对了」** [TM2006 p.133]；Tricker 1979 重新发现此法 [TM2006 p.134]。
- ch18「其它楔角？」：新楔角要么来自新的晶面（作者「在无数大气晶体里没见过证据」），要么来自多晶（polycrystal）[TM2006 p.193–194]；M-arc 是仍未解释的新晕 [TM2006 p.194]；Hevel 90° 晕超过单楔上限 80.5°，需要新机制 [TM2006 p.202–203]；44° 幻日是幻日的幻日（二次晕），「odd radius 不自动意味着 odd wedge angle」[TM2006 p.203]。

**对 roadmap ch9「Tape 的 Angle x 在本系列里只是参数 $c/a$」的判断**：**成立，但要加一句限定。** 依据：
1. Tape 自己就把 $x$ 化归为 $c/a$ + Miller 指数：Eq. (9.6) $\tan x=\frac{\sqrt3}{2}\frac ac|\frac lh|$ [TM2006 p.108]，取 $\{1,0,\bar1,1\}$ 后 $x$ 是 $c/a$ 的单参数函数；Table 8.1 / TK1999 Table 3 的 8 个楔角全部由此算出 [TM2006 p.108; TK1999 p.33]。这与 framework §3 定理 7「整个 odd-radius 晕家族由单参数 $c/a$ 决定」一致（本系列取 $c/a=1.6288$，锥面法向与 c 轴夹 $62.0°=90°-28°$）。
2. 限定：「Search for Angle x」在 Tape 那里首先是**历史与观测问题**——哪一个 $x$ 是真的（Bravais 54.7 / Besson 25 / Humphreys 24.8 / Steinmetz–Weickmann 28）、锥面到底是不是 $\{1,0,\bar1,1\}$ 面、$c/a$ 是多少 [TM2006 p.123–134]，以及 ch18 的「还有没有别的楔角」[TM2006 p.193]。本系列说「只是参数」指的是**框架层面**（$\Phi=M\circ W$ 与楔角公式不依赖 $x$ 的具体值），不是说 $x$ 的值不重要——ch9 提纲引这句话时应写成「在本系列的框架里 Angle x 只是一个参数：换一个 $c/a$，定理 6、7 的算法一字不改」，并把「哪个值是真的」明确交还给 Tape [TM2006 p.101, p.133]。
3. 附带：TM2006 Eq. (9.1) 的楔角公式与本系列楔角公式逐字相同 [TM2006 p.102]，所以 ch9「同一公式 $\cos A=-\langle\mathbf n_a,\mathbf n_b\rangle$ 扫 20 个面得 9 个可透射楔角」在 Tape 那里有直接对应（Table 9.1 + Table 8.1），本系列多出的是「以 $M$ 展开后仍成立」（$\tilde{\mathbf n}_b=M^{-1}\mathbf n_b$）这一步。

## 4. 对应表（笔记核心）

判定列的含义：**同物异名** = 同一个数学对象换了名字；**本系列多出** = Tape 三篇里没有这个对象；**Tape 有而本系列没有** = 本系列文档（`docs/framework.md`、ch7–ch8 正文）里没有对应对象；**部分** = 有对应但粒度或范围不同。「Tape 没有」的判断依据一律给页码（否定性结论的依据是「在该文该节的定义/范围声明里被排除」，不是「没搜到」）。

| # | Tape 对象（出处） | 本系列对象 | 判定 | 说明 |
|---|---|---|---|---|
| 1 | halo function $F(\theta,\mu,\beta)$ [Tape1980 p.4 Eq. (20)]；halo point $\mathbf H(u,\alpha,\mathbf S)=\mathbf F(u\mathbf N_0,u\mathbf X_0,\mathbf S)$ [TK1999 p.4 Eq. (11)] | halo map $F_P:Q\to S^2$，$F_P(R)=$ 光点$\big(R\,\Phi_P(R^{-1}\cdot)\big)$（framework §0 对象链），限 $M=I$、$\Phi_P=W$ | 同物异名（限纯折射） | 三者都是「取向 → 天球光点」；Tape 的 $\Phi$ 只有 $W$。1980 把太阳钉在 $u$ 轴、用 Bravais 定律显式写；1999 用两次平行投影 + 取向矩阵写；本系列写成 $R\Phi R^{-1}$ 的共轭（ch8 §1）。 |
| 2 | 真实偏折 $\Delta(\theta,\mu)$，$\sin(\Delta/2)=-\sin\theta\sin(D/2)$ [Tape1980 p.3 Eq. (15)]；$\cos\Delta=\mathbf S\cdot\mathbf H$ [TK1999 p.9 Eq. (40)] | $D_P(\mathbf u)=\angle(\Phi_P(\mathbf u),\mathbf u)$（定理 8） | 同物异名 | 1980 的 normal-plane 偏折 $D(\theta,\mu)$ 是 Bravais 定律的中间量，本系列无对应。 |
| 3 | 取向坐标 $(\theta,\mu)$ = 太阳在楔系的球坐标 [Tape1980 p.4, p.12]；sun locus $\mathbf S_u=u^{-1}\mathbf S$ [TK1999 p.7, p.12] | $\mathbf u=R^{-1}\mathbf s$，定理 8 纤维化的**底** $S^2$ | 同物异名 | 差一个楔系↔晶体系的固定旋转。 |
| 4 | $\beta$ = 绕太阳方向（$u$ 轴）的旋转 [Tape1980 p.4]；「$\ker JF$ 与 $\beta$ 无关」[Tape1980 p.5 Fig. 8] | $\mathrm{Rot}_{\mathbf s}(\theta)$，定理 8 纤维化的**纤维** | 同物异名 | **定理 8 的纤维化在 Tape 1980 §IV 已以坐标形式存在**：$F=R_\beta\circ(\text{只依赖 }\mathbf u)$，$\Delta$ 不含 $\beta$。TK1999 没有这个纤维化（它用的是 #10 的另一个）。 |
| 5 | 纤维曲线 $F^{-1}(Y)\subset\mathcal F-\mathcal S$，「无穷多取向点亮同一点」[Tape1980 p.5, p.12] | 定理 8 内层积分里 $\delta(\mathbf x-\cdots)$ 的支撑，即 $F_P^{-1}(\mathbf x)$ | 同物异名 | Tape 只有几何（曲线），没有在纤维上积分的测度（见 #17）。 |
| 6 | wedge：$(\hat{\mathbf N}_1,\hat{\mathbf N}_2,\hat{\mathbf P})$ [Tape1980 p.1]；$(\mathbf N,\mathbf X)$ 与 wedge frame $\mathbf A,\mathbf B,\mathbf C$ [TK1999 p.3 Eq. (8)] | 展开空间里的面对 $(\mathbf n_a,\tilde{\mathbf n}_b)$ 与 $W=\mathcal S_{\tilde{\mathbf n}_b}\circ\mathcal S_{\mathbf n_a}$（定理 4） | 同物异名 | $\hat{\mathbf N}_1=-\mathbf n_a$、$\hat{\mathbf N}_2=\tilde{\mathbf n}_b$；$\mathbf N=\mathbf n_a$、$\mathbf X=-\tilde{\mathbf n}_b$；$\hat{\mathbf P}=\mathbf B\parallel-\mathbf n_a\times\tilde{\mathbf n}_b$。Tape 的 wedge 永远是**物理**面对（wedge $ij$ 由入射面 $i$、出射面 $j$ 定义 [TK1999 p.27]）；本系列的 $\tilde{\mathbf n}_b$ 是展开后的**虚**面。 |
| 7 | refracting angle / wedge angle $\alpha$ [Tape1980 p.1; TK1999 p.4; TM2006 p.102 Eq. (9.1)] | 楔角 $A$，$\cos A=-\langle\mathbf n_a,M^{-1}\mathbf n_b\rangle$（ch8 §2） | 同物异名 | 三篇数值都等于 $A$（内/外法向约定不同，见 §5）。TM2006 Eq. (9.1) 与本系列公式逐字相同（$M=I$）。 |
| 8 | $\mathrm{pr}(\mathbf S,\mathbf N,n_2)=\mathbf S+\lambda\mathbf N$ [TK1999 p.2 Eqs. (2)–(3)]；以折射率为半径的同心天球及其法线投影作图 [TM2006 p.48 Fig. 4.5]，并由 Snell 定律推出 [TM2006 p.51 Fig. 4.8] | 折射算子 $\mathcal S_{\mathbf n}$，$\mathbf p'=\mathbf p_\parallel+\sigma\sqrt{n_2^2-\|\mathbf p_\parallel\|^2}\mathbf n$（ch8 §1） | 同物异名 | 同一个 Snell；Tape 作用在光点（$-$光线，长度 $=n$），本系列作用在光线方向。ch8 §1 所说「内外两个同心圆」就是这些同心天球的二维截面，是通行的几何折射作图，不应归为 Tricker 独有。 |
| 9 | $\mathbf F(w\mathbf N,w\mathbf X,w\mathbf S)=w\mathbf F(\mathbf N,\mathbf X,\mathbf S)$，$\mathbf H(wu,\alpha,w\mathbf S)=w\mathbf H(u,\alpha,\mathbf S)$ [TK1999 p.4 Eqs. (12)–(13)] | 旋转等变引理 $\mathcal S_{Q\mathbf n}(Q\mathbf r)=Q\mathcal S_{\mathbf n}(\mathbf r)$；$T=R\Phi R^{-1}$（ch8 §1） | 同物异名 | TK1999 只用它做变换规则与 pole；本系列用它把 $M$ 从两次折射中间提出来（定理 4）——**同一个引理，用途不同**。 |
| 10 | halo-making set（$ZU\subseteq U$）、zenith locus $K=\{u^{-1}\mathbf k\}$、$p:SO(3)\to S^2$ [TK1999 p.7–8 Eqs. (29)–(38)] | 姿态族 $Q=\mathrm{supp}\,\rho$ 的方位不变性；**另一个纤维化**：底 = 天顶在晶体系的方向、纤维 = $Z$ | 部分（本系列未显式写） | 与定理 8 互为「姿态适配」（底 = $\mathbf k$ 在晶体系）与「径向适配」（底 = $\mathbf s$ 在晶体系）的两种切法。TM2006 p.235 脚注 1 同一假设。 |
| 11 | Spin Vector Assumption $(\psi,\mathbf P_u)$、point / great circle halo [TK1999 p.2, p.6, p.8]；spin vector Table 13.1、contact / non-contact arcs [TM2006 p.145] | ch11 姿态族：片（$\mathbf c=\mathbf N_1$ 竖直）/ 柱 / Parry / Lowitz，各带扩散 $\sigma$；$\dim Q=1/2$ | 部分 | TK1999 多两族（AP、AL）[TK1999 p.28]；本系列多「随机 + 扩散 $\sigma$」与权重（#17）。pole $\mathbf P_u$ = spin vector 在楔系的坐标 = 本系列「晶体系向量经 $u_0^{-1}$ 换到展开楔系」，本系列没有为它起名。 |
| 12 | 三维/二维/一维晕（generating set 是开集/曲面/曲线）[Tape1980 p.13]；point halo 取向集一维、great circle halo 二维 [TK1999 p.7] | $\dim(\text{晕})=\dim Q-\dim\mathrm{Stab}$（定理 3）/ $\dim Q-\dim(\text{纤维})$（framework §5） | 部分 | Tape 按 $\dim Q$ 分；本系列按 $\dim Q-\dim(\text{纤维})$ 分（多了「纤维」项——平行光路的 dimension collapse），对纯折射楔两者一致（纤维零维）。 |
| 13 | 奇点、$\ker JF$（Prop. 2 Eq. (21)–(22)）、caustic = 奇点集的像 [Tape1980 p.1, p.5, p.14] | $DF$ 降秩、Jacobian focusing（framework §4） | 同物异名 | Tape 给了显式核公式与「核 ⟂ $\mathcal N$ 法向」判据 [Tape1980 p.14–15]，本系列只有定义；**ch10 应直接引用 Prop. 2 与 Eq. (34)**。 |
| 14 | 二维晕 case (i)/(ii)：$X\in\mathcal S$（与圆晕 caustic 重合的点）vs $X\notin\mathcal S$ [Tape1980 p.14] | framework §4 表的「Jacobian focusing」一列 | 同物异名 | Tape 的 $\mathcal S$（$\theta=90,\mu=\mu_M(90)$）= 本系列 22° 晕的 fold 奇点线 $D(i)\simeq D_{\min}+\frac12D''(i-i_0)^2$。 |
| 15 | Whitney fold / pleat [Tape1980 p.14]；「pleat 真实吗」[Tape1980 p.15]；Tape 1982 *Folds, pleats, and halos*；Tape 1983 *Halos and Singularities*（1982 文的技术扩展，DOI `10.1364/MO.1983.FA4`） | fold 局部律 $I\sim1/\sqrt{D-D_{\min}}$（framework §4）；pleat / cusp 数值确认列为未决（framework §7） | 部分 | fold / pleat 并非 1983 才出现：1980 原文已有判据和位置，1982 作科普展开，1983 再作技术扩展。Tape 有 pleat 的位置（Figs. 15–16）没有强度；本系列有 fold 强度律没有 pleat。 |
| 16 | 最小偏折轨迹 ≠ caustic（除切弧与幻日）[Tape1980 p.15] | 无独立对象 | Tape 有而本系列没有 | ch10 写「最小偏折 = fold caustic」时必须加 Tape 的限定：只对切弧 / 幻日 / 圆晕成立；side arc 上最小偏折轨迹一般不是 caustic。 |
| 17 | 姿态分布 $\rho$ | $\rho$、$\mu_{\rm sky}=(F_P)_*[\rho\,w_P\,dq]$、$SO(3)$ 上的群卷积 $\rho_0*k_\sigma$（framework §0, §4, §5） | **本系列多出（Tape 没有）** | 依据：Tape 1980「若参数取随机或加权值就得到 Greenler 式仿真」[Tape1980 p.1]，note 22 承认 $(\theta,\mu)$ 等距不等于取向均匀 [Tape1980 p.18]，理想化「不偏离优先取向」[Tape1980 p.13]；TK1999「不做强度计算，所有光线等权，忽略遮挡」[TK1999 p.1]，Fig. 31 MC「取向假定完美」[TK1999 p.39]；TM2006 只定性说倾角使弧变圆 [TM2006 p.153]。**弱假设 (29) 与 SVA 只约束 $\mathrm{supp}\,\rho$，不等价于某个 $\rho$ 族**——它们等价于「$\rho$ 是 $Z$-不变集合上的均匀测度」这一个特例（SVA 下 $\rho\propto\mathbf 1_{U(K(\psi,\mathbf P_u))}$）。 |
| 18 | $D_P(\mathbf u)$ 与纤维化积分（定理 8 的二重积分） | — | **本系列多出（Tape 没有积分，有坐标）** | Tape 1980 有纤维化的**坐标**（#4）与纤维**曲线**（#5），TK1999 有另一纤维化的**定理**（#10），但三篇都没有把 $\mu_{\rm sky}$ 写成对底与纤维的积分——因为没有 $\rho$（#17）与 $w_P$。 |
| 19 | 折叠 $M$、12 种折叠、$\Phi=M\circ W$ 分解 | 定理 4、定理 1–2 | **本系列多出（Tape 没有）** | 依据：Tape 1980「忽略反射光线」[Tape1980 p.1]；TK1999「光路从入射面进、直接从出射面出，无中间内反射」，仅以一次 normal-plane 内反射为例说「会得到一整本新 atlas」[TK1999 p.15]；TM2006 refraction halos 定义排除反射 [TM2006 p.139]，ch4 的 subsun（1、326）与幻日环只用光点图逐条画 [TM2006 p.48, p.50]，不分类。 |
| 20 | signature $(M,\mathbf n_a,M^{-1}\mathbf n_b)$、商掉 $D_{6h}$、34 类 | 定理 5、5′、5″ | **本系列多出（Tape 没有）** | 最接近的是 TK1999「哪些楔做同一个晕」：给定取向类下按 $(\alpha,\text{pole})$ 排序楔 [TK1999 p.29–30]，与 TM2006「35 与 46 的区别是面编号的偶然」[TM2006 p.48]——那是**在给定姿态族下**商掉晶体对称，本系列是**不看姿态**商掉 $D_{6h}$，且多了 $M$ 这一维。Wedge Change Rule 的 $w_v=v^{-1}wv$ [TK1999 p.36] 是 `canonical_signature` 里 $g$ 作用的楔系写法。 |
| 21 | atlas（$\alpha\times\mathbf P_u\times\psi\times\Sigma$）[TK1999 p.42, App. A]；pole diagrams（每楔角一张）[TK1999 p.62, App. B]；分类矩阵（楔角 × 取向类）[TM2006 p.141] | ch8 的 34 类 $\Phi$ 表（$(M,\text{楔角})$ 组织）；framework §5「行 = 光路类、列 = 姿态族」 | Tape 有而本系列没有（产品形态） | 两边的「行」不同：Tape 按 $\alpha$（连续）+ pole（连续），本系列按 $(M,\text{楔角})$（离散，有限）。Tape 的 atlas 没有 $M$ 这一维；本系列没有 pole 这一连续参数（姿态族只取了五族）。 |
| 22 | Bravais 坐标 $\mathbf B(\theta,\delta)$（pole 球面）[TK1999 p.6 Eq. (26)]；D-centered $(s,t)$ [TK1999 p.17] | 定理 8 底 $S^2\ni\mathbf u$ 上的坐标（本系列未选定） | 部分 | **不是天球坐标**——它们是「空间方向在楔系里」的坐标。子任务 3 若要画 $D_P(\mathbf u)$，可直接用 Bravais 网（极 = 楔棱），便于与 Fig. 9 的 level curves of $\Delta$ 对照。 |
| 23 | S-centered $(\Delta,\tau)$：到太阳的角距 + 从太阳量的 bearing（天球内部看顺时针）[TK1999 p.17 Eq. (53)] | 天球坐标：$\angle(\mathbf x,\mathbf s)=D_P(\mathbf u)$ + 方位 | 同物异名 | ch8 §6 的「方位 142°」是绕天顶沿幻日环量的方位角，$\Sigma=0$ 时等于 $\Delta$；TK1999 的 $\tau$ 是绕太阳的 bearing，二者不同（§5）。 |
| 24 | contact circle $\mathcal C(\alpha,\sigma)$、Criterion for Contact、Contact Point Theorem、Nonempty Halos Theorem [TK1999 p.16–22; TM2006 p.231] | 无独立对象 | Tape 有而本系列没有 | 用本系列语言可复述：contact ⇔ $Q$ 与定理 8 在最小偏折方向 $\mathbf u_D$ 上方的那条**纤维**相交；contact circle 就是这条纤维投到 #10 那个纤维化的底上的像。这一句是番外「两种语言互译」的现成素材，但本系列文档里没有写。 |
| 25 | Rules 1–4、「别无其它」定理、Face Interchange Rule、八个相关晕 [TK1999 p.22–26]；mmm 对称 [TK1999 p.37–38] | 定理 3（与 $R_z$ 对易）、ch8 §3 正/反向配对 | 部分 | Rule 1 = 方位不变性在天球上的表述；Face interchange「形状无简单关系」= 本系列 $\Phi$ 类不合并正反向对。x-rotation / z-reflection（换太阳高度符号）本系列没有。 |
| 26 | Table 3 / Table 8.1 的 8 个楔角 [TK1999 p.33; TM2006 p.86]；Eq. (9.1) [TM2006 p.102] | 定理 7 的 9 个楔角（含 0°）；楔角公式 | 同物异名 | 数值逐一相同（28.0/52.4/56.0/60/62.0/63.8/80.2/90）。本系列多「0°」（平行光路，$W=I$）与「以 $M$ 展开后仍成立」。 |
| 27 | Angle x [TM2006 p.7, p.101, p.123]；$\tan x=\frac{\sqrt3}{2}\frac ac|\frac lh|$ [TM2006 p.108 Eq. (9.6)] | 参数 $c/a$（定理 7；锥面法向与 c 轴夹 $62.0°=90°-28°$） | 同物异名（框架层面） | 见 §3.4：Tape 的「search」是哪个值为真 + 是否还有别的楔角；本系列只承接「给定 $c/a$ 后一切可算」这半句。 |
| 28 | light point / light point diagram [TM2006 p.43, p.50]；「光点」[TK1999 p.3] | 番外用语「光点法」 | 同物异名 | 是 Tape 自己的术语（TM2006 命名）；几何折射定律溯源 Hamilton、MacCullagh 1837 [TM2006 p.51]。 |
| 29 | caustic 的解析处理：Eq. (21) 显式核、Eq. (33)–(34) 奇点集方程数值解、Figs. 15–16 [Tape1980 p.5, p.15, p.11] | — | Tape 有而本系列没有 | issue 点名的那一项。本系列 ch10 计划「22° 晕的 $F$、$DF$ 数值」（roadmap）应以 Prop. 2 为起点而不是重推。 |
| 30 | Tape 1980 自陈「caustic 强度没有简单解析度量」[Tape1980 p.16]；Können 1983 在五个理想化假设下给出近晕角解析强度分布与 halocaustic 形状 [Können1983 p.1, p.3, p.10] | fold 律 $1/\sqrt{D-D_{\min}}$ + $\rho\,w_P$ 权重 + $SO(3)$ 卷积（framework §4–5） | 部分 | 不能再把 Tape 1980 的自陈写成后续文献一直未补的缺口；Können 1983 已补理想化解析强度，本系列多出的是任意 $\rho$、光路权重与卷积的统一 pushforward 语言。Können 1998 主要研究内边缘偏振，只把辐亮度陡峭度当作偏振可见性的因素 [Können1998 p.4]。 |
| 31 | Tricker 1973：六棱柱侧面的逐次镜像；平行底面上的入、出折射等量；长六棱柱就是简单万花筒 [Tricker1973 p.4, Fig. 4] | 内反射总矩阵 $M$；平行光路 $W=I$、$\Phi=M$（ch3、ch7、framework §2–3） | 同物异名（限平行光路） | Tricker 用镜像点逐步作图，本系列把同一串反射合成为一个 $O(3)$ 元素。它是一条具体光路机制，不含一般 $M\circ W$ 分解，也不含 12 类 / 34 类的分类。 |

**总括**：Tricker 1973 给出 $W=I$ 时逐次镜像合成 $M$ 的古典实例（#31）；Tape 三篇给出本系列 $W$ 那一半（#6–9）+ 取向 → 光点映射的两种纤维化几何（#3–5、#10）+ 奇点/caustic 的解析工具（#13–16、#29）+ 一套按 $(\alpha,\text{pole})$ 的连续分类与 atlas（#11、#21–25）。Können 1983 又补上理想化条件下的近晕角强度解析（#30）。本系列的合流点是把两边放进同一个 $\Phi=M\circ W$：再做不看姿态的 signature 商与有限类数（#20），并加入任意姿态分布 $\rho$ 与光路权重下的 pushforward / 卷积语言（#17–18、#30）。Tape 有而本系列没有的是：caustic 解析（#29）、最小偏折 ≠ caustic 的警示（#16）、contact / nonempty 定理（#24）、太阳高度变换规则（#25）、atlas 产品（#21）。

## 5. 记号差异表

子任务 3 写换算时按这张表对，任何一处数值对不上先怀疑换算约定，再怀疑公式（scrum.md 风险 2）。

| 项 | Tape 1980 | TK1999 | TM2006 | 本系列 | 换算 / 提醒 |
|---|---|---|---|---|---|
| 楔角 | refracting angle $\alpha$ = 从 $\hat{\mathbf N}_1$（入射面**内**法向）到 $\hat{\mathbf N}_2$（出射面**外**法向）的角，$0<\alpha<180$ [p.1] | wedge angle $\alpha$ = 入射面与出射面的夹角；$\mathbf N$（入射面**外**法向）$\cdot\mathbf X$（出射面**内**法向）$=\cos\alpha$ [p.4 Eq. (10)] | $\cos\alpha=-\mathbf N_i\cdot\mathbf N_j/(\lvert\mathbf N_i\rvert\lvert\mathbf N_j\rvert)$，两者都是**外**法向 [p.102 Eq. (9.1)] | 楔角 $A$，$\cos A=-\langle\mathbf n_a,M^{-1}\mathbf n_b\rangle$，外法向，展开后 | **四者数值相同**：$\alpha=A$。差别只在哪个法向取内、哪个取外。本系列只说「楔角」，不说「法线夹角」（= $180°-A$）。 |
| 通光上限 | $\sin(\alpha/2)\le n^{-1}$ [p.2] | $\alpha_{\max}=99.5$ [p.11] | $n\sin(\alpha_{\max}/2)=1$，99.5 [p.86 Eq. (8.2)] | $2\arcsin(1/n)\approx99.5°$（定理 5） | 相同。 |
| 圆晕半径 | $-D_{\min}(90)$：21.8 / 45.7 [p.5] | $\sin[(\alpha+\Delta_m)/2]=n\sin(\alpha/2)$ [p.9 Eq. (41)] | 同左 [p.86 Eq. (8.1)]，21.8 / 45.7 | $\min_{\mathbf u}D_P(\mathbf u)$ | 相同（$n=1.31$）。 |
| 光线 vs 光点 | $\hat{\mathbf I},\hat{\mathbf R}$ 是**光线传播方向**单位向量；光点 $=-\hat{\mathbf R}$，太阳 $\hat{\mathbf S}=-\hat{\mathbf I}$ [p.2; p.18 note 18] | 全程用**光点**：$\mathbf S=-\mathbf I$、$\mathbf T=-\mathbf J$、$\mathbf H$；向量长度 = 所在介质折射率 [p.3] | 同 TK1999，天球半径 = 折射率 [p.48] | `signature.phi(d)`：`d` 是**外部入射传播方向**，定义域 $\langle\mathbf d,\mathbf n_a\rangle<0$；framework §4 原写 $\mathbf x=R\Phi_P(R^{-1}\mathbf s)$（**已修正（chore framework-fixes）**：现为 $\mathbf x=-R\Phi_P(-R^{-1}\mathbf s)$，与本行给出的严格写法一致） | **本系列两处约定不一致**（$\Phi$ 作用在传播方向 vs 作用在太阳方向 $\mathbf s$）。严格写法：$\mathbf x=-R\,\Phi_P(-R^{-1}\mathbf s)$（光点 = $-$出射方向，入射方向 = $-$太阳方向）。$D_P$ 的定义 $\angle(\Phi_P(\mathbf u),\mathbf u)$ 在两种写法下相等（同时取负不改变夹角），不影响定理 8，但子任务 3 逐点比对光点时必须取 $-\Phi(-\cdot)$。→ §7 上抛。 |
| 太阳位置 | $(\cos\Sigma,0,\sin\Sigma)$，$\Sigma$ 太阳高度；然后转到 $uvw$ 系使太阳 $=(1,0,0)$ [p.4] | $\mathbf S$ 任意空间向量；$\sigma=90-\Sigma$ 太阳天顶角 [p.12]；Rule 1 说方位无关 [p.22] | $\Sigma$ 太阳高度、$\sigma$ 天顶角 [p.152] | $\mathbf s$ | 相同物理量；Tape 1980 把太阳放在 $xz$ 平面内、TK1999 的 halo 定义把太阳当自变量。 |
| 空间坐标轴 | $xyz$，$z$ 向上（$\Sigma=90$ 时 $u^\circ v^\circ w^\circ=z,y,-x$ [p.12]） | $\mathbf k=(0,0,1)$ 天顶 [p.2]；TM2006 明说 $x$ 朝前、$y$ 朝右、$z$ 朝上 [TM2006 p.147] | 同 TK1999 | `HexPrism`：$\mathbf n_1=+z$；天球方向约定见各章脚本 | 相同手性（右手）；「前」= 太阳方向所在的一侧（TK1999 standard orientation 入射面朝前）。 |
| 取向参数化 | $(\theta,\mu,\beta)$：$\theta$ = $\hat{\mathbf P}$ 与 $\hat{\mathbf S}$ 夹角（$0\le\theta\le180$）、$\mu$ = 绕 $\hat{\mathbf P}$ 从 $\hat{\mathbf N}_1$ 量的投影入射角（$-90\le\mu\le\mu_L$）、$\beta$ = 绕 $u$ 轴（太阳）的旋转（mod 360）[p.4]；或 $(\hat{\mathbf P},\hat{\mathbf N})$ 正交对 [p.12] | $u\in SO(3)$，列 = $\mathbf A,\mathbf B,\mathbf C$，从 standard orientation 转到目标；**楔取向，不是晶体取向**——同一晶体取向对不同楔是不同的 $u$ [p.4; p.74 note 6, note 8] | 同 TK1999，非正式 [p.148, p.229] | $R\in SO(3)$ 晶体姿态，$T=R\Phi R^{-1}$ | TK1999 的 $u=R\,u_0$，$u_0$ = 楔 $ij$ 在晶体系里的 frame（列 $\mathbf A_0,\mathbf B_0,\mathbf C_0$ 由 Eq. (8) 以 $\mathbf N=\mathbf n_i$、$\mathbf X=-\mathbf n_j$ 算出）。**Tape 1980 的 $(\theta,\mu)$ 只覆盖通光的取向**（$\overline{\mathcal D}$），不是 $S^2$ 全部。 |
| 手性 / 角度正向 | normal plane 内所有角的符号由 $\hat{\mathbf P}$ 按**右手定则**定 [p.1]；$\beta$ 绕 $u$ 轴 [p.4]；$D<0$ 恒成立 [p.2] | $\mathbf A,\mathbf B,\mathbf C$ 右手系 [p.3]；bearing $\tau$、$t$ 从天球**内部**看**顺时针**为正、12:00 为 0 [p.17]；$\mathbf D(s,t)=\mathrm{rot}(-t,\mathbf D_u)\mathbf D(s,0)$ 带负号 [p.17 Eq. (52)]；$\mathbf B(\theta,\delta)$ 第三分量 $-\sin\theta\sin\delta$ [p.6 Eq. (26)] | compass bearing，3:00 = 90° [p.231] | 右手系；方位角沿幻日环从太阳量（ch8 §6） | 三处负号（Eq. (26)、Eq. (52)、$D<0$）是抄公式时最容易丢的地方。 |
| 「方位 142°」 vs bearing | — | $\tau$ = 从太阳量的 bearing（绕**太阳**）[p.17] | 同 | ch8 §6：沿幻日环的方位角（绕**天顶**） | $\Sigma=0$ 时幻日环 = 地平线，方位角 = 到太阳的角距 $\Delta$，bearing $\tau=\pm90$。 |
| 面编号 | 无（只有一个楔） | 底面 1、2，侧面 3–8 看着面 1 逆时针，$\mathbf N_4=\cos60\,\mathbf N_3+\sin60\,\mathbf N_1\times\mathbf N_3$；锥面 13–18、23–28 [p.27 Eq. (78); p.33 Eq. (79)] | 同 TK1999 [p.47, p.62] | `HexPrism` 面 1 = $+z$，3 = $+x$，4 = $(\tfrac12,\tfrac{\sqrt3}2,0)$，… | **完全一致**（本笔记开头核对）。wedge $ij$ 的 $i$ = 入射、$j$ = 出射，与本系列光路面序列首尾同序。 |
| 字母 $\mathbf P$ | axial vector（楔棱方向 $\hat{\mathbf N}_1\times\hat{\mathbf N}_2$）[p.1] | spin vector（固定在楔上、天顶角恒定）[p.2]；棱方向改叫 $\mathbf B$ | spin vector [p.143] | 光路 $P$ | 1980 的 $\hat{\mathbf P}$ = 1999 的 $\mathbf B$（同向，已核）。 |
| 字母 $\mathbf N$ | $\hat{\mathbf N}$ 入射面外法向、$\hat{\mathbf N}_1$ 内法向、$\hat{\mathbf N}_2$ 出射面外法向 [p.1] | $\mathbf N$ 入射面外法向；$\mathbf N_i$ 面 $i$ 外法向 [p.3, p.27] | $\mathbf N_i$ 外法向 [p.102] | $\mathbf n_a,\mathbf n_b$ 外法向 | — |
| 字母 $D$ | normal-plane 偏折角（负值）[p.2] | 最小偏折**入射向量** $\mathbf D$；偏折角是 $\Delta$ [p.9–10] | $\mathbf D$ 同 TK1999 [p.229] | $D_P(\mathbf u)$ 偏折角 | 三个 $D$ 三个意思。 |
| 字母 $\theta$ | $\hat{\mathbf P}$ 与 $-\hat{\mathbf I}$ 的夹角 [p.2] | Bravais 余纬（pole 球面）[p.6] | — | 定理 8 的纤维角 $\mathrm{Rot}_{\mathbf s}(\theta)$ | 三个 $\theta$ 三个意思；本笔记 §1 用 Tape 1980 的、§2 用 TK1999 的。 |
| 字母 $\Sigma$ / $\sigma$ / $s$ | $\Sigma$ 太阳高度 | $\Sigma$ 太阳高度、$\sigma$ 太阳天顶角、$s$ = $\mathbf P_u$ 到 $\mathbf D_u$ 的角距、$s_1,s_2$ 到入射区最近/最远距离 [p.16–17] | 同 | $\mathbf s$ 太阳方向 | — |
| 强度 / 权重 | 无 [p.1] | 无 [p.1] | 无（只说倾角）[p.153] | $\rho\,w_P$ | 见 §4 #17。 |

## 6. 锚定实例的可行性判断

### 6.1 22° 幻日（`3-5`，片晶）= 本系列 A60-12（`data/signature_table.md`）

三篇都能直接表示，且给出的对象一一对应：

- **Tape 1980**：幻日是一维晕，generating set 是 $\overline{\mathcal F}$ 中的水平直线 $\beta=90,\ \theta=90-\Sigma$（左幻日）或 $\beta=-90,\ \theta=90+\Sigma$（右幻日），由 $\hat{\mathbf P}$ 竖直（Eqs. (26)(27)）解出 [Tape1980 p.16]；左幻日 = 上切弧的 $\theta=90-\Sigma$ 那段圆弧绕太阳转 90° [Tape1980 p.16]；caustic 是单点 $F(90-\Sigma,\mu_M(90-\Sigma),90)$，幻日最内点 [Tape1980 p.16]。每段 $\{(\theta_0,\mu,\beta_0)\}$ 的像叫「幻日」，「圆晕是幻日的叠加」（Bravais）[Tape1980 p.12]；Fig. 7 里上切弧上的圆弧段 [Tape1980 p.4]。幻日在 Figs. 9–13 里作为子集出现 [Tape1980 p.16]。
  - 可算的量（给子任务 3）：太阳高度 $\Sigma$ 下幻日内边到太阳的角距 $=\Delta(90-\Sigma,\mu_M(90-\Sigma))$，由 Eqs. (10)(11)(15) 得 $\sin(\Delta/2)=-\sin(90-\Sigma)\sin(D_{\min}(90-\Sigma)/2)$，$D_{\min}(\theta)=\alpha+2\mu_M(\theta)$，$\sin\mu_M(\theta)=-n'(\theta)\sin(\alpha/2)$，$n'(\theta)=(n^2-\cos^2\theta)^{1/2}/\sin\theta$。$\Sigma=0$ 时 $\theta=90$、$n'=n$、$\Delta=-D_{\min}(90)=21.8°$。
- **TK1999**：Plate 3 5 与 Plate 3 7 是左、右 22° 幻日，在幻日环上，互为 face interchange 与左右镜像 [TK1999 p.32]；pole $\mathbf P_u=(0,\pm1,0)$（spin vector $\mathbf N_1$ 平行于楔棱）[TK1999 p.6, p.32]；Fig. 33 中 $(0,1,0)$ 处的晕「可能看着眼熟——它是右 22° 幻日」[TK1999 p.7]；Fig. 55 的 22° pole diagram [TK1999 p.66]；$\alpha=60$，point halo（$\psi=0$）。46° 幻日是 AP 1 3 / AP 3 1，整个落在幻日环上（$\mathbf k_u$ 在 Bravais 极上，sun locus 与一条 Bravais circle 重合）[TK1999 p.31]——同一论证对 22° 幻日成立（它们的 $\mathbf k_u$ 也在 Bravais 极上）。
  - 可算的量：$\mathbf H(u,\alpha,\mathbf S)=\mathrm{pr}[\mathrm{pr}(\mathbf S,u\mathbf N_0,n),u\mathbf X_0,1]$，$u=\mathrm{zrot}(\phi)\,u_0$，$u_0$ 把 $\mathbf P_u=(0,1,0)$ 转到 $\mathbf k$（如绕 $x$ 轴转 $+90°$，$(0,1,0)\mapsto(0,0,1)$），$\phi\in[0,360)$；内边 = $\min_\phi\arccos(\mathbf S\cdot\mathbf H)$。
- **TM2006**：PH 35、37 [TM2006 p.63 Fig. 6.2 表]；片晶下楔 35 做左幻日、楔 37 做右幻日 [TM2006 p.140]；Fig. 4.3「进一个侧面、出隔一个的侧面」→ 左幻日 [TM2006 p.46]；右幻日的 pole 是 $(0,1,0)$ [TM2006 p.150]；35 与 46 都给左幻日、区别是面编号的偶然 [TM2006 p.48]（= 本系列商掉 $D_{6h}$）。
- **本系列**：A60-12，楔角 60°，$M=I$（#12），$3\to5$，五档 $h/a$ 全可达 [`data/signature_table.md`]；片晶姿态族 + 定理 8：$D_P(\mathbf u)$ 沿片晶的 $\mathbf u$ 轨迹（绕 $\mathbf c$ 轴的圆）取最小 = 幻日内边。

**判断：可行，三种语言算同一个数（幻日内边角距随 $\Sigma$ 的曲线）。** 子任务 3 的互证目标建议就取这条曲线（$\Sigma=0,10,20,30$）+ $\Sigma=0$ 时的完整光点轨迹。

### 6.2 A60-10（`3-4-5-7`，60° 楔 + 120° 折叠，ch8 §6「142° 幻日」）

白盒事实（本机核验，见 progress M1）：`3-4-5-7` 的 $M=\mathcal S_{\mathbf n_5}\mathcal S_{\mathbf n_4}=R_{\mathbf c}(120°)$（绕晶体 c 轴转 120°），$M^{-1}\mathbf n_7=\mathbf n_5$，展开楔是面对 $(\mathbf n_3,\mathbf n_5)$——**与幻日同一个楔**；且 $\Phi_{3457}=M\circ\Phi_{35}$ 在共同定义域上逐点相等（最大差 $6.7\times10^{-16}$）。

- **Tape 1980**：不能表示。文章开头就「忽略反射光线」[Tape1980 p.1]，$F$ 只依赖 $\alpha$ 与 $n$ [Tape1980 p.13]，没有任何对象承载 $M$。
- **TK1999**：框架本身排除——「本文考虑的光路从入射面进、直接从出射面出，无中间内反射」[TK1999 p.15]；wedge $ij$ 由**物理**入射面 $i$、出射面 $j$ 定义 [TK1999 p.27]，`3-4-5-7` 的物理出射面是 7、展开出射面是 5，TK1999 没有「展开楔」这个对象。§2.E 只给了一个例子（一次在 normal plane 内的反射 → $\mathbf H_u$ 关于 $y=0$ 反射）并说「任何其它新光路都会得到一整本新 atlas」[TK1999 p.15]。**但对片晶这一族，A60-10 可以作为 TK1999 的一个推论表示出来**：片晶姿态 $R=\mathrm{zrot}(\phi)R_0$，$\mathbf c\parallel\mathbf k$，于是 $RMR^{-1}=\mathrm{zrot}(120°)$，$T_{3457}=\mathrm{zrot}(120°)\,T_{35}$，天球上的光点 $\mathbf H_{3457}=\mathrm{zrot}(120°)\mathbf H_{35}$——由 Rule 1 [TK1999 p.22 Eq. (67)]，这正是「把 Plate 3 5 幻日整体绕竖直转 120°」：$\Sigma=0$ 时幻日内边 21.8° → 141.8°，即 ch8 §6 报告的 142° 锐边（ch8 测的是半高点 142.56°，在锐边外侧，方向一致；精确对齐留子任务 3）。**这个表示成立的唯一原因是 $M$ 恰好是绕 spin vector 的旋转**（$M\in$ 绕 $\mathbf P=\mathbf N_1$ 的旋转群，经 $R$ 共轭后落进 $Z$）。换成柱晶 / Parry 姿态族，$RMR^{-1}$ 不再绕竖直，TK1999 的 atlas 里没有它，只能落到 p.15 那句「新 atlas」。
- **TM2006**：refraction halos 定义排除反射 [TM2006 p.139]；含反射的晕（subsun 1 / 326、幻日环、120° 幻日 1342 / 1382）只在 ch4、ch6 用光点图逐条画 [TM2006 p.48, p.63]，不进 pole theory。120° 幻日（1342，平行光路，本系列 $M=r$ 的 $\Phi=M$）与 A60-10（同一个 $M$ 接在 60° 楔后）在 TM2006 里是两个无关条目——本系列把它们放进同一行（折叠 #4/#6）、不同列（楔角 0° vs 60°）。
- **本系列**：A60-10 = $(M=\#4/\#6,\ \text{楔角 }60°,\ 3\to7)$ [`data/signature_table.md`]；与 A60-12（幻日）同楔、不同折叠；与 A0 族的 120° 幻日同折叠、不同楔。ch8 §6：这一格给 142° 锐边的宽鼓包，幻日环那一格（A0-02，平行光路）给外侧的 Liljequist 窄峰 [ch8 §6]。

**判断：A60-10 在 Tape 的 wedge 框架里没有位置（三篇的范围声明都排除内反射）；折叠 $M$ 在他们那里只以「一次反射 → 反射一下 $\mathbf H_u$、再画一本 atlas」的形式出现 [TK1999 p.15]，没有被当作独立于楔的第二个分类维度。** 对片晶可以借 Rule 1 把它写成「幻日转 120°」，但这恰恰说明了番外的落点：**古典几何能解释这一个实例（幻日，甚至它转 120° 的复制品），现代代数分类的是「楔 × 折叠」这个结构**——A60-10 是「同一个楔（幻日的楔）× 一个非平凡折叠」，$W$ 这一半 Tape 已经做完，$M$ 这一半是本系列加的。子任务 3 的第二个互证目标建议取：片晶、$\Sigma=0$，用 TK1999 的 $\mathbf H(u,60,\mathbf S)$ 算 Plate 3 5 光点轨迹，$\mathrm{zrot}(120°)$ 后与本系列 `phi(M=fold_matrix(3-4-5-7), 3, 7)` 在片晶姿态上的光点轨迹逐点比（预期逐点相等到浮点精度）；再用柱晶姿态跑同一比较，预期 Tape 侧**无对应对象**，只能与本系列自己的 $\Phi_{35}$ 经 $RMR^{-1}$ 共轭的结果比——这一步就是「Tape 框架到此为止」的可展示证据。

## 7. 文献核对清单（含已解决项）

不在本机的文献涉及的断言、阅读中遇到的不确定点，以及后续检索已经解决的项目。每条注明为什么要核对、与正文哪条断言相关；已解决项保留在原编号上，避免番外提纲中的转写表漂移。

| # | 待核对 | 为什么 | 关联 |
|---|---|---|---|
| 1 | **部分解决（作者补充，2026-09-21）**：同心圆作图本身不再待核——TM2006 Figs. 4.5、4.8 直接说明 [TM2006 p.48, p.51]。Tricker 1973 又直接确认了另一件事：他确实用六棱柱侧面的逐次镜像分析「万花筒」光路，并说明平行底面上的入、出折射等量 [Tricker1973 p.4]。仍待核的是 Tricker 1970 是否使用同心圆图式、用的名字是什么（"point of light"? 别的?） | 番外可分别据 TM2006 写标准同心球折射作图、据 Tricker 1973 写万花筒式纯折叠；不能把两者未经原书便合并成「Tricker 1970 的光点图」。作者判断它们属于同一古典几何传统，但直接继承关系仍应标为推断 | §T、§3.1、§4 #8/#28/#31、番外提纲 |
| 2 | 「光点法」这个称呼是否 Tape 自己的用语：本笔记已核实 "light point" [TK1999 p.3]、"light point diagram" [TM2006 p.50] 是 Tape 的术语；Tape 1980 用的是 "point of light" [Tape1980 p.1, p.18 note 18]。**待核对的只剩**：Tricker 1970 是否也这么叫（同上条）；ch2 正文引用 Tape 时用的原话是什么 | 番外标题用词 | §3.1 |
| 3 | Tape 1994 *Atmospheric Halos*（本机无）：TK1999 [11] 与 TM2006 [76] 多处引它——TK1999 p.35 说 Sturm 照片在 Ref. 11 p.92、p.39 说 MC 方法在 Ref. 11 pp.132–133；TM2006 p.61 说光路图与更多仿真在 [76]；TM2006 p.202 说 Hevel 晕 [76] 也「一无所获」。1994 书里是否已有 pole / spin vector 的雏形（TM2006 p.147 说 pole 是 Können 1990 年代提出，1994 书应尚无），以及 Tricker 万花筒展开在 1994 书里的处理 | 番外若要说「Tape 1994 还没有 pole」需原书页码 | §3.3、§4 #11 |
| 4 | **已解决（2026-09-21）**：fold / pleat 在 Tape 1980 p.14 已出现；1982 年是 Tape, *Folds, pleats, and halos*, *American Scientist* 70, 467–474；1983 年另有 Tape, *Halos and Singularities*（DOI `10.1364/MO.1983.FA4`），Optica 摘要明确称其为 1982 文的技术扩展，并点名 folds / pleats。framework §4 已改成这条三阶段文献链 | 原来的「1983」不是 Können 1983，也不应暗示 fold / pleat 到 1983 才出现 | §1.4、§4 #15、framework §4 |
| 5 | **部分解决（2026-09-21）**：TM2006 [74] 后来高度吻合 Walter Tape, *Maximum deviation of light in a transparent wedge*, *Applied Optics* 47, H44–H51 (2008)，DOI `10.1364/AO.47.000H44`。正式摘要明确求透明楔最大偏折，并说明它等价于圆晕外半径；全文仍需订阅，尚不能确认是否与 2006 的待刊稿逐字相同，或是否完整包含 p.89 的分段式 | ch10 可引用 2008 正式出处；若要逐式核对 $\Delta_{\max}$，仍需全文 | §3.1 |
| 6 | **已解决（2026-09-21）**：Können 1983 全文确认，在五个理想化假设下以 $I\propto dN/d\omega$ 推出近晕角的简单解析强度分布与 halocaustic 形状 [Können1983 p.1, p.3, p.10]；Können 1998 主旨是 inner-edge polarization，仅把边缘辐亮度陡峭度列为偏振可见性的因素 [Können1998 p.4] | §4 #30 已从「本系列多出」改成「部分」；番外不展开，转交 ch10 | §4 #30 |
| 7 | **已修正（chore framework-fixes）**：本系列自身：framework §4 原写 $\mathbf x=R\Phi_P(R^{-1}\mathbf s)$，与 `signature.phi(d)`（`d` 为入射传播方向）的符号约定不一致（§5「光线 vs 光点」行）。建议 framework 改写为 $\mathbf x=-R\Phi_P(-R^{-1}\mathbf s)$ 或明注「$\Phi$ 此处按光点约定理解」。本任务不改 framework（越界），上抛。**子任务 3 已按严格写法实现 `crosscheck_bridge.light_point` 并通过全部互证（`data/notes.md` §1、§3），是「该行应改写」的数值证据；仍上抛**——`chore-framework-fixes` 已据此把 framework §4 改为 $\mathbf x=-R\Phi_P(-R^{-1}\mathbf s)$，与本条建议一致 | 子任务 3 逐点比对光点时必须先定这一条 | §5 |
| 8 | ch8 §6 的「142.56°」是半高点，与 $21.8°+120°=141.8°$ 的锐边理论值差 0.7°——差值是否全部来自半高定义 + 太阳角径 + 截面权重，待子任务 3 用零角径、片晶零倾角的设置重算。**已用 `crosscheck_b.py` 数值验证：锐边理论值 141.8393° = Δ_m(60°) + 120°，与 142.56° 的差归因于半高定义 + 0.5° 桶 + 角径 / 倾角展宽，见 `data/notes.md` §2** | §6.2 的「142° = 幻日转 120°」是精确陈述，数值验收要对到锐边而不是半高 | §6.2 |
| 9 | Tape 1980 Eq. (32) 的 $\varphi$ 取值表里 "infralateral" 出现两次（$\varphi=-\alpha$ 与 $\varphi=\alpha$）[Tape1980 p.14]——按 $\lambda$ 只定义到 mod 180 [Tape1980 p.13] 应是 $\lambda=0$ 与 $\lambda=180$ 两个分支，不是笔误；若子任务 3 要复现 infralateral 需两支都取 | §1.3 | 
| 10 | TK1999 Fig. 55（22° pole diagram，p.66）与 Fig. 59（46°，p.71–72）的表格数值（$s_1,s_2,s,t$）本笔记未逐格抄录（属 atlas 图集，Step 3 的范围声明不通读）；子任务 3 若要对 Plate 3 5 的 $s_1,s_2$ 数值，需回 p.66 抄 | §2.4、§6.1 |

## 附录 A. 给子任务 3 的公式包（按实现顺序）

所有公式已在 §1–§3 抄录并带页码，此处只列**实现顺序与符号表**，不再重复推导。

**A.1 TK1999 路线（推荐作为 Tape 侧的实现，最短）**

输入：$\alpha$（楔角，度）、$n=1.31$、$\mathbf S$（太阳光点，单位向量，$=-$入射传播方向）、取向矩阵 $u\in SO(3)$。

1. $\mathbf N_0=[\cos(\alpha/2),0,\sin(\alpha/2)]$，$\mathbf X_0=[\cos(\alpha/2),0,-\sin(\alpha/2)]$ [TK1999 p.4 Eq. (10)]。
2. $\mathbf N=u\mathbf N_0$，$\mathbf X=u\mathbf X_0$ [Eq. (9)]。
3. $\lambda(\mathbf S,\mathbf N,n_2)=[(\mathbf S\cdot\mathbf N)^2+n_2^2-n_1^2]^{1/2}-\mathbf S\cdot\mathbf N$，$\mathrm{pr}(\mathbf S,\mathbf N,n_2)=\mathbf S+\lambda\mathbf N$ [Eqs. (2)–(3)]；定义域：$\mathbf S\cdot\mathbf N\ge0$ 且根号内 $\ge0$ [p.3]。
4. $\mathbf T=\mathrm{pr}(\mathbf S,\mathbf N,n)$（$n_1=1,n_2=n$）；$\mathbf H=\mathrm{pr}(\mathbf T,\mathbf X,1)$（$n_1=n,n_2=1$）[Eqs. (6)–(7)]。无定义 → "no ray"。
5. 姿态族：SVA，$u\in U\iff u\mathbf P_u\cdot\mathbf k=\cos\psi$ [Eq. (25)]；片晶（point halo）$\psi=0$、$U=Z u_0$，$u_0\mathbf P_u=\mathbf k$，$u=\mathrm{zrot}(\phi)u_0$。
6. 对楔 $ij$：$\mathbf N=\mathbf N_i$、$\mathbf X=-\mathbf N_j$（晶体系外法向），frame $u_0$ 的列 $=(\mathbf A,\mathbf B,\mathbf C)$ 由 Eq. (8) 算；pole $\mathbf P_u=u_0^{-1}\mathbf P$ [Eqs. (8), (21)]。
7. 输出：$\Delta=\arccos(\mathbf S\cdot\mathbf H)$ [Eq. (40)]；校验 $\Delta_m$：$\sin[(\alpha+\Delta_m)/2]=n\sin(\alpha/2)$ [Eq. (41)]。

**A.2 Tape 1980 路线（作为第二独立链路，验 Bravais 定律版本）**

输入：$\alpha,n,\Sigma$，取向 $(\theta,\mu,\beta)$。

1. $n'(\theta)=(n^2-\cos^2\theta)^{1/2}/\sin\theta$ [p.2]。
2. $\sin r=\sin\mu/n'$，$\mu'=r+\alpha$，$\sin r'=n'\sin\mu'$，$D=\alpha+\mu-r'$ [Eqs. (1)–(4)]；定义域 $\overline{\mathcal D}$ 由 Eqs. (5)–(6)。
3. $A(\theta,\gamma)$ [Eq. (19)]；$F=R_\beta(A(\theta,D(\theta,\mu)))$，$R_\beta$ 绕 $u$ 轴 [Eq. (20)]；$uvw\to xyz$：绕 $y$ 轴转 $+\Sigma$（$uvw$ 是 $xyz$ 转 $-\Sigma$ 得到的）[p.4]。
4. 光点 $=F$ 本身（$F$ 的值已经是光点 $-\hat{\mathbf R}$）[p.18 note 18]。
5. 片晶：$\beta=\pm90$、$\theta=90\mp\Sigma$、$\mu\in[-90,\mu_L(\theta)]$ [p.16]。
6. 校验：$\sin(\Delta/2)=-\sin\theta\sin(D/2)$ [Eq. (15)]；$\ker JF$ [Eq. (21)] 可选。

**A.3 本系列侧**：`halo_notes.math.signature.phi(crystal, M, a, b, d)`，`d` = 入射传播方向 $=-\mathbf S$（片晶姿态 $R$ 下 $\mathbf d=-R^{-1}\mathbf S$），光点 $=-R\,\Phi(\mathbf d)$（§5「光线 vs 光点」行）。楔 $ij$ ↔ `a=i, b=j, M=I`；A60-10 ↔ `M = fold_matrix(3-4-5-7)`（$=R_{\mathbf c}(120°)$）、`a=3, b=7`。

**A.4 符号表（互证脚本统一用本系列符号，Tape 符号只出现在注释里）**

| 本系列 | TK1999 | Tape 1980 | 含义 |
|---|---|---|---|
| $A$ | $\alpha$ | $\alpha$ | 楔角 |
| $n$ | $n$ | $n$ | 折射率 1.31 |
| $\mathbf n_a$ | $\mathbf N$ | $\hat{\mathbf N}=-\hat{\mathbf N}_1$ | 入射面外法向 |
| $\tilde{\mathbf n}_b$ | $-\mathbf X$ | $\hat{\mathbf N}_2$ | 出射面外法向（展开后） |
| $-\mathbf n_a\times\tilde{\mathbf n}_b$ 方向 | $\mathbf B$ | $\hat{\mathbf P}$ | 楔棱 |
| $\mathbf s$ | $\mathbf S$ | $\hat{\mathbf S}=-\hat{\mathbf I}$，在 $uvw$ 系 $=(1,0,0)$ | 太阳方向（光点） |
| $-\Phi_P(-\mathbf u)$ 经 $R$ | $\mathbf H$ | $F$ | 晕点（光点） |
| $\mathbf u=R^{-1}\mathbf s$ | $\mathbf S_u$ | $(\theta,\mu)$ | 太阳在楔/晶体系 |
| $\mathrm{Rot}_{\mathbf s}(\cdot)$ | — | $\beta$ | 绕太阳的纤维 |
| $Q$ / $\mathrm{supp}\,\rho$ | $U$、$K$ | $\mathcal N$ | 姿态族 |
| $\mathbf c=\mathbf n_1$ | $\mathbf P=\mathbf N_1$（plate / column） | $\hat{\mathbf P}$ 竖直（幻日）| 片晶轴 |
| $D_P(\mathbf u)$ | $\Delta$ | $\Delta$ | 偏折角 |
| $\min D_P$ | $\Delta_m$ | $-D_{\min}(90)$ | 圆晕半径 |
| $M$ | —（p.15 一句话） | — | 折叠 |
