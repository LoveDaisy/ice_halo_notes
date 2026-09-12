"""风格第三层：具体几何风格参数——锥体箭头尺寸、纬线圈数、不可见面画不画等。

只放"画不画 / 多大 / 几圈"这类几何量；不可见线"画成什么颜色线宽"完全由
:mod:`mapping` 的 ``edge_hidden`` 决定，这里不重复定义任何视觉参数。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any


class HiddenEdgeMode(Enum):
    """不可见面的边：按 ``edge_hidden`` 样式画出来，或干脆不画。"""

    DRAW = "draw"
    HIDE = "hide"


class FaceNumberStyle(Enum):
    """面编号：贴在面上随视角仿射变形（旧图观感），或在面心水平正放。"""

    WARPED = "warped"
    FLAT = "flat"


@dataclass(frozen=True)
class GeomStyle:
    # 不可见面
    hidden_edges: HiddenEdgeMode = HiddenEdgeMode.DRAW
    label_hidden_faces: bool = True
    # 面编号
    face_number_style: FaceNumberStyle = FaceNumberStyle.WARPED
    # 贴面编号的字高（世界单位，a=1 的 crystal units）：贴面文字像贴纸一样随晶体缩放，
    # 不按印刷点计；正放模式仍用 TextStyle.fontsize（点）
    face_number_height: float = 0.55
    # 锥体箭头（长度单位与晶体同：a=1 时的 crystal units）
    cone_length: float = 0.36
    cone_radius: float = 0.13
    cone_rings: int = 3          # 纬线圈数（含底面圆）
    cone_samples: int = 72       # 每圈采样点数
    # 光路外部段
    incident_tail: float = 1.6   # 入射段在晶体外画多长
    exit_head: float = 1.6       # 出射段在晶体外画多长
    # 锥体箭头统一锥尖朝传播方向（旧 2.4 / 2.6 约定）；下面两个参数是**锥尖**在该段上的位置
    incident_cone_at: float = 0.5  # 入射段：0=尾端（自由端），1=入射点；默认光线中段（旧 2.4）
    exit_cone_at: float = 1.0      # 出射段：0=出射点，1=末端（自由端）；默认尖在末端（标准箭头）
    end_markers: bool = True       # 光路首尾画小圆点
    event_markers: bool = True     # 折射 / 反射点画小圆点
    # 2D 截面图（geometry2d / scene2d）
    arrow2d_length: float = 0.16   # 光线上的实心小三角箭头：长（沿传播方向）与底宽，单位与截面同（a=1）；旧图 1.2 比例
    arrow2d_width: float = 0.11
    arrow2d_at: float = 0.5        # 每段上箭头尖的默认位置（0=段起点，1=段终点）
    mark_arrow_scale: float = 1.8  # 对称操作标注（旋转弧、翻转轴双向箭头）的三角相对光线箭头的放大倍数（旧图 1.2 / 1.3 的大灰箭头）
    edge_number_height: float = 0.19   # 截面边编号的字高（世界单位；旧图 1.2 / 1.3 约 0.15–0.2 a）
    edge_number_inset: float = 0.25    # 编号中心从边中点向内退的距离
    # 坐标轴
    axis_length: float = 2.4
    axis_label_pad: float = 0.18   # 轴标签离箭头尖的距离
    axis_cone_scale: float = 0.5   # 轴箭头（实心）相对光线锥体的整体缩放（长度与半径同缩；旧图 3.3 目测约 0.35，取裁定区间 0.5–0.7 下限）
    # 主轴箭头（6.1 / 3.4 第三帧从晶体中心沿 c 轴伸出的粗箭头）与 3D 旋转弧（3.4）
    main_axis_cone_scale: float = 0.8   # 主轴箭头的实心锥体相对光线锥体的缩放（比坐标轴箭头大一号）
    arc_cone_scale: float = 0.5         # 旋转弧末端箭头的锥体缩放（与坐标轴箭头同号）
    arc_label_pad: float = 0.35         # 弧旁标签离弧中点的径向距离（世界单位）
    # 球面图元（sphere）
    sphere_grid_step_deg: float = 15.0  # 经纬网格间隔（6.1 旧图约 15°；3.5 / 3.6 旧 nb 用 10°，脚本自行覆盖）
    sphere_samples: int = 181           # 每条网格线 / 大圆的采样点数（可见性切段的分辨率）
    cone_extend: float = 1.15           # 3.6 锥面沿母线延伸到与球面交线之外的比例

    def replace(self, **changes: Any) -> "GeomStyle":
        return replace(self, **changes)


DEFAULT_GEOM = GeomStyle()
