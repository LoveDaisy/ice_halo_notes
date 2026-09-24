# 7.5 静态图 / 单行图 / gif 共用：柱晶姿态平面 (ψ, θ) → 晶体 + 真实追迹光路 → 天空（Lumice 渲染底图），三栏布局与全部数据。
# fig_pose_to_sky.py 与 fig_pose_to_sky_gif.py 各自 import 本模块，不各写一份几何（同 ch3 的 _tricker_arc.py 模式）。
#
# 右栏（R1-1 / R2-3，2026-09-13 作者裁定）：底图 = sim_pose_to_sky_backdrop.py 出的 Lumice `globe` 球面外视渲染（与图 6 同一份
# 仿真：同 population、同「矩阵类全部光路」复合过滤器，只换 render 段；帧中心按 backdrop_center 机械取该行参考点（上行反日点 /
# 下行太阳）与三个样本天空点质心的角平分方向，带 30° 经纬网格），叠加层用 `halo_notes.sim.projection.project`（按镜头分派）
# 把天空方向投到同一像素坐标：样本点（三色）、上行淡画的公式特里克尔弧、参考点标记；下行的弥散区就是渲染本身，不再画点云。
# 对齐核验（公式弧叠在渲染弧上、网格线叠合 < 2 px）见 test_figures 7.5；钉不住则回退等积鱼眼底图（R2-3）。
#
# 中栏相机（R2-2）：`search_camera` 在相机方向球面网格（5° 粗扫 + 1° 细扫）上，对 D = {入射} ∪ {该行三条出射}（br 行三条重合，
# 退化为两方向）最大化「两两方向所张平面对相机的正对度」的最小值（正对度 = 投影夹角的正弦 × 两段投影长度 / sin 真实夹角，
# 见 face_on——字面的「投影夹角」在视线接近角平分线时退化到 180° 的短桩，故不用），硬约束三条出射光的画面水平分量 > 0
#（出射朝右，中→右引线不再穿过面板），可行域先限定在 R1-2 的「入射 / 出射投影夹角 ≥ 0.9 × 真实夹角」内（两条要求同时成立）；
# 上下两行各自搜索。搜索结果记录在 CAMERA_SEARCH_RECORD（脚本导入时与实时搜索核对）。
#
# 几何事实（2026-09-13 探针 scan3e：h/a=3、Σ=10°、入射方向 = −太阳方向、每格 1°、入射面 25×25 网格采样，见 `--probe`）：
# - #3 $br$ 的代表光路 1-2-3-5-1 只在很窄的姿态里可行（ψ=45° 时无解；ψ=35° 时 θ∈[34°, 65°] 连续可行、ψ=30° 时 [28°, 54°]、
#   ψ=40° 时 [42°, 57°]）；同矩阵的另一条代表 3-1-5-7-4 在扫过的 ψ 里都无解。h/a=2 时窗口只有 ~12°，h/a=1 无解——
#   所以本图取 h/a=3。这正是正文第 3 节「上界 vs 下界」：群论给出 12 种矩阵，能不能走通是几何的事。
# - #2 $s$ 的代表光路 1-3-2 宽松得多：ψ=35° 时 θ∈[10°, 136°]，ψ=30° 时 [2°, 140°]。
# 于是 ψ0=35°、三个样本 θ = 39° / 49° / 59°（落在两条光路的公共可行区间内、相隔 10°）；gif 只扫 ψ0=35° 一段（R1-3：
# 可行区间只允许 ψ 差 5°，「换 ψ 才动」演不出来）：#3 扫 [34°, 60°]（可行到 65°，截到 θ 轴的一个周期 60° 之内）、
# #2 扫 [10°, 60°]（可行到 136°，同样截到一个周期）。
from __future__ import annotations

import functools
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, annotate_2d, draw_connector, finish, frame, render_crystal,
                             search_raypath, solve_camera_distance)
from halo_notes.draw.geometry import unit
from halo_notes.draw.projection import visible_faces
from halo_notes.draw.raypath import face_grid_points, face_sequence
from halo_notes.draw.scene2d import Z_TEXT
from halo_notes.draw.style import LineStyle, MarkerStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from lumice_integral.symmetry import reflection_group as rg
from lumice_integral.camera import sun_direction
from lumice_integral.symmetry.attitude import column_attitude, sky_direction
from halo_notes.sim.projection import frame_center, globe_view_for, project

CODE_DIR = Path(__file__).resolve().parent
IMG = CODE_DIR.parent / "img"
DATA = CODE_DIR.parent / "data"


def _load_tricker_arc():
    """ch3 的 _tricker_arc.py（特里克尔弧参数方程 / 反日点 / Σ）：按路径加载，不复制公式。"""
    path = CODE_DIR.parents[1] / "03-parallel-raypaths" / "code" / "_tricker_arc.py"
    spec = importlib.util.spec_from_file_location("_tricker_arc", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_tricker_arc", mod)
    spec.loader.exec_module(mod)
    return mod


TRICKER = _load_tricker_arc()
SUN_ELEVATION_DEG = TRICKER.SUN_ELEVATION_DEG          # 10°，与 3.5 同值
SUN = sun_direction(SUN_ELEVATION_DEG)                 # 指向太阳
D_IN = -SUN                                            # 入射光方向（固定）
ANTHELIC = TRICKER.anthelic_point()
REFERENCE = {3: ANTHELIC, 2: SUN}                      # 每行天空的参考点：上行反日点、下行太阳
REFERENCE_NAME = {3: "反日点", 2: "太阳"}

PRESET = PRESETS["default"].replace(
    style_map=PRESETS["default"].style_map.replace(
        annotation=TextStyle("ink", fontsize=13, family=CJK_SANS),
        panel_title=TextStyle("ink", fontsize=16, family=CJK_SANS),
        sphere_curve=LineStyle("sphere_curve", linewidth=1.6, alpha=0.8),      # 底图上淡画的公式特里克尔弧
        ray_internal=LineStyle("accent_warm", linewidth=1.4, alpha=0.6)),
    geom=PRESETS["default"].geom.replace(end_markers=False, face_number_height=0.3))
SAMPLE_COLORS = PRESET.style_map.sample_colors
BACKDROP_TEXT = TextStyle("background", fontsize=12, family=CJK_SANS)      # 底图（黑）上的白字
BACKDROP_MARK = MarkerStyle("background", size=5)

H_RATIO = 3.0
CRYSTAL = HexPrism(a=1.0, h=H_RATIO)
GRID_N = 35                                            # 入射面网格采样密度（可行入射区只是面上一小片；25 时 ψ=30°、θ≈52.6° 漏解）
PSI0, THETAS = 35.0, (39.0, 49.0, 59.0)


@dataclass(frozen=True)
class RowSpec:
    number: int                     # ch3 编号
    faces: tuple[int, ...]          # 代表光路（固定入射方向下可行区间最宽的那条）
    sweep: tuple[float, float]      # gif：ψ0 下 θ 的扫描区间 [θa, θb]（连续可行区间 ∩ [0°, 60°)，1° 扫描得到）
    title: str

    @property
    def matrix(self) -> np.ndarray:
        return rg.MATRICES[self.number]


ROWS = {
    3: RowSpec(3, (1, 2, 3, 5, 1), (34.0, 60.0), r"$M = br$（#3）：θ 线压成一点，平面压成特里克尔弧"),
    2: RowSpec(2, (1, 3, 2), (10.0, 60.0), r"$M = s$（#2）：每个 (ψ, θ) 各落一点，铺成太阳弥散区"),
}
for _spec in ROWS.values():
    assert tuple(_spec.faces) in rg.by_number(_spec.number).representative_paths


def solve(psi: float, theta: float, faces) -> tuple[np.ndarray, HexPrism, object]:
    """姿态 (ψ, θ) 下、固定入射方向 D_IN、面序列 faces 的真实光路：返回 (R, 晶体, RayPath)。找不到抛 ValueError。"""
    R = column_attitude(psi, theta)
    crystal = CRYSTAL.transformed(R)
    entry = crystal.face(faces[0])
    path = search_raypath(crystal, list(faces), np.array([D_IN]), entry_points=face_grid_points(crystal, entry, GRID_N),
                          tail=1.2, head=1.2)
    assert face_sequence(path) == list(faces)
    return R, crystal, path


def sky_point(number: int, R: np.ndarray) -> np.ndarray:
    """天空点 = T·ŝ = R M Rᵀ ŝ；机械核验：== −（追迹的出射方向）。"""
    return sky_direction(rg.MATRICES[number], R, SUN)


# ---- 相机 / 版面 ----------------------------------------------------------------------

FOV_3D = 20.0
CAMERA_STEP_COARSE, CAMERA_STEP_FINE = 5.0, 1.0
CAMERA_EL_RANGE = (-85.0, 85.0)
# 三栏 figure 坐标：左（姿态平面）/ 中（晶体面板列）/ 右（天空底图）
COL_LEFT, COL_MID, COL_RIGHT = (0.05, 0.27), (0.34, 0.53), (0.58, 0.98)
ROW_PAD = 0.06


def face_on(cam: Camera, a: np.ndarray, b: np.ndarray) -> float:
    """一对方向所张平面对相机的「正对度」|(â × b̂)·v̂| / |â × b̂| ∈ [0, 1]：= 画面上两段投影的 2D 叉积 / sin(真实夹角)，
    即投影夹角的正弦 × 两段投影长度 / sin(真实夹角)；平面正对观察者时 = 1（投影夹角 = 真实夹角、两段都不缩短），侧视时 → 0。
    字面的「投影夹角」有退化最优——视线接近两方向的角平分线时两段都缩成短桩、投影夹角趋于 180°（实测 179.996°），
    「展开」的本意反而没了；正对度把透视缩短计进去，没有这个退化。"""
    n = np.cross(unit(a), unit(b))
    nn = np.linalg.norm(n)
    return float(abs(n @ cam.view_dir) / nn) if nn > 1e-9 else 1.0


def min_face_on(cam: Camera, directions) -> float:
    """D 中两两方向所张平面正对度的最小值；三维上重合的方向对（如 br 行三条出射）不参与。"""
    d = [unit(v) for v in directions]
    best = 1.0
    for i in range(len(d)):
        for j in range(i + 1, len(d)):
            if np.linalg.norm(d[i] - d[j]) < 1e-6:
                continue
            best = min(best, face_on(cam, d[i], d[j]))
    return best


IN_OUT_MIN_RATIO = 0.9   # R1-2 沿用：每条光路入射 / 出射段在画面上的投影夹角 ≥ 0.9 × 真实夹角（搜索的可行域，按透视投影算）


def camera_at(az: float, el: float, scene_points) -> Camera:
    """(方位, 仰角) → 透视相机，距离按 FOV_3D 包住 scene_points（成图与搜索用同一构造）。"""
    d = solve_camera_distance(scene_points, azimuth=az, elevation=el, target_fov_deg=FOV_3D)
    return Camera(azimuth=az, elevation=el, distance=d)


def segment_angles(cam: Camera, path) -> tuple[float, float, np.ndarray]:
    """一条光路的入射段与出射段在画面上（透视投影）的夹角、三维真实夹角、出射段画面向量。"""
    a = cam.project_xy(path.points[:2])
    b = cam.project_xy(path.points[-2:])
    v_in, v_out = a[1] - a[0], b[1] - b[0]
    proj = float(np.degrees(np.arccos(np.clip(v_in @ v_out / np.linalg.norm(v_in) / np.linalg.norm(v_out), -1.0, 1.0))))
    true = float(np.degrees(np.arccos(np.clip(unit(path.points[1] - path.points[0]) @ unit(path.points[-1] - path.points[-2]),
                                              -1.0, 1.0))))
    return proj, true, v_out


def in_out_unfolded(cam: Camera, paths, ratio: float = IN_OUT_MIN_RATIO) -> bool:
    """R1-2 的「展开」条件：每条光路入射 / 出射段的画面投影夹角 ≥ ratio × 真实夹角。"""
    return all(segment_angles(cam, p)[0] >= ratio * segment_angles(cam, p)[1] for p in paths)


def exits_point_right(cam: Camera, paths) -> bool:
    """每条光路出射段的画面水平分量 > 0。"""
    return all(segment_angles(cam, p)[2][0] > 0 for p in paths)


def search_camera(paths, scene_points, *, require_exit_right: bool = True,
                  coarse: float = CAMERA_STEP_COARSE, fine: float = CAMERA_STEP_FINE) -> tuple[Camera, dict]:
    """显式搜索中栏相机（R2-2）：方位 × 仰角网格（``coarse`` 度粗扫全球、再在最优附近 ±coarse 内 ``fine`` 度细扫），
    每个格点按 :func:`camera_at` 建透视相机；可行域 = R1-2 的展开条件（:func:`in_out_unfolded`），在其中最大化
    D = {入射} ∪ {各出射} 两两所张平面正对度（:func:`face_on`）的最小值；``require_exit_right`` 时再硬约束全部出射段
    画面水平分量 > 0（"unconstrained" = 只去掉这一条）。返回 (相机, {"azimuth", "elevation", "value", "unconstrained",
    "projected_in_out"})；并列取扫描顺序靠前者。"""
    d_in = unit(paths[0].points[1] - paths[0].points[0])
    outs = [unit(p.points[-1] - p.points[-2]) for p in paths]
    dirs = [d_in] + outs

    def score(az: float, el: float) -> tuple[float, bool]:
        cam = camera_at(az, el, scene_points)
        if not in_out_unfolded(cam, paths):
            return -1.0, False
        return min_face_on(cam, dirs), exits_point_right(cam, paths)

    def scan(azs, els):
        best_c, best_u = None, None
        for el in els:
            for az in azs:
                v, ok = score(float(az), float(el))
                if best_u is None or v > best_u[2] + 1e-9:
                    best_u = (float(az), float(el), v)
                if (ok or not require_exit_right) and (best_c is None or v > best_c[2] + 1e-9):
                    best_c = (float(az), float(el), v)
        return best_c, best_u

    lo, hi = CAMERA_EL_RANGE
    c0, u0 = scan(np.arange(0.0, 360.0, coarse), np.arange(lo, hi + 1e-9, coarse))
    if c0 is None:
        raise ValueError("no camera satisfies the constraints")
    c1, _ = scan(np.arange(c0[0] - coarse, c0[0] + coarse + 1e-9, fine),
                 np.clip(np.arange(c0[1] - coarse, c0[1] + coarse + 1e-9, fine), lo, hi))
    _, u1 = scan(np.arange(u0[0] - coarse, u0[0] + coarse + 1e-9, fine),
                 np.clip(np.arange(u0[1] - coarse, u0[1] + coarse + 1e-9, fine), lo, hi))
    az, el, value = c1
    az %= 360.0
    cam = camera_at(az, el, scene_points)
    return cam, {"azimuth": az, "elevation": el, "value": value, "unconstrained": u1[2],
                 "projected_in_out": [segment_angles(cam, p)[0] for p in paths]}


@dataclass(frozen=True)
class Backdrop:
    """一行的 Lumice 底图：像素数组 + 出它的 render 段（投影用）+ 该行的参考点名（太阳 / 反日点）。"""
    image: np.ndarray               # (H, W, 3) uint8
    render: dict
    number: int

    @property
    def size(self) -> tuple[int, int]:
        return int(self.render["resolution"][0]), int(self.render["resolution"][1])

    @property
    def reference(self) -> np.ndarray:
        return REFERENCE[self.number]

    @property
    def reference_name(self) -> str:
        return REFERENCE_NAME[self.number]

    def project(self, directions) -> np.ndarray:
        return project(directions, self.render)


def backdrop_center(number: int) -> np.ndarray:
    """底图帧中心（机械规则）：该行参考点（反日点 / 太阳）与三个样本天空点质心的角平分方向——样本与参考点都离帧中心
    < 40°，远离 globe 75.5° 球冠的边缘（边缘处透视压扁）；上行 7.6°、下行 32° 离参考点。"""
    return unit(unit(REFERENCE[number]) + unit(np.mean(ROW_DATA[number].sky_points, axis=0)))


def backdrop_view(number: int) -> dict:
    """底图 render.view（globe 语义：帧中心 = (az + 180°, −el)）。"""
    return globe_view_for(backdrop_center(number))


@functools.lru_cache(maxsize=None)
def backdrop(number: int) -> Backdrop:
    """读 sim_pose_to_sky_backdrop.py 落盘的 config + 渲染图（data/，LFS）；惰性加载（底图脚本自己也 import 本模块）。
    核验：镜头 globe、帧中心 == backdrop_center(number)、Σ 一致。"""
    from PIL import Image
    cfg = json.loads((DATA / f"pose_to_sky_backdrop.col_{number}.lumice.json").read_text())
    render = cfg["render"][0]
    image = np.asarray(Image.open(DATA / "pose_to_sky_backdrop" / f"col_{number}" / "img_01.png").convert("RGB"))
    assert image.shape[:2] == tuple(render["resolution"][::-1])
    assert render["lens"]["type"] == "globe", "底图必须是 globe 球面外视（R2-3）"
    assert np.linalg.norm(frame_center(render) - backdrop_center(number)) < 1e-6, "底图帧中心必须是 backdrop_center 的规则值"
    assert abs(cfg["scene"]["light_source"]["altitude"] - SUN_ELEVATION_DEG) < 1e-9
    return Backdrop(image, render, number)


def sky_limits(number: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """右栏 axes 的 xlim / ylim（像素坐标，y 向下）。"""
    w, h = backdrop(number).size
    return (0, w), (h, 0)


def sample_marker(k: int, size: float = 9.0) -> MarkerStyle:
    return MarkerStyle(SAMPLE_COLORS[k], size=size)


def sample_line(k: int, width: float = 1.2, alpha: float = 0.9) -> LineStyle:
    return LineStyle(SAMPLE_COLORS[k], linewidth=width, alpha=alpha)


# ---- 三栏的常驻内容 ----------------------------------------------------------------------

THETA_PERIOD = 60.0    # θ 轴只画一个周期：见 build_attitude_axes 的说明


def build_attitude_axes(ax) -> None:
    """左栏：姿态平面 (ψ, θ)，ψ ∈ [0°, 360°)、θ ∈ [0°, 60°)，竖直线 ψ=ψ0。两行调用同一函数、同样参数 → byte-identical。

    θ 只画一个周期 60°（R1-2）：六棱柱绕 c 轴有六重对称，θ 与 θ+60° 是**同一枚晶体**（只是面编号轮换一位），所以姿态平面上
    θ 的物理周期是 60°。对光路矩阵而言这是 R_z(60°) 共轭：br ↦ br（b、r 都与 R_z 对易），s = S_90 ↦ S_150 = S_−30——
    仍是 s 一类、同一共轭类里的另一个元素；于是 θ ∈ [0°, 60°) 一段里"面序列固定"的一条光路，与 [60°, 120°) 里换了面编号的
    同一条物理光路一一对应，画一个周期就是全部。"""
    ax.set_xlim(0, 360)
    ax.set_ylim(0, THETA_PERIOD)
    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_yticks([0, 20, 40, 60])
    ax.tick_params(labelsize=10, colors=PRESET.palette["ink"])
    ax.set_xlabel(r"$\psi$（c 轴方位角，°）", **PRESET.text_kwargs("annotation"))
    ax.set_ylabel(r"$\theta$（绕 c 轴自转角，°）", **PRESET.text_kwargs("annotation"))
    ax.set_aspect("auto")
    ax.grid(True, color=PRESET.palette["grid"], linewidth=0.4, alpha=0.5)
    ax.axvline(PSI0, zorder=2, **PRESET.line_kwargs(LineStyle("slate", linewidth=1.0, alpha=0.8)))
    ax.text(PSI0 + 6, THETA_PERIOD - 2, r"$\psi=\psi_0$", fontsize=11, color=PRESET.palette["slate"], va="top")
    ax.text(358, 2, "θ 的周期是 60°（六重对称）", fontsize=9, color=PRESET.palette["slate"], ha="right", va="bottom",
            fontfamily=list(CJK_SANS))


def draw_samples_on_attitude(ax, samples, *, trail: np.ndarray | None = None) -> list:
    """姿态平面上的样本点（颜色 sample_1/2/3）；``trail`` (N,2) 给定时先画轨迹（gif）。"""
    artists = []
    if trail is not None and len(trail) > 1:
        artists += ax.plot(trail[:, 0], trail[:, 1], zorder=3, **PRESET.line_kwargs(sample_line(0, 1.0, 0.5)))
    for k, (psi, theta) in enumerate(samples):
        artists += ax.plot([psi], [theta], zorder=4, **PRESET.marker_kwargs(sample_marker(k)))
    return artists


def build_sky_axes(ax, number: int) -> None:
    """右栏常驻：Lumice globe 底图（像素坐标 imshow）+ 参考点标记（反日点 / 太阳）+（上行）整条公式特里克尔弧。"""
    b = backdrop(number)
    w, h = b.size
    ax.imshow(b.image, extent=(0, w, h, 0), interpolation="bilinear", zorder=0)
    xy = b.project(b.reference)[0]
    ax.plot([xy[0]], [xy[1]], zorder=8, **PRESET.marker_kwargs(BACKDROP_MARK))
    ax.text(xy[0] + 0.012 * w, xy[1] - 0.012 * h, b.reference_name, ha="left", va="bottom",
            zorder=Z_TEXT, **PRESET.text_kwargs(BACKDROP_TEXT))
    if number == 3:
        uv = b.project(TRICKER.CURVE)                       # 视线背后的点是 NaN，折线自然断开
        ax.plot(uv[:, 0], uv[:, 1], zorder=6, **PRESET.line_kwargs("sphere_curve"))


def draw_sky_samples(ax, number: int, points, *, stacked: bool, trail: np.ndarray | None = None) -> list:
    """右栏样本点：``stacked=True``（上行：三点重合）画成三色同心环（大到小），否则各画一点；``trail`` 画轨迹（gif）。"""
    b = backdrop(number)
    artists = []
    if trail is not None and len(trail) > 1:
        uv = b.project(trail)
        artists += ax.plot(uv[:, 0], uv[:, 1], zorder=9, **PRESET.line_kwargs(sample_line(0, 1.4, 0.8)))
    sizes = (15.0, 10.5, 6.0) if stacked else (9.0, 9.0, 9.0)
    for k, (p, size) in enumerate(zip(points, sizes)):
        uv = b.project(p)[0]
        artists += ax.plot([uv[0]], [uv[1]], zorder=10 + k, **PRESET.marker_kwargs(sample_marker(k, size)))
    return artists


def draw_crystal_panel(ax, number: int, k: int, crystal: HexPrism, path, *, framed: bool = True) -> list:
    """中栏一格：柱晶（可见面贴编号）+ 入射（红）/ 内部 / 出射（蓝）光路，边框取样本色。返回本次新增 artist（gif 逐帧移除用）。"""
    from matplotlib.patches import Rectangle
    before = set(ax.get_children())
    cam = CAMERAS_3D[number]
    render_crystal(ax, crystal, [path], camera=cam, preset=PRESET,
                   face_numbers=[f.number for f in visible_faces(crystal, cam)])   # 只贴朝向观察者的面：转过去的编号跟着变
    if framed:
        kw = PRESET.line_kwargs(sample_line(k, 2.4, 1.0))
        ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False, edgecolor=kw["color"],
                               linewidth=kw["linewidth"], zorder=20, clip_on=False))
    finish(ax, *CRYSTAL_LIMITS[number])
    return [a for a in ax.get_children() if a not in before]


PANEL_ENTRY = (0.0, 0.5)   # 左栏 → 中栏引线的终点：面板左边框中点（axes fraction），不进入画框


def exit_end_xy(number: int, path) -> np.ndarray:
    return CAMERAS_3D[number].project_xy(path.end)[0]


def sky_xy(number: int, p) -> np.ndarray:
    """天空方向在该行底图上的像素坐标（引线终点）。"""
    return backdrop(number).project(p)[0]


# ---- 一行（静态图） ----------------------------------------------------------------------

@dataclass
class RowData:
    number: int
    faces: tuple[int, ...]
    attitudes: list[np.ndarray]
    crystals: list[HexPrism]
    paths: list
    sky_points: list[np.ndarray]


def compute_row(number: int) -> RowData:
    spec = ROWS[number]
    Rs, cs, ps, sk = [], [], [], []
    for theta in THETAS:
        R, crystal, path = solve(PSI0, theta, spec.faces)
        Rs.append(R), cs.append(crystal), ps.append(path)
        sk.append(sky_point(number, R))
        d_out = unit(path.points[-1] - path.points[-2])
        assert np.linalg.norm(-d_out - sk[-1]) < 1e-9, "追迹的出射方向必须与 R M Rᵀ ŝ 一致"
    return RowData(number, spec.faces, Rs, cs, ps, sk)


ROW_DATA = {n: compute_row(n) for n in ROWS}


def scene_points(number: int) -> list[np.ndarray]:
    d = ROW_DATA[number]
    return [c.vertices for c in d.crystals] + [p.points for p in d.paths] + [np.array([[0, 0, 2.2], [0, 0, -2.2]])]


def _row_camera(number: int) -> tuple[Camera, dict]:
    return search_camera(ROW_DATA[number].paths, scene_points(number))


_CAMS = {n: _row_camera(n) for n in ROWS}
CAMERAS_3D = {n: c for n, (c, _) in _CAMS.items()}
CAMERA_SEARCH = {n: info for n, (_, info) in _CAMS.items()}
# 搜索结果记录（2026-09-13，5° 粗扫 + 1° 细扫）：(方位角°, 仰角°, 约束下最优正对度, 无约束最优正对度)——脚本导入时与实时搜索核对。
# #2 行约束 / 无约束 = 0.905：无约束最优处三条出射的画面水平分量异号，镜像相机也救不回来，「出射朝右」是真实代价
CAMERA_SEARCH_RECORD = {3: (272.0, -11.0, 1.0, 1.0), 2: (219.0, -57.0, 0.721, 0.797)}
for _n, _rec in CAMERA_SEARCH_RECORD.items():
    _got = (CAMERA_SEARCH[_n]["azimuth"], CAMERA_SEARCH[_n]["elevation"], round(CAMERA_SEARCH[_n]["value"], 3),
            round(CAMERA_SEARCH[_n]["unconstrained"], 3))
    assert _got == _rec, f"相机搜索结果变了：#{_n} {_got} != 记录 {_rec}（更新 CAMERA_SEARCH_RECORD 与顶注）"
# 中栏取景：该行三枚晶体 + 三条光路（含晶体外 1.2 的入射 / 出射段）一起包进画面，三格共用同一比例尺
CRYSTAL_LIMITS = {n: frame(CAMERAS_3D[n], [c.vertices for c in ROW_DATA[n].crystals] + [p.points for p in ROW_DATA[n].paths],
                           570, 330, margin=0.04) for n in ROWS}


def add_row_axes(fig, y0: float, h: float, n_mid: int):
    """一行的四组 axes：左姿态平面、中 n_mid 个晶体面板（竖排）、右天空球。返回 (ax_left, [ax_mid...], ax_sky)。"""
    ax_left = fig.add_axes([COL_LEFT[0], y0 + 2 * ROW_PAD * h, COL_LEFT[1] - COL_LEFT[0], h * (1 - 3 * ROW_PAD)])   # 下方留 x 轴标签
    mids = []
    gap = 0.02 * h
    ph = (h * (1 - 2 * ROW_PAD) - gap * (n_mid - 1)) / n_mid
    for k in range(n_mid):
        y = y0 + h * (1 - ROW_PAD) - (k + 1) * ph - k * gap
        ax = fig.add_axes([COL_MID[0], y, COL_MID[1] - COL_MID[0], ph])
        ax.set_axis_off()
        mids.append(ax)
    ax_sky = fig.add_axes([COL_RIGHT[0], y0 + ROW_PAD * h, COL_RIGHT[1] - COL_RIGHT[0], h * (1 - 2 * ROW_PAD)])
    ax_sky.set_axis_off()
    return ax_left, mids, ax_sky


def render_row(fig, y0: float, h: float, number: int) -> dict:
    """静态图的一行：三栏 + 引线。返回 {"left": ax, "mids": [...], "sky": ax, "connectors": [...]}。"""
    data = ROW_DATA[number]
    ax_left, mids, ax_sky = add_row_axes(fig, y0, h, 3)
    build_attitude_axes(ax_left)
    draw_samples_on_attitude(ax_left, [(PSI0, t) for t in THETAS])
    order = list(range(len(mids)))[::-1]                       # 面板自上而下 = θ3 / θ2 / θ1，与左栏 θ 轴同向，引线不交叉
    for k, ax in zip(order, mids):
        draw_crystal_panel(ax, number, k, data.crystals[k], data.paths[k])
    build_sky_axes(ax_sky, number)
    draw_sky_samples(ax_sky, number, data.sky_points, stacked=(number == 3))
    finish(ax_sky, *sky_limits(number))
    ax_sky.set_title(ROWS[number].title, **PRESET.text_kwargs("panel_title"), math_fontfamily="cm", loc="right")
    connectors = []
    for k, ax in zip(order, mids):
        connectors.append(draw_connector(ax_left, (PSI0, THETAS[k]), ax, PANEL_ENTRY, preset=PRESET,
                                         semantic=sample_line(k), coords_b="axes fraction"))
        connectors.append(draw_connector(ax, exit_end_xy(number, data.paths[k]), ax_sky, sky_xy(number, data.sky_points[k]),
                                         preset=PRESET, semantic=sample_line(k)))
    annotate_2d(ax_left, "\n".join(f"θ{k + 1} = {t:g}°" for k, t in enumerate(THETAS)), (200, 30), preset=PRESET,
                ha="left", va="center")
    return {"left": ax_left, "mids": mids, "sky": ax_sky, "connectors": connectors}


# ---- 探针（可行区间扫描；写进本文件顶注） ----------------------------------------------------

def probe(number: int, psis, step: float = 1.0) -> dict:
    """对 ROWS[number].faces 逐 ψ 扫 θ∈[0,360) 的可行性（每 step 度一次），返回 {ψ: [(θa, θb), …]} 连续可行区间。"""
    out = {}
    for psi in psis:
        ok = []
        for t in np.arange(0.0, 360.0, step):
            try:
                solve(psi, float(t), ROWS[number].faces)
                ok.append(float(t))
            except ValueError:
                pass
        runs: list[list[float]] = []
        for t in ok:
            if runs and abs(t - runs[-1][1] - step) < 1e-9:
                runs[-1][1] = t
            else:
                runs.append([t, t])
        out[psi] = [tuple(r) for r in runs]
    return out


if __name__ == "__main__":   # `python _pose_to_sky.py --probe 3 30,35,40`
    if len(sys.argv) >= 4 and sys.argv[1] == "--probe":
        print(probe(int(sys.argv[2]), [float(p) for p in sys.argv[3].split(",")]))
