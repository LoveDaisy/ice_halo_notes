# 核验 docs/framework.md 定理 5′（类数上界）：六棱柱 signature (M, n_a, M^-1 n_b) 在晶体点群
# D6h（24 元，ch7 的 D3h=G 之外再乘绕 z 轴的 60° 旋转）下商掉后，按楔角 A=arccos(-<n_a, M^-1 n_b>)
# 分组计数；再用采样指纹核对每个 signature 类对应的方向映射 Φ 在 D6h 共轭下是否进一步合并。
# 算法本体（D6h 构造、规范型、Φ 与带定义域的采样指纹）在 lumice_integral.symmetry.signature，本脚本只是薄封装：
# 遍历 M ∈ G（lumice_integral.symmetry.reflection_group 的 12 矩阵权威表）× 全部面对，面法向从 HexPrism 实例取。
#
# Φ 的定义域是判据的一部分：入射须从外侧进入面 a（<d, n_a> < 0），出射须无 TIR 且从外侧离开面 b
# （<d', n_b> > 0）——定义域外的方向不算入指纹。漏这一条会把 60° 的 12 个 signature 类错误合并成 6
# 个（因为忽略入射侧时，一条光路与其时间反演在指纹上无法区分），这是本脚本存在的意义之一。
import itertools

import numpy as np

from lumice_integral.geometry import HexPrism
from lumice_integral.symmetry import reflection_group as rg
from lumice_integral.symmetry.signature import A_MAX_DEG, D6H, canonical_signature, phi_fingerprint, wedge_angle

assert len({rg.key(g) for g in D6H}) == 24, "D6h 应有 24 个元素"

crystal = HexPrism()                                  # 面法向只从它取；楔角与 signature 与高径比无关
FACES = [f.number for f in crystal.faces]

# ---- 第一步：signature 类数按楔角分组 --------------------------------------------

classes: dict[float, set[tuple]] = {}
for M in rg.GROUP:
    for a, b in itertools.product(FACES, FACES):
        angle = round(wedge_angle(crystal, M, a, b), 1)
        classes.setdefault(angle, set()).add(canonical_signature(crystal, M, a, b))

print("signature 类数按楔角分组：")
transmittable_total = 0
for angle in sorted(classes):
    ok = angle < A_MAX_DEG
    print(f"  楔角 {angle:6.1f}°  signature 类数 {len(classes[angle]):3d}  {'可透射' if ok else 'TIR 死角'}")
    if ok:
        transmittable_total += len(classes[angle])

assert sorted(classes) == [0.0, 60.0, 90.0, 120.0, 180.0], "楔角取值应恰为 {0,60,90,120,180}°"
assert {a: len(classes[a]) for a in classes} == {0.0: 14, 60.0: 12, 90.0: 16, 120.0: 12, 180.0: 14}
print("可透射合计:", transmittable_total)
assert transmittable_total == 42

# ---- 第二步：signature 类 → 方向映射 Φ 类（D6h 共轭下）是否再合并 -------------------

print("\nΦ 类数（在 D6h 共轭下核对 signature 类是否再合并）：")
phi_total = 0
phi_counts = {}
for angle in (60.0, 90.0):
    reps = sorted(classes[angle])
    fps: dict[tuple, list] = {}
    for k, a, b in reps:
        M = np.array(k).reshape(3, 3)
        fps.setdefault(phi_fingerprint(crystal, M, a, b), []).append((rg.identify(M).number, a, b))
    phi_counts[angle] = len(fps)
    print(f"  楔角 {angle:5.1f}°: signature 类 {len(reps):3d} → Φ 类 {len(fps):3d}")
    phi_total += len(fps)

# 0°（平行光路）：W = I，Φ = M，Φ 类数就是 ch7 的 6 个共轭类——signature 按 M 编号分组即可核对，
# 不需要过一遍 phi_fingerprint（省去对 14 个 signature 各做 24×600 次 snell 求值）。
by_M: dict[int, int] = {}
for k, a, b in classes[0.0]:
    M = np.array(k).reshape(3, 3)
    by_M[rg.identify(M).number] = by_M.get(rg.identify(M).number, 0) + 1
print(f"  楔角   0.0°: signature 类 {len(classes[0.0]):3d} → Φ 类 {len(by_M):3d}  ← ch7 的 6 个共轭类")
phi_counts[0.0] = len(by_M)
phi_total += len(by_M)

assert phi_counts == {0.0: 6, 60.0: 12, 90.0: 16}
print("Φ 类数合计:", phi_total)
assert phi_total == 34

print("OK")
