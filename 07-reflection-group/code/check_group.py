# 核验 docs/framework.md 定理 1/2/3/5：六棱柱镜面生成群 |G|=12、共轭类 = ch3 发表的 6 类、
# 特征值只得 5 类（#11 并入 #2）、与 Rz 对易的元素、可能的楔角余弦。
# 冰晶标准坐标同 ch3：面 1/2 为 ±z 底面，面 3..8 为方位角 0°,60°,...,300° 的侧面。
# 计算本体在 halo_notes.math.reflection_group（12 矩阵权威表，图 3 / 5 / 6 与单测共用）；本脚本只跑一遍并打印，
# 断言同时进 halo_notes/math/tests/test_reflection_group.py。
from halo_notes.math.reflection_group import (ELEMENTS, GROUP, GROWTH, PUBLISHED, commuting_with_rz, conjugacy_classes,
                                              eigenvalue_classes, key, published_classes, wedge_cosines)

seen = {key(g) for g in GROUP}
print("|G| =", len(GROUP), " 闭包按字长增长:", GROWTH)

# ch3 工作笔记「平行光路矩阵归总」的 12 个矩阵，及发表表格的类型编号
assert all(key(e.matrix) in seen for e in ELEMENTS), "笔记里的 12 个矩阵不全在 G 里"
assert len({key(e.matrix) for e in ELEMENTS}) == 12 == len(GROUP), "笔记的 12 个矩阵 ≠ G"

# G 下的共轭类 vs 发表的 6 类
g_classes, p_classes = conjugacy_classes(), published_classes()
print("G-共轭类   :", g_classes)
print("发表的 6 类:", p_classes)
assert g_classes == p_classes, "G-共轭类与发表表格不一致"

# 特征值（O(3) 共轭）分类：太粗
ev = eigenvalue_classes()
print("特征值分类 :", ev, " ← #11 并入 #2/8/10，只有", len(ev), "类")

# 与 Rz(θ) 对易 ⇔ 锐利（柱晶弧 / 片晶点）
commuting = commuting_with_rz()
print("与 Rz 对易 :", commuting, " ← 发表类型", sorted({PUBLISHED[i] for i in commuting}))
assert sorted({PUBLISHED[i] for i in commuting}) == [3, 4, 5, 6]

# 楔角：<n_a, M^-1 n_b> 的可能取值
print("<n_a, M^-1 n_b> 取值:", wedge_cosines(), " ← 楔角 0/60/90/120/180°")
print("OK")
