# 产出 ../img/numerical_err.png：单精度下算 ((1+cos α)/2)^(N−2) 的两种方法相对 float64 真值的误差 vs N（对数轴 10⁴–10⁷，
# N = 10^(4:0.2:7) 共 16 点，α = 2/√N，照抄 code/legacy/numerical.m）：蓝圆 = 直接算幂（float32），红三角 = 渐近式
# exp(−α²(N−2)/4)（float32）。重制 5.4 旧图 img/legacy/numerical_err.png（1500×1125）。
# 读者要看出：直接算幂在 N 大时误差发散到 ±0.06 量级，而指数近似式始终贴 0（正文第 144 行）。
# 注意：float32 幂法误差的逐点数值取决于 cosf/powf 实现（numpy 与 MATLAB 在 N=10^6.8 处不同），但发散的结论不变。
from pathlib import Path

import numpy as np

from halo_notes.math.density import cos_power, exp_asymptotic
from halo_notes.math.tests.test_density import numerical_error_assertions
from matlab_style import DPI, LABEL_FS, MATLAB_BLUE, MATLAB_ORANGE, TICK_FS, TITLE_FS, matlab_figure

OUT = Path(__file__).resolve().parent.parent / "img" / "numerical_err.png"


def errors():
    """返回 (num, 幂法 float32 误差, 渐近式 float32 误差)，真值为 float64 幂法。"""
    num = 10.0 ** np.arange(4, 7.01, 0.2)
    alpha = 2 / np.sqrt(num)
    gt = cos_power(alpha, num)
    return num, cos_power(alpha, num, np.float32) - gt, exp_asymptotic(alpha, num, np.float32) - gt


def main() -> None:
    num, err_power, err_exp = errors()
    numerical_error_assertions(num, err_power, err_exp)

    fig, ax = matlab_figure()
    ax.set_xscale("log")
    ax.plot(num, err_power, "o", ms=8, mew=2, mfc="none", color=MATLAB_BLUE, clip_on=False,
            label=r"$\left(\frac{1}{2}(1+\cos\alpha)\right)^N$")
    ax.plot(num, err_exp, "^", ms=8, mew=2, mfc="none", color=MATLAB_ORANGE, clip_on=False,
            label=r"$\exp\left(-\frac{1}{4}\alpha^2 N\right)$")
    ax.plot(num, np.zeros_like(num), "k:", lw=1.2)
    ax.set_xlim(1e4, 1e7)
    ax.set_ylim(-0.08, 0.12)
    ax.set_yticks(np.arange(-0.08, 0.1201, 0.02))
    assert (err_power > -0.08).all() and (err_power < 0.12).all()   # 固定 y 范围不能把点裁掉
    # 图例放左上：numpy 的幂法在 N=10^6.8 处误差 0.10，右上图例会把这个点盖住（旧图 MATLAB 该点 ≈ 0，故放右上）
    ax.legend(fontsize=TICK_FS, loc="upper left", edgecolor="black", fancybox=False)
    ax.set_xlabel("Number of points", fontsize=LABEL_FS)
    ax.set_ylabel("Error", fontsize=LABEL_FS)
    ax.set_title("Numerical error of different methods", fontsize=TITLE_FS, fontweight="bold")
    fig.savefig(OUT, dpi=DPI, facecolor="white")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
