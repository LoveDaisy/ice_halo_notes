"""最近邻角距离的解析 pdf（S²、S³）与 ((1+cos α)/2)^N 的两种数值算法（ch5 图 5.3 / 5.4 / 5.5）。

S³ 公式的两种写法是同一个函数：`llr_quat_dist.m` 第 33 行以欧拉角样本数 M 写成
``2(2M−1)/π · (1 − α/π + cos α sin α/π)^(2M−2) · sin²α``，正文第 164 行以四元数样本数 N 写成
``2(N−1)/π · sin²α · (1 − α/π + sin 2α/(2π))^(N−2)``；代入 N = 2M（对径认同，四元数样本是欧拉角样本的两倍，
正文第 152 行）并用 cos α sin α = sin 2α / 2，两式逐项相等。本模块统一用 N（球面上的点数）作参数。
"""

from __future__ import annotations

import numpy as np


def s2_nearest_neighbor_pdf(alpha, n: int):
    """S² 上 n 个均匀点，最近邻角距离的 pdf：(n−1)/2 · ((1+cos α)/2)^(n−2) · sin α（正文第 118 行）。"""
    a = np.asarray(alpha, float)
    return (n - 1) / 2 * ((1 + np.cos(a)) / 2) ** (n - 2) * np.sin(a)


def s3_nearest_neighbor_pdf(alpha, n: int):
    """S³ 上 n 个均匀点（n = 四元数样本数）最近邻角距离的 pdf，写法照抄 `llr_quat_dist.m` 第 33 行
    （2M−1 → n−1、2M−2 → n−2）：2(n−1)/π · (1 − α/π + cos α sin α/π)^(n−2) · sin²α。"""
    a = np.asarray(alpha, float)
    return 2 * (n - 1) / np.pi * (1 - a / np.pi + np.cos(a) * np.sin(a) / np.pi) ** (n - 2) * np.sin(a) ** 2


def s3_nearest_neighbor_pdf_text_form(alpha, n: int):
    """同 :func:`s3_nearest_neighbor_pdf`，按正文第 164 行的记号写（sin 2α / 2π）；单测用来核两式相等。"""
    a = np.asarray(alpha, float)
    return 2 * (n - 1) / np.pi * np.sin(a) ** 2 * (1 - a / np.pi + np.sin(2 * a) / (2 * np.pi)) ** (n - 2)


def cos_power(alpha, n, dtype=np.float64):
    """((1+cos α)/2)^(n−2)，全程在 ``dtype`` 下计算（`numerical.m` 第 6–7 行：float64 为真值，float32 为对照）。"""
    a = np.asarray(alpha, dtype)
    e = np.asarray(np.asarray(n, float) - 2, dtype)
    return np.power(((1 + np.cos(a)) / 2).astype(dtype), e).astype(dtype)


def exp_asymptotic(alpha, n, dtype=np.float64):
    """渐近式 exp(−α²(n−2)/4)（正文第 140 行；`numerical.m` 第 8 行），全程在 ``dtype`` 下计算。"""
    a = np.asarray(alpha, dtype)
    e = np.asarray(np.asarray(n, float) - 2, dtype)
    return np.exp((-a ** 2 / 4 * e).astype(dtype)).astype(dtype)


def l1_distance(hist_density, pdf_at_centers, bin_width: float) -> float:
    """直方图（pdf 归一化）与解析 pdf 在 bin 中心处的 L1 距离 Σ|h−p|·Δ，两者都归一时取值在 [0, 2]。"""
    return float(np.sum(np.abs(np.asarray(hist_density) - np.asarray(pdf_at_centers))) * bin_width)


__all__ = ["cos_power", "exp_asymptotic", "l1_distance", "s2_nearest_neighbor_pdf", "s3_nearest_neighbor_pdf",
           "s3_nearest_neighbor_pdf_text_form"]
