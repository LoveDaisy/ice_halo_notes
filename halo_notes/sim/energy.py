"""Lumice 渲染图的像素能量 / 辐亮度口径（全仓唯一实现，ch7 / ch8 / ch9 的取数都经这里）。

Lumice 渲染出的像素值已是「辐亮度在该像素立体角上的积分」（Lumice ``src/core/lens_proj_build.hpp:157``：
"A rendered pixel holds a radiance INTEGRATED over its own solid angle"）。所以：

- 像素**能量** = 线性亮度 L 本身（:func:`pixel_energy`）——求能量占比 / 质心 / 剖面**不要再乘** cos(lat)；
- ``rectangular`` 全天图的像素立体角 ∝ cos(lat)（:func:`~.projection.rectangular_pixel_directions` 返回的 ``weight``），
  像素**辐亮度** = L / cos(lat)（:func:`pixel_radiance`）；一片区域的平均辐亮度 = ΣL / Σcos(lat)。
"""
from __future__ import annotations

import numpy as np


def linear_luminance(image: np.ndarray) -> np.ndarray:
    """8-bit sRGB → 线性亮度（三通道之和）；2D（灰度）输入逐像素解码、原样返回。"""
    a = np.asarray(image, float) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return lin.sum(axis=-1) if lin.ndim == 3 else lin


def pixel_energy(image: np.ndarray) -> np.ndarray:
    """Lumice 渲染图每像素的能量 = :func:`linear_luminance` 本身（像素值已含立体角，见模块 docstring）。
    与 :func:`linear_luminance` 同值，单列一个名字是为了在取数处写明语义「这是能量」。"""
    return linear_luminance(image)


def pixel_radiance(energy: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """``rectangular`` 图每像素辐亮度 = 像素能量 / 立体角权重 ``weight``（= cos(lat)，取自
    :func:`~.projection.rectangular_pixel_directions`）。只做朴素相除，不平滑；极点附近 cos → 0 的噪声放大由调用方处理。"""
    return np.asarray(energy, float) / np.asarray(weight, float)
