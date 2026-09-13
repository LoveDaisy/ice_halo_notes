# 产出 ../img/two_mirrors_120.png：法线夹角 60° 的两面镜子先后反射 = 绕交线（c 轴）转 120°（正文第 50 行）。
# 六棱柱的**正俯视**（正交投影、沿 −c 看，画面 x/y = 晶体 x/y，角度不失真）+ 一条真实追迹的 3D 光路 1-3-4-2（`solve_raypath`）：
# 从顶面 1 进入、在相邻侧面 3、4 先后内反射、从底面 2 出射——首尾面 1 ∥ 2 折射抵消，底面折射不改变方向的方位角，
# 所以俯视图里入射方位 → 出射方位恰好转了 120°（两面镜法线夹 60°）。中心的弧箭头标出这 120°；另一条淡色虚线从出射点
# 画出"只转 60°"的方向作对比（显式 sketch，不是光路）。
# 为什么不用截面内的 2D 光路：在 xy 截面内进侧面 3 的光线（折射角 ≤ 49.8°）碰不到相邻面 4 / 8，且转 120° 后
# 不可能从平行面 6 出去（2026-09-13 探针：所有「侧面进 + 相邻两镜 + 平行侧面出」的 2D 序列 solve_raypath_2d 均无解），
# 只有带 z 分量的 3D 光路才走得通——这正是 ch3 笔记里 #4/#6 的典型光路都从底面进出的原因。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, RayPath, SegmentKind, annotate, draw_raypath,
                             draw_rotation_arc_3d, face_sequence, finish, frame, new_figure, render_crystal, rotation,
                             solve_raypath)
from halo_notes.draw.geometry import unit
from halo_notes.draw.scene import Z_EXTERNAL
from halo_notes.draw.style import LineStyle
from halo_notes.math import reflection_group as rg

OUT = Path(__file__).resolve().parent.parent / "img" / "two_mirrors_120.png"
WIDTH, HEIGHT, DPI = 2400, 2100, 200

FACES = [1, 3, 4, 2]
PATHS = {"1-3-4-2": FACES}
# 俯视里晶体内部段是主角（两次反射都在里面）：不填充顶面、内部段不减淡；锥体箭头缩小（正交俯视里 0.36 的锥体显得很大）
PRESET = PRESETS["default"].replace(
    style_map=PRESETS["default"].style_map.replace(ray_internal=LineStyle("accent_warm", linewidth=1.6, alpha=0.85)),
    geom=PRESETS["default"].geom.replace(cone_length=0.22, cone_radius=0.075))
CRYSTAL = HexPrism(a=1.0, h=2.0)   # 柱晶：h 大一些光路在侧面上的落点离棱远（最不擦边解的余量 0.2）
Z = np.array([0.0, 0.0, 1.0])
# 正俯视：视线沿 +z 指向观察者、画面"上"取 +y，正交投影
CAMERA = Camera(azimuth=0.0, elevation=90.0, up=(0.0, 1.0, 0.0), projection="orthographic")
ARC_RADIUS, SPOKE, ARC_OFFSET = 0.42, 0.62, (0.0, 0.0, 0.0)   # 120° 弧：以晶体中心为心
COMPARE_LENGTH = 1.3                 # "只转 60°" 对比线长度
LABEL_PAD = 0.62
XLIM_PAD = 0.12


def horizontal(d: np.ndarray) -> np.ndarray:
    return unit([d[0], d[1], 0.0])


def azimuth_deg(d: np.ndarray) -> float:
    return float(np.degrees(np.arctan2(d[1], d[0])))


PATH = solve_raypath(CRYSTAL, FACES, tail=1.0, head=1.0)   # 不给偏好：取各事件点离棱最远（最不擦边）的解
assert face_sequence(PATH) == FACES
D_IN, D_OUT = unit(PATH.points[1] - PATH.points[0]), unit(PATH.points[-1] - PATH.points[-2])
ROTATION_DEG = (azimuth_deg(D_OUT) - azimuth_deg(D_IN) + 180.0) % 360.0 - 180.0   # 俯视里的转角（有符号）
assert abs(abs(ROTATION_DEG) - 120.0) < 1e-9, ROTATION_DEG
# 两面镜法线夹 60°；矩阵连乘 == R_z(±120°)（权威表 #4 / #6）
assert abs(np.degrees(np.arccos(rg.NORMALS[3] @ rg.NORMALS[4])) - 60.0) < 1e-9
assert rg.identify(rg.path_matrix(FACES)).xy in ("r+", "r-")
# 对比线：只转 60°（同一出射点、水平分量转 60°、竖直分量同出射光），显式 sketch
EXIT_POINT = PATH.points[-2]
D_COMPARE = unit(rotation(Z, np.sign(ROTATION_DEG) * 60.0) @ horizontal(D_IN) * np.hypot(D_OUT[0], D_OUT[1])
                 + Z * D_OUT[2])
COMPARE = RayPath(np.array([EXIT_POINT, EXIT_POINT + D_COMPARE * COMPARE_LENGTH]), (SegmentKind.INTERNAL,), sketch=True)


def main() -> None:
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    render_crystal(ax, CRYSTAL, [PATH], camera=CAMERA, preset=PRESET)
    for k in range(3, 9):   # 侧面在俯视里是边：编号写在边中点内侧
        f = CRYSTAL.face(k)
        annotate(ax, str(k), CRYSTAL.centroid(f) - CRYSTAL.normal(f) * 0.24, camera=CAMERA, preset=PRESET,
                 ha="center", va="center", semantic="face_number")
    annotate(ax, "顶面 1 在上、底面 2 在下\n光线从 1 进、2 出（俯视重合）", (0.0, 0.0, 0.5), (-0.95, -0.55),
             camera=CAMERA, preset=PRESET, ha="center", va="center", semantic="annotation")
    # 120° 弧：起于入射水平方向、转到出射水平方向；两条辐条
    c = np.asarray(ARC_OFFSET, float)
    sp = PRESET.line_kwargs("symmetry_spoke")
    for d in (horizontal(D_IN), horizontal(D_OUT)):
        xy = CAMERA.project_xy(np.stack([c, c + d * SPOKE]))
        ax.plot(xy[:, 0], xy[:, 1], zorder=Z_EXTERNAL, solid_capstyle="round", **sp)
    draw_rotation_arc_3d(ax, Z, ARC_RADIUS, horizontal(D_IN), ROTATION_DEG, center=c, camera=CAMERA, preset=PRESET,
                         semantic="arc_azimuth", label=r"$120^\circ$", label_pad=0.3)
    draw_raypath(ax, COMPARE, camera=CAMERA, preset=PRESET, semantic="ray2d_discarded")
    annotate(ax, "只转 60°？\n（对比方向，不是光路）", COMPARE.end, (0.05, 0.1), camera=CAMERA, preset=PRESET,
             ha="left", va="bottom", semantic="annotation")
    annotate(ax, "入射（俯视投影）", PATH.points[0], (0.08, 0.0), camera=CAMERA, preset=PRESET, ha="left",
             va="center")
    annotate(ax, "出射（俯视投影）", PATH.points[-1], (0.0, -0.2), camera=CAMERA, preset=PRESET, ha="left", va="top")
    finish(ax, *frame(CAMERA, [CRYSTAL.vertices, PATH.points, COMPARE.points], WIDTH, HEIGHT, margin=XLIM_PAD))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
