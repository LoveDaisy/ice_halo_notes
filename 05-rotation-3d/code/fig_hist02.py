# 产出 ../img/hist02.png：SO(3)「均匀」姿态——经纬度均匀于 S² + 转角均匀于 [0,2π)——转成单位四元数并拼上 −q（对径认同，
# 四元数样本 = 欧拉角样本 × 2，正文第 152 行），S³ 上最近邻角距离直方图 vs 解析 pdf；rep_num=2，bin 范围 [0, 2·(4/N)^0.33]。
# 逐行翻译 code/legacy/llr_quat_dist.m，重制 5.5 旧图 img/legacy/hist02.png（1500×1125）。
# 读者要看出：形态与 5.3 相似但峰位不同（≈ 0.055 rad，正文第 156 行）。随机种子固定为 SEED，重跑 byte-identical。
from pathlib import Path

import numpy as np

from halo_notes.math.density import l1_distance, s3_nearest_neighbor_pdf
from halo_notes.math.sampling import llr_to_quat, nearest_neighbor_angle, uniform_so3_llr
from matlab_style import DPI, matlab_figure, plot_nn_histogram

OUT = Path(__file__).resolve().parent.parent / "img" / "hist02.png"
SEED = 20220505
PTS_NUM, REP_NUM = 10000, 2
L1_THRESHOLD = 0.15   # 与 halo_notes/math/tests/test_density.py 同阈值


def sample(rng: np.random.Generator) -> np.ndarray:
    """rep_num 次：pts_num 组欧拉角 → 四元数 → 拼 −q → 2·pts_num 个点的最近邻角距离，合并。"""
    out = []
    for _ in range(REP_NUM):
        q = llr_to_quat(uniform_so3_llr(PTS_NUM, rng))
        out.append(nearest_neighbor_angle(np.vstack([q, -q])))
    return np.concatenate(out)


def main() -> None:
    dm = sample(np.random.default_rng(SEED))
    q_max = (4 / PTS_NUM) ** 0.33 * 2
    edges = np.linspace(0, q_max, 101)
    centers = (edges[:-1] + edges[1:]) / 2
    pdf = s3_nearest_neighbor_pdf(centers, 2 * PTS_NUM)

    fig, ax = matlab_figure()
    density = plot_nn_histogram(ax, dm, edges, pdf, f"Uniformly distributed {PTS_NUM}*2 points on S(3)")
    l1 = l1_distance(density, pdf, edges[1] - edges[0])
    assert l1 < L1_THRESHOLD, l1
    assert abs(centers[np.argmax(pdf)] - 0.055) < 0.003
    fig.savefig(OUT, dpi=DPI, facecolor="white")
    print(f"saved {OUT}  (L1 = {l1:.4f})")


if __name__ == "__main__":
    main()
