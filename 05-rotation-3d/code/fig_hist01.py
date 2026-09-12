# 产出 ../img/hist01.png：S² 上 10000 个均匀点（三维高斯归一化）最近邻角距离的直方图 vs 解析 pdf
# (N−1)/2·((1+cos α)/2)^(N−2)·sin α，两次独立重复（rep_num=2）合并；bin 范围 [0, 3·√(4/N)] 分 100 格。
# 逐行翻译 code/legacy/spherical_distance.m，重制 5.3 旧图 img/legacy/hist01.png（1500×1125）。
# 读者要看出：采样与解析吻合（正文第 125 行），峰位 ≈ 0.014 rad。随机种子固定为 SEED，重跑 byte-identical。
from pathlib import Path

import numpy as np

from halo_notes.math.density import l1_distance, s2_nearest_neighbor_pdf
from halo_notes.math.sampling import nearest_neighbor_angle, uniform_s2
from matlab_style import DPI, matlab_figure, plot_nn_histogram

OUT = Path(__file__).resolve().parent.parent / "img" / "hist01.png"
SEED = 20220503
PTS_NUM, REP_NUM = 10000, 2
L1_THRESHOLD = 0.15   # 与 halo_notes/math/tests/test_density.py 同阈值


def sample(rng: np.random.Generator) -> np.ndarray:
    """rep_num 次：撒 pts_num 个点，各自求最近邻角距离，合并。"""
    return np.concatenate([nearest_neighbor_angle(uniform_s2(PTS_NUM, rng)) for _ in range(REP_NUM)])


def main() -> None:
    dm = sample(np.random.default_rng(SEED))
    q_max = np.sqrt(4 / PTS_NUM) * 3
    edges = np.linspace(0, q_max, 101)
    centers = (edges[:-1] + edges[1:]) / 2
    pdf = s2_nearest_neighbor_pdf(centers, PTS_NUM)

    fig, ax = matlab_figure()
    density = plot_nn_histogram(ax, dm, edges, pdf, f"Uniformly distributed {PTS_NUM} points on S(2)")
    # 机械核验：直方图与 pdf 的 L1 距离；pdf 峰位 ≈ 0.014 rad
    l1 = l1_distance(density, pdf, edges[1] - edges[0])
    assert l1 < L1_THRESHOLD, l1
    assert abs(centers[np.argmax(pdf)] - 0.014) < 0.001
    fig.savefig(OUT, dpi=DPI, facecolor="white")
    print(f"saved {OUT}  (L1 = {l1:.4f})")


if __name__ == "__main__":
    main()
