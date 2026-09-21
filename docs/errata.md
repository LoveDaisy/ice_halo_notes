# 勘误表

> 已发表各章（公开上映版冻结在 vault `Writing/articles/`，知乎不回改）在后续写作与工具重建中被发现的错误。每条记：位置、错在哪、怎么发现的、处置状态。
> 状态：`已改正`（导演剪辑版正文已改，附 commit）/ `已发现，待作者裁定`（只记录，正文未动）。
> 新发现的错误一律先在这里登记，再由作者决定改不改、怎么改；不得只改正文不登记。

| # | 章 / 位置 | 错误 | 发现方式与日期 | 状态 |
|---|---|---|---|---|
| 1 | ch1《迷镜千幻不离宗》第 76 行，D6 翻转公式 | 原文 $F^f_k(n)\equiv -n-k$、$F^d_{k,k+1}(n)\equiv -n+k \pmod 6$ 逐字套用会得到 $F^f_3\equiv F^d_{4,5}$ 重合、只剩 5 个不同翻转，不构成 D6，与同章图 1.6 / 群表 1.7 矛盾。正确为 $F^f_k(n)\equiv 2k-n$、$F^d_{k,k+1}(n)\equiv 2k+1-n$（图对、公式错）。 | 2026-09-12 `task-data-figs` 用 python 重出乘法表 1.7 时按公式实现与图不符，独立验算后确认（`halo_notes/math/group.py` 模块 docstring 有推导） | 已改正：`c150984`（chore figures-followup，合入 `f8f8106`） |
| 2 | ch1 第 29 / 49 行，幻日左右 | 原文写 3-5 光路是左幻日、3-7 是右幻日，左右颠倒。 | 2026-09-12 `task-sim-glue` 重制 1.5 时对 Lumice 输出取证：Lumice 与本仓面编号手性相同，3-5 = 右幻日、3-7 = 左幻日 | 已改正：`c150984`（同上；图与 config 不动，只改文字） |
| 3 | ch2《计算机遍历、搜索、优化》第 90 行，`1-3-2` 的最小入射角 | 原文说优化得到 $\cos\theta=0.998$（入射角 ≈3.6°）。精确的方向扫描判定（`halo_notes.geometry.feasibility`）显示最小入射角随网格细化趋于 0°：ch2 的内点法把解挡在多边形边界内侧，3.6° 是障碍项造成的局部最优，不是真最小值。定性结论（几何、光学均可行）不变。 | 2026-09-14 scrum `raypath-enumerator` 15.2（`scratchpad/scrum-raypath-enumerator/task-feasibility-enumerator/progress.md` 22:41 DECISION） | 已发现，待作者裁定 |
| 4 | ch2 第 94 行，`1-3-4`「几何上成立、光学上不成立」 | 原文说最小入射角 74.5° > 临界角 49.8°，光学不可行。精确判定：**几何+光学均可行**——存在贴 3/4 公共棱、以 ≈89.8° 掠射面 3 的光线，出射角 49.25° < 49.76°；可行方向集只有 0.0005 sr 的细缝。ch2 的 74.5° 同样是内点法局部最优。`entry_points` 构造的见证光线喂 `trace` 复核面序列恰为 1-3-4。 | 同上（15.2）；Lumice 4.6.x `analyze` 蒙特卡洛在 h/a=0.2 也命中该链 | 已发现，待作者裁定（是否在正文改例子 / 加注） |
| 5 | ch2 第 108–113 行，片晶 h/a=0.2 光路计数 25 / 61 / 169（长度 4/5/6） | 新枚举器得 31 / 70 / 147（去掉方向集面积 <0.003 sr 的细缝后 27 / 64 / 139）；长度 ≤3 的 18 条逐条相等。多出的全是细缝，少的（长度 6 约 20 条）ch2 未发表清单无法逐条对；独立蒙特卡洛 10⁶ 射线命中 27/66/146 全部 ⊆ 新枚举。「a 取直径」假说已排除（h/边长=0.4 时长度 6 为 152）。ch2 数字更可能含优化残差容差放进来的条目，尚未坐实。 | 同上（15.2）；主 session 探针 2026-09-15 | 已发现，待作者裁定（建议正文加注「计数依赖判据与容差」，不改数字） |
| 6 | ch8《三种楔子、十二种折叠》§1 第 65 行与参考资料第 333 行，「Tricker 的万花筒展开」 | 参考资料只列 Tricker 1970 *Introduction to Meteorological Optics*（本机无书，未核）。万花筒逐次镜像的一手来源是 R. A. R. Tricker, *A simple theory of certain heliacal and anthelic halo arcs. The long hexagonal ice prism as a kaleidoscope*, Q.J.R. Met. Soc. 99 (1973) 649–656（p.652 明说「theory is identical to that of the simple kaleidoscope」）。且 Tricker 1973 直接对应的是平行光路 $W=I,\ \Phi=M$，正文「Tricker 的万花筒展开……都联系在了一起」的合流口径应理解为「逐次镜像合成为 $M$，非平行首尾面的 $W$ 是本系列补的另一半」。 | 2026-09-21 作者补入 Tricker 1973 PDF 逐页复核（`scratchpad/DRAFT-DISCUSS-BOARD-ch9-ex.md` 23:27 条；`ex-tape-vs-matrix/源笔记-Tape.md` §T） | 已发现，待作者裁定（建议参考资料补 Tricker 1973；1970 书是否也含此构造待原书） |

## 备注

- 已发表章的导演剪辑版可以改，公开版不改；改正后在本表补 commit。
- ch2 的三条同源：当年用 `fmincon` 内点法解一个实际非凸（$s_k\mathbf q_1$ 双线性）的问题，障碍项让解停在多边形边界内侧。新判据见 `docs/framework.md` §2 定理 5″ 与 `halo_notes/geometry/feasibility.py`。
