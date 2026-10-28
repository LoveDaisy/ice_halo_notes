"""候选图 2a：参数环面必须对应真实柱晶姿态，不能以漂亮形状代替族约束。"""
import numpy as np

import fig_column_torus as F


def test_periods_and_column_constraint():
    for psi in (0, 37, 183, 359):
        for theta in (0, 62, 180, 311):
            r = F.attitude(psi, theta)
            assert abs(r[2, 2]) < 1e-12
            np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)
            for p, t in ((psi + 360, theta), (psi, theta + 360)):
                np.testing.assert_allclose(F.attitude(p, t), r, atol=1e-12)
                np.testing.assert_allclose(F.torus(p, t), F.torus(psi, theta), atol=1e-12)
            # 各自走半圈不是同一个带面号姿态，排除把周期自由度压成单向线段。
            assert np.linalg.norm(r - F.attitude(psi + 180, theta)) > 1
            assert np.linalg.norm(r - F.attitude(psi, theta + 180)) > 1


def test_parry_circle_locks_upward_side_face():
    for psi in np.linspace(0, 360, 73):
        r = F.attitude(psi, F.PARRY_THETA)
        np.testing.assert_allclose(r[:, 0], [0, 0, 1], atol=1e-12)
        assert abs(r[2, 2]) < 1e-12
        assert abs(F.torus(psi, F.PARRY_THETA)[2] - F.MINOR) < 1e-12
        assert np.linalg.norm(F.attitude(psi, F.PARRY_THETA + 30)[:, 0] - [0, 0, 1]) > 0.1


def test_visible_surface_is_on_torus_and_faces_camera():
    image, xyz = F.surface_pixels(width=201)
    assert np.isfinite(image).all() and image.min() >= 0 and image.max() <= 1
    assert len(xyz) > 1000
    # 代数环面方程是一条不同于射线步进距离函数的几何核验链。
    x, y, z = xyz.T
    residual = (x*x + y*y + z*z + F.MAJOR**2 - F.MINOR**2)**2 - 4 * F.MAJOR**2 * (x*x + y*y)
    assert np.max(np.abs(residual)) < 0.002
    radial = np.hypot(x, y)
    normals = np.column_stack([x * (1 - F.MAJOR / radial),
                               y * (1 - F.MAJOR / radial), z]) / F.MINOR
    assert (normals @ F.EYE).min() > -1e-6
    # 每个命中点前移一小段应在外部，防止误取背面表面。
    assert F.signed_distance(xyz + 0.002 * F.EYE).min() > 0
