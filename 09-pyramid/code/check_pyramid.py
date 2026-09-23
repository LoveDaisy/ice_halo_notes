# 核验 docs/framework.md 定理 6/7：锥晶镜面群无限（闭包随字长爆炸），
# 可透射楔角恰为 0/28/52.4/56/60/62/63.8/80.2/90，对应 odd-radius 晕家族。
import argparse
import itertools
import math
import numpy as np

CA = 1.6288          # ice c/a
N_ICE = 1.31
THETA = math.degrees(math.atan((2 / math.sqrt(3)) * CA))   # {10-11} 锥面法向与 c 轴夹角
A_MAX = 2 * math.degrees(math.asin(1 / N_ICE))   # 可透射楔角上限
KNOWN_PYRAMID_GROWTH_6 = [1, 11, 70, 372, 1884, 9444, 47244]


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


def mirror_group_growth(pyramid: bool, max_len: int) -> list[int]:
    """镜面反射矩阵闭包按字长 0..max_len 的累计元素数（字长 k = 至多 k 个镜面反射的乘积）。"""
    mirrors = [refl(n) for n in face_normals(pyramid)]
    seen = {key(np.eye(3))}
    layer = [np.eye(3)]
    growth = [1]
    for _ in range(1, max_len + 1):
        nxt = []
        for g in layer:
            for m in mirrors:
                h = m @ g
                if key(h) not in seen:
                    seen.add(key(h))
                    nxt.append(h)
        layer = nxt
        growth.append(len(seen))
    return growth


def wedge_angles(pyramid: bool) -> list[float]:
    """全部面对（含同一面自配）的楔角 arccos(−n_a·n_b)，0.1° 取整去重、升序。"""
    N = face_normals(pyramid)
    wedge = set()
    for a, b in itertools.product(N, N):
        c = -float(np.dot(a, b))
        if abs(c) <= 1:
            wedge.add(round(math.degrees(math.acos(c)), 1))
    return sorted(wedge)


def transmittable_wedges(pyramid: bool) -> list[float]:
    """可透射楔角（< A_MAX）。"""
    return [x for x in wedge_angles(pyramid) if x < A_MAX - 1e-9]


def main() -> None:
    print(f"锥面法向与 c 轴夹角: {THETA:.3f}°")
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-len", type=int, default=6)
    args = parser.parse_args()
    MAX_LEN = args.max_len
    for pyramid in (False, True):
        N = face_normals(pyramid)
        growth = mirror_group_growth(pyramid, MAX_LEN)
        wedge = wedge_angles(pyramid)
        ok = transmittable_wedges(pyramid)
        print(f"{'锥晶' if pyramid else '柱晶'} 面数={len(N):2d}  闭包按字长 0..{MAX_LEN}: {growth}")
        print(f"      楔角: {wedge}")
        print(f"      可透射(<{A_MAX:.1f}°): {ok}")
        if pyramid:
            assert ok == [0.0, 28.0, 52.4, 56.0, 60.0, 62.0, 63.8, 80.2, 90.0]
            if MAX_LEN == 6:
                assert growth == KNOWN_PYRAMID_GROWTH_6
            else:
                assert all(growth[i] > growth[i - 1] for i in range(1, len(growth))), "锥晶闭包应持续增长"
        else:
            assert ok == [0.0, 60.0, 90.0] and growth[3:] == [12] * len(growth[3:])
    print("OK")


if __name__ == "__main__":
    main()
