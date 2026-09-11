# 核验 docs/framework.md 定理 1/2/3/5：六棱柱镜面生成群 |G|=12、共轭类 = ch3 发表的 6 类、
# 特征值只得 5 类（#11 并入 #2）、与 Rz 对易的元素、可能的楔角余弦。
# 冰晶标准坐标同 ch3：面 1/2 为 ±z 底面，面 3..8 为方位角 0°,60°,...,300° 的侧面。
import itertools
import numpy as np

s3 = np.sqrt(3) / 2


def Rz(deg):
    t = np.radians(deg)
    return np.array([[np.cos(t), -np.sin(t), 0], [np.sin(t), np.cos(t), 0], [0, 0, 1]])


def refl(n):
    n = np.asarray(n, float)
    n /= np.linalg.norm(n)
    return np.eye(3) - 2 * np.outer(n, n)


def sxy(phi):
    """xy 平面内、过原点且与 x 轴夹角 phi 的直线的反射（z 不变）。"""
    t = np.radians(phi)
    return np.array([[np.cos(2 * t), np.sin(2 * t), 0], [np.sin(2 * t), -np.cos(2 * t), 0], [0, 0, 1]])


def key(M):
    return tuple(np.round(M, 6).flatten())


normals = {1: [0, 0, 1], 2: [0, 0, -1]}
for k in range(6):
    a = np.radians(60 * k)
    normals[3 + k] = [np.cos(a), np.sin(a), 0]
mirrors = {k: refl(v) for k, v in normals.items()}

# 镜面生成群的闭包
G = [np.eye(3)]
seen = {key(np.eye(3))}
frontier = [np.eye(3)]
growth = [1]
while frontier:
    nxt = []
    for g in frontier:
        for m in mirrors.values():
            h = m @ g
            if key(h) not in seen:
                seen.add(key(h))
                G.append(h)
                nxt.append(h)
    frontier = nxt
    growth.append(len(seen))
print("|G| =", len(G), " 闭包按字长增长:", growth)

# ch3 工作笔记「平行光路矩阵归总」的 12 个矩阵，及发表表格的类型编号
b, r, r2 = np.diag([1, 1, -1.0]), Rz(120), Rz(-120)
user = {1: sxy(90) @ b, 2: sxy(90), 3: r2 @ b, 4: r2, 5: r @ b, 6: r,
        7: sxy(-30) @ b, 8: sxy(-30), 9: sxy(30) @ b, 10: sxy(30), 11: b, 12: np.eye(3)}
published = {1: 1, 7: 1, 9: 1, 2: 2, 8: 2, 10: 2, 3: 3, 5: 3, 4: 4, 6: 4, 11: 5, 12: 6}
assert all(key(M) in seen for M in user.values()), "笔记里的 12 个矩阵不全在 G 里"
assert len({key(M) for M in user.values()}) == 12 == len(G), "笔记的 12 个矩阵 ≠ G"

# G 下的共轭类 vs 发表的 6 类
def conj_class(M):
    return frozenset(key(g @ M @ g.T) for g in G)

classes = {}
for i, M in user.items():
    classes.setdefault(conj_class(M), []).append(i)
g_classes = sorted(classes.values())
p_classes = sorted([k for k, v in published.items() if v == t] for t in range(1, 7))
print("G-共轭类   :", g_classes)
print("发表的 6 类:", p_classes)
assert g_classes == p_classes, "G-共轭类与发表表格不一致"

# 特征值（O(3) 共轭）分类：太粗
ev = {}
for i, M in user.items():
    ev.setdefault(tuple(np.round(np.sort_complex(np.linalg.eigvals(M)), 6)), []).append(i)
print("特征值分类 :", sorted(ev.values()), " ← #11 并入 #2/8/10，只有", len(ev), "类")

# 与 Rz(θ) 对易 ⇔ 锐利（柱晶弧 / 片晶点）
commuting = [i for i, M in user.items() if np.allclose(M @ Rz(37), Rz(37) @ M)]
print("与 Rz 对易 :", commuting, " ← 发表类型", sorted({published[i] for i in commuting}))
assert sorted({published[i] for i in commuting}) == [3, 4, 5, 6]

# 楔角：<n_a, M^-1 n_b> 的可能取值
cosines = set()
for M in G:
    for a, bb in itertools.product(normals, normals):
        cosines.add(round(float(np.dot(normals[a], M.T @ np.asarray(normals[bb], float))), 6))
print("<n_a, M^-1 n_b> 取值:", sorted(cosines), " ← 楔角 0/60/90/120/180°")
print("OK")
