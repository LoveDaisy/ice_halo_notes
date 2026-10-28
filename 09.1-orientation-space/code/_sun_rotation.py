# 9.1 图 5a / ch10 图 2 的同源绕太阳动作；不含绘图与光路求解。
import numpy as np
from scipy.spatial.transform import Rotation


def solar_orbit(rotation, sun, angles_deg):
    """世界系左乘绕太阳的旋转，返回 (N,3,3) 姿态与固定的单位太阳方向。"""
    sun = np.asarray(sun, dtype=float)
    sun = sun / np.linalg.norm(sun)
    turns = Rotation.from_rotvec(np.radians(np.atleast_1d(angles_deg))[:, None] * sun).as_matrix()
    return turns @ np.asarray(rotation), sun


def body_sun(rotations, sun):
    return np.einsum('...ji,j->...i', rotations, sun)
