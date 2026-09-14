# 核验 docs/framework.md 定理 5′（类数上界）：六棱柱 signature (M, n_a, M^-1 n_b) 在晶体点群
# D6h（24 元，ch7 的 D3h=G 之外再乘绕 z 轴的 60° 旋转）下商掉后，按楔角 A=arccos(-<n_a, M^-1 n_b>)
# 分组计数；再用采样指纹核对每个 signature 类对应的方向映射 Φ 在 D6h 共轭下是否进一步合并。
# 计算本体只用 halo_notes.math.reflection_group 的 12 矩阵权威表（GROUP/NORMALS/key/identify）与
# numpy；D6h 的另外 12 个元素（Rz(60k) 与竖直镜 sxy(30k)，及各自乘底面镜 B）现场拼出，不改库。
#
# Φ 的定义域是判据的一部分：入射须从外侧进入面 a（<d, n_a> < 0），出射须无 TIR 且从外侧离开面 b
# （<d', n_b> > 0）——定义域外的方向不算入指纹。漏这一条会把 60° 的 12 个 signature 类错误合并成 6
# 个（因为忽略入射侧时，一条光路与其时间反演在指纹上无法区分），这是本脚本存在的意义之一。
import itertools
import math

import numpy as np

from halo_notes.math import reflection_group as rg

N_ICE = 1.31
A_MAX_DEG = 2 * math.degrees(math.asin(1 / N_ICE))  # ≈ 99.5°，超过则楔角全反射（TIR 死角）

# ---- D6h：ch7 的 D3h（G）不足以商 signature——法向方位角本身以 60° 为周期，还差绕 z 轴的旋转
# 与竖直镜；D6h = <Rz(60k), sxy(30k)> ∪ B·(前者)，共 24 元。
Gc = []
for k in range(6):
    Gc.append(rg.Rz(60 * k))
    Gc.append(rg.sxy(30 * k))
Gc = Gc + [rg.B @ g for g in Gc]
assert len({rg.key(g) for g in Gc}) == 24, "D6h 应有 24 个元素"


def face_of(v: np.ndarray) -> int:
    for f, n in rg.NORMALS.items():
        if np.allclose(n, v):
            return f
    raise ValueError(v)


def canon_signature(M: np.ndarray, a: int, b: int) -> tuple:
    """(M, n_a, n_b) 在 D6h 下的规范代表：对每个 g 取 (g M g^T, g·a, g·b) 的字典序最小者。"""
    best = None
    for g in Gc:
        Mg = g @ M @ g.T
        t = (rg.key(Mg), face_of(g @ rg.NORMALS[a]), face_of(g @ rg.NORMALS[b]))
        if best is None or t < best:
            best = t
    return best


# ---- 第一步：signature 类数按楔角分组 --------------------------------------------

classes: dict[float, set[tuple]] = {}
for M in rg.GROUP:
    for a, b in itertools.product(rg.NORMALS, rg.NORMALS):
        nb_tilde = M.T @ rg.NORMALS[b]  # = M^-1 n_b（M 正交）
        cos_a = -float(rg.NORMALS[a] @ nb_tilde)
        angle = round(math.degrees(math.acos(max(-1.0, min(1.0, cos_a)))), 1)
        classes.setdefault(angle, set()).add(canon_signature(M, a, b))

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


def snell(d: np.ndarray, n: np.ndarray, n1: float, n2: float) -> np.ndarray | None:
    """d 为单位入射方向，n 为界面外法向。返回折射方向；入射角超临界角（TIR）或从背面入射返回 None。"""
    c = -float(n @ d)  # 从外侧入射要求 d 与 -n 同向，即 c > 0
    if c <= 0:
        return None
    r = n1 / n2
    k = 1 - r * r * (1 - c * c)
    if k < 0:
        return None
    return r * d + (r * c - math.sqrt(k)) * n


def phi(M: np.ndarray, a: int, b: int, d: np.ndarray) -> np.ndarray | None:
    """Φ_P(d) = S_{n_b} ∘ M ∘ S_{n_a}，定义域显式：入射须从外侧进面 a，出射须无 TIR 且从外侧离开面 b。"""
    na, nb = rg.NORMALS[a], rg.NORMALS[b]
    d1 = snell(d, na, 1.0, N_ICE)
    if d1 is None:
        return None
    d2 = M @ d1
    d3 = snell(d2, -nb, N_ICE, 1.0)  # 从内侧出射：法向取指向内部的 -n_b
    if d3 is None or float(d3 @ nb) <= 0:
        return None
    return d3


_rng = np.random.default_rng(0)  # 固定种子，保证指纹可复现
_SAMPLE = _rng.normal(size=(600, 3))
_SAMPLE /= np.linalg.norm(_SAMPLE, axis=1, keepdims=True)


def canon_phi(M: np.ndarray, a: int, b: int) -> tuple:
    """把 Φ 在 D6h 共轭下（Φ_g(d) = g·Φ(g^-1 d)）规范化：字典序最小的采样指纹。"""
    best = None
    for g in Gc:
        pts = []
        for d in _SAMPLE:
            o = phi(M, a, b, g.T @ d)
            pts.append((9.0, 9.0, 9.0) if o is None else tuple(np.round(g @ o, 3)))
        t = tuple(pts)
        if best is None or t < best:
            best = t
    return best


print("\nΦ 类数（在 D6h 共轭下核对 signature 类是否再合并）：")
phi_total = 0
phi_counts = {}
for angle in (60.0, 90.0):
    reps = sorted(classes[angle])
    fps: dict[tuple, list] = {}
    for k, a, b in reps:
        M = np.array(k).reshape(3, 3)
        fps.setdefault(canon_phi(M, a, b), []).append((rg.identify(M).number, a, b))
    phi_counts[angle] = len(fps)
    print(f"  楔角 {angle:5.1f}°: signature 类 {len(reps):3d} → Φ 类 {len(fps):3d}")
    phi_total += len(fps)

# 0°（平行光路）：W = I，Φ = M，Φ 类数就是 ch7 的 6 个共轭类——signature 按 M 编号分组即可核对，
# 不需要过一遍 canon_phi（省去对 14 个 signature 各做 24×600 次 snell 求值）。
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
