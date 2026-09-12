# 光路 1-3-2 的"光走廊"场景（2.5 / 2.7 / 2.8 / 2.9 共用）：同一个片晶、同一视角、同一套幽灵晶体与高亮面，
# 各图只是在走廊里画不同的直线。不是画图脚本本身，被 fig_light_corridor_rp132_*.py 引用。
from pathlib import Path

import numpy as np

from halo_notes.draw import (PRESETS, Camera, Corridor, HexPrism, RayPath, SegmentKind, finish, new_figure,
                             render_corridor, solve_raypath)
from halo_notes.draw.raypath import EventKind, RayEvent

IMG = Path(__file__).resolve().parent.parent / "img"
WIDTH, HEIGHT, DPI = 2400, 1350, 200  # = 旧图分辨率
CAMERA = Camera(azimuth=-60, elevation=28)  # 反射面 3 在右后，幽灵晶体展开到右后方（旧图视角）
PRESET = PRESETS["default"]
CRYSTAL = HexPrism(1.0, 0.8).transformed(translation=CAMERA.to_world(-0.7, 0.1, 0))  # 晶体 + 幽灵整体居中
XLIM, YLIM = (-4.2, 4.2), (-2.36, 2.36)
FACES = [1, 3, 2]  # 走廊的面序列：顶面 1 进、侧面 3 反射、底面 2 出


def direction(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    a, e = np.deg2rad(azimuth_deg), np.deg2rad(elevation_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def solve_132(d: np.ndarray, offset=(0.0, 0.0, 0.0)) -> RayPath:
    """走 1-3-2 的真实光路，偏好沿 ``d`` 打向顶面 1 上质心 + ``offset`` 处（可行时原样采用）。"""
    geom = PRESET.geom
    return solve_raypath(CRYSTAL, FACES, prefer_direction=d,
                         prefer_point=CRYSTAL.centroid(CRYSTAL.face(1)) + np.asarray(offset, float),
                         tail=geom.incident_tail, head=geom.exit_head)


# 走廊本身由这条参考光路定义（与 2.4 同一条），三张图的幽灵晶体 / 高亮面都一样
REFERENCE = solve_132(direction(-40, -25), offset=(0.5, 0.3, 0))
CORRIDOR = Corridor(CRYSTAL, REFERENCE)   # 构造时已断言展开直线穿过 1 / 3 / 幽灵 2 三个面的内部


def centroid_line(chain) -> RayPath:
    """连接走廊三个面（面 1、面 3、幽灵的面 2）质心的折线——2.7 里"仅靠对称性就知道共线"的那条。
    这是几何候选线，不是光线（在面 1 没有折射折点），所以 ``sketch=True``；事件只用来在三个
    质心处打点。"""
    crystal, ghost = chain
    pts = [crystal.centroid(crystal.face(1)), crystal.centroid(crystal.face(3)),
           ghost.centroid(ghost.face(2))]
    events = (RayEvent(0, 1, EventKind.REFRACT_IN), RayEvent(1, 3, EventKind.PASS_THROUGH),
              RayEvent(2, 2, EventKind.REFRACT_OUT))
    return RayPath(np.array(pts), (SegmentKind.INTERNAL, SegmentKind.INTERNAL), events, sketch=True)


def new_corridor_figure():
    """建图并画好走廊（晶体 + 幽灵都是线框、三个走廊面高亮），返回 ``(fig, ax, chain)``。"""
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    chain = render_corridor(ax, CRYSTAL, REFERENCE, camera=CAMERA, preset=PRESET)
    return fig, ax, chain


def save(fig, name: str) -> None:
    out = IMG / name
    finish(fig.axes[0], XLIM, YLIM)
    fig.savefig(out, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {out}")
