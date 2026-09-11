# 核验 docs/framework.md 定理 6/7：锥晶镜面群无限（闭包随字长爆炸），
# 可透射楔角恰为 0/28/52.4/56/60/62/63.8/80.2/90，对应 odd-radius 晕家族。
import itertools
import math
import numpy as np

CA = 1.6288          # ice c/a
N_ICE = 1.31
THETA = math.degrees(math.atan((2 / math.sqrt(3)) * CA))   # {10-11} 锥面法向与 c 轴夹角
print(f"锥面法向与 c 轴夹角: {THETA:.3f}°")


def refl(n):
    n = np.asarray(n, float)
    n /= np.linalg.norm(n)
    return np.eye(3) - 2 * np.outer(n, n)


def key(M):
    return tuple(np.round(M, 5).flatten())


def face_normals(pyramid):
    N = [[0, 0, 1], [0, 0, -1]]
    for k in range(6):
        a = math.radians(60 * k)
        N.append([math.cos(a), math.sin(a), 0])
    if pyramid:
        t = math.radians(THETA)
        for k in range(6):
            a = math.radians(60 * k)
            for sgn in (+1, -1):
                N.append([math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), sgn * math.cos(t)])
    return [np.asarray(v, float) / np.linalg.norm(v) for v in N]


A_MAX = 2 * math.degrees(math.asin(1 / N_ICE))   # 可透射楔角上限
for pyramid in (False, True):
    N = face_normals(pyramid)
    mirrors = [refl(n) for n in N]
    seen = {key(np.eye(3))}
    layer = [np.eye(3)]
    growth = [1]
    for _ in range(1, 7):
        nxt = []
        for g in layer:
            for m in mirrors:
                h = m @ g
                if key(h) not in seen:
                    seen.add(key(h))
                    nxt.append(h)
        layer = nxt
        growth.append(len(seen))
    wedge = set()
    for a, b in itertools.product(N, N):
        c = -float(np.dot(a, b))
        if abs(c) <= 1:
            wedge.add(round(math.degrees(math.acos(c)), 1))
    ok = sorted(x for x in wedge if x < A_MAX - 1e-9)
    print(f"{'锥晶' if pyramid else '柱晶'} 面数={len(N):2d}  闭包按字长 0..6: {growth}")
    print(f"      楔角: {sorted(wedge)}")
    print(f"      可透射(<{A_MAX:.1f}°): {ok}")
    if pyramid:
        assert ok == [0.0, 28.0, 52.4, 56.0, 60.0, 62.0, 63.8, 80.2, 90.0]
        assert growth[-1] > growth[-2] > growth[-3], "锥晶闭包应持续增长"
    else:
        assert ok == [0.0, 60.0, 90.0] and growth[3:] == [12] * len(growth[3:])
print("OK")
