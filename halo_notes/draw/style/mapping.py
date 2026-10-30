"""风格第二层：语义 → 样式。

每个绘图语义（可见面线、入射光、面编号……）对应一组视觉参数；颜色字段
填的是配色板里的颜色名，不是色值，真正的色值在 :class:`presets.Preset`
组合时才解析。**所有"画成什么样"的数值只住在这一层**——后续切片要加新语义
（高亮面、展开幽灵晶体……）优先在这里加字段，不要新开第五层风格对象。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Mapping


# 含 CJK 字形的无衬线字体回退序列：macOS 自带的冬青黑体在前，缺时退回 matplotlib 默认
# （列表里每个缺失的族 matplotlib 都会打一条 findfont 警告，所以不堆一长串候选）
CJK_SANS = ("Hiragino Sans GB", "DejaVu Sans")


@dataclass(frozen=True)
class LineStyle:
    color: str            # 配色板颜色名
    linewidth: float = 1.0
    linestyle: str = "-"
    alpha: float = 1.0


@dataclass(frozen=True)
class FillStyle:
    color: str
    alpha: float = 1.0


@dataclass(frozen=True)
class TextStyle:
    color: str
    fontsize: float = 12.0
    alpha: float = 1.0
    weight: str = "normal"
    style: str = "normal"   # "normal" / "italic"
    family: str | tuple[str, ...] | None = None   # 元组 = 按序回退的字体族列表


@dataclass(frozen=True)
class MarkerStyle:
    color: str
    size: float = 4.0       # 直径，pt
    alpha: float = 1.0


@dataclass(frozen=True)
class SurfaceStyle:
    """一种着色曲面：底色、环境光占比（越高越哑光）、mesh 线色与半宽、轮廓线色。

    颜色字段填的是配色板里的颜色名；解析成 hex 的 :class:`~figure.Surface` 由
    图表入口 ``figure_scheme()`` 给出。
    """

    base: str
    ambient: float
    mesh: str
    mesh_width: float = 0.004
    outline: str | None = None


# 取向族（篇内一致）：柱晶蓝 / 片晶红是系列两主色，包含关系用同色相深浅编码
# （Parry ⊂ 柱晶深一档、Lowitz ⊃ 片晶浅一档），随机族中性石板灰
_FAMILY_COLORS = MappingProxyType({
    "random": "stone",
    "column": "arc_roll",
    "parry": "navy",
    "plate": "face_3",
    "lowitz": "coral_pale",
})
# 黑底天象上的族辉光：随机族为中性白灰，柱晶 / 片晶沿用蓝 / 红
_SKY_GLOW_COLORS = MappingProxyType({
    "random": "mist",
    "column": "accent_cool",
    "plate": "face_3",
})
# 黑底天象上的中性元素：文字、等角距圈 / 地平线等辅助线、夜空底色
_SKY_COLORS = MappingProxyType({
    "ink": "ink_faint",
    "ring": "slate",
    "guide": "cloud",
    "night": "ink",
})
# 非族非光线的二元对照（路线 A/B、D 与 Δφ 等）：a 墨实线，b 紫虚线（pair_dash）
_PAIR_COLORS = MappingProxyType({
    "a": "charcoal",
    "b": "face_8",
})
# 三组着色曲面：柱晶环面（冰蓝）、Lowitz 环面（淡珊瑚）、中性示意球（极淡蓝白）
_SURFACE_STYLES = MappingProxyType({
    "column": SurfaceStyle("glacier", 0.80, "glacier_mesh", 0.0042, "glacier_deep"),
    "lowitz": SurfaceStyle("blush", 0.84, "blush_mesh", 0.0042, "blush_deep"),
    "neutral": SurfaceStyle("frost", 0.84, "frost_mesh", 0.0040, "frost_deep"),
})


@dataclass(frozen=True)
class SemanticStyleMap:
    """语义 → 样式的一整套映射。字段名就是语义名。"""

    edge_visible: LineStyle
    edge_hidden: LineStyle
    edge_ghost: LineStyle                # 展开幽灵晶体的线框（透明线框：所有边都画，不分可见/不可见）
    face_fill: FillStyle | None          # None 表示不填充
    face_fill_hidden: FillStyle | None
    face_highlight: FillStyle            # 高亮面（光走廊里的反射面 / 出入面）
    face_highlight_hidden: FillStyle     # 高亮面背对观察者时
    ray_incident: LineStyle
    ray_internal: LineStyle              # 晶体内部段
    ray_exit: LineStyle
    ray_occluded: LineStyle              # 外部段被晶体挡住的部分
    ray_unfolded: LineStyle              # 展开后的直线光路（穿过幽灵晶体串）
    ray_folded: LineStyle                # 与展开直线同图时退居次要的真实折线光路
    ray_marker: MarkerStyle              # 光路端点 / 事件点
    ray_marker_hidden: MarkerStyle
    face_number: TextStyle
    face_number_hidden: TextStyle
    face_number_ghost: TextStyle         # 展开幽灵晶体上朝向观察者的面编号（中等灰：比实体淡、比背面深）
    axis: LineStyle
    axis_occluded: LineStyle
    axis_label: TextStyle
    annotation: TextStyle
    # ---- 2D 截面图（scene2d）：以下全部带默认值，只增不改 ----
    ray2d: LineStyle = LineStyle("accent_warm", linewidth=1.6)            # 截面光路默认单色（1.2 / 3.1 的红线）
    ray2d_discarded: LineStyle = LineStyle("ink_faint", linewidth=1.6, linestyle="--")  # 6.2 蒙特卡洛未选中的分支（灰虚线）
    edge_reference: LineStyle = LineStyle("reference", linewidth=1.3)      # 对称操作的参考幽灵（原位淡六边形，1.3 / 1.6）
    face_number_reference: TextStyle = TextStyle("slate", fontsize=26, weight="bold", alpha=0.22)  # 参考幽灵上的淡编号
    symmetry_mark: LineStyle = LineStyle("reference", linewidth=3.2)       # 旋转弧箭头 / 翻转轴的双向箭头
    symmetry_spoke: LineStyle = LineStyle("reference", linewidth=1.2)      # 旋转弧两端的辐条（参考方向 / 目标方向）
    flip_axis: LineStyle = LineStyle("slate", linewidth=1.3, linestyle=(0, (6, 3, 1, 3)), alpha=0.9)  # 翻转轴：点划线
    plate_fill: FillStyle = FillStyle("plate", alpha=1.0)                  # 6.2 平板
    plate_edge: LineStyle = LineStyle("plate_edge", linewidth=3.0)
    medium_fill: FillStyle = FillStyle("medium", alpha=1.0)                # 3.1 楔形介质
    medium_edge: LineStyle = LineStyle("ink", linewidth=1.6)
    angle_mark: LineStyle = LineStyle("ink", linewidth=1.0)                # 3.1 楔角 θ 的弧标注
    panel_title: TextStyle = TextStyle("ink", fontsize=30)                 # 多面板下方的 LaTeX 标题
    leader: LineStyle = LineStyle("ink", linewidth=0.8)                    # 注释引线
    caption: TextStyle = TextStyle("ink_soft", fontsize=26, weight="bold", family=CJK_SANS)  # 1.2 旧图的粗体图注
    symbol: TextStyle = TextStyle("ink", fontsize=84, family=("DejaVu Sans",))   # ⇓ / ⟺ 这类 Unicode 箭头符号
    # ---- 3D 旋转弧 / 主轴箭头（3.4）与球面族图元（3.5 / 3.6 / 6.1）：只增不改 ----
    arc_roll: LineStyle = LineStyle("arc_roll", linewidth=2.6)              # 绕晶体 c 轴的 θ 弧
    arc_tilt: LineStyle = LineStyle("arc_tilt", linewidth=2.6)              # 绕 y 轴的 π/2 弧
    arc_azimuth: LineStyle = LineStyle("arc_azimuth", linewidth=2.6)        # 绕 z 轴的 α 弧
    arc_label: TextStyle = TextStyle("ink", fontsize=22, style="italic")    # 弧旁的 LaTeX 标签（与 axis_label 同款）
    axis_main: LineStyle = LineStyle("ink", linewidth=3.0)                  # 主轴箭头：黑色粗线 + 实心锥
    sphere_grid: LineStyle = LineStyle("grid", linewidth=0.5)               # 经纬网格朝向观察者的一半
    sphere_grid_hidden: LineStyle = LineStyle("grid", linewidth=0.5, alpha=0.4)   # 背面网格：同色减淡
    equator: LineStyle = LineStyle("slate", linewidth=1.3)                  # 6.1 赤道：前半实线
    equator_hidden: LineStyle = LineStyle("slate", linewidth=1.3, linestyle="--")  # 后半虚线
    sphere_curve: LineStyle = LineStyle("sphere_curve", linewidth=3.0)      # 球面上的参数曲线（3.5 旧图的粗蓝弧）
    sphere_curve_hidden: LineStyle = LineStyle("sphere_curve", linewidth=3.0, alpha=0.3)
    pose_cloud: MarkerStyle = MarkerStyle("cloud", size=0.9)                # 姿态点云（6.1 旧图的细小灰点）
    pose_cloud_hidden: MarkerStyle = MarkerStyle("cloud", size=0.9, alpha=0.35)
    cone_surface: FillStyle = FillStyle("cone", alpha=0.35)                 # 3.6 锥面淡填充
    cone_edge: LineStyle = LineStyle("grid", linewidth=0.4)                 # 3.6 锥面网格线
    # ---- ch7（7.1–7.5）：翻转标记 / 跨 axes 引线 / 姿态样本三色：只增不改 ----
    flip_marker: LineStyle = LineStyle("slate", linewidth=1.6)             # 7.3 下行格「z 上下翻转」小标记：一条水平线 + 一支双向竖箭头
    connector: LineStyle = LineStyle("ink_soft", linewidth=1.0, alpha=0.8)   # 7.5 跨 axes 引线（ConnectionPatch）
    sample_colors: tuple[str, str, str] = ("sample_1", "sample_2", "sample_3")   # 7.5 三个姿态样本的语义色（配色板颜色名）
    sample_marker: MarkerStyle = MarkerStyle("sample_1", size=9.0)          # 样本点模板：颜色按 sample_colors 逐个 replace
    sample_frame: LineStyle = LineStyle("sample_1", linewidth=2.4)          # 中栏面板边框模板（同上）
    # 面号 → 配色板颜色名；给定时截面边编号按面号取色（字号 / 透明度仍取对应 face_number* 语义），
    # None = 全部用语义里的颜色。3D 贴面编号不读这个字段
    face_number_colors: Mapping[int, str] | None = None
    # ---- 9.1 / ch10 图表语义（升格自 #48 定稿，2026-10-30 作者签核）：只增不改 ----
    # 作用域是「篇内一致」：``figure_scheme(**overrides)`` 按篇覆盖这里的字段，不做全系列硬映射
    family_colors: Mapping[str, str] = _FAMILY_COLORS        # 取向族 → 颜色名
    sky_glow_colors: Mapping[str, str] = _SKY_GLOW_COLORS    # 黑底天象的族辉光 → 颜色名
    sky_colors: Mapping[str, str] = _SKY_COLORS              # 黑底天象中性元素（ink/ring/guide/night）→ 颜色名
    sun_color: str = "gold"                                  # 太阳：金色圆点 / 箭头
    point_color: str = "accent_cool"                         # 光点方向 x = 出射光反向（语义同源，色随 ray_exit）
    pair_colors: Mapping[str, str] = _PAIR_COLORS            # 非族二元对照：a 墨实线 / b 紫虚线
    pair_dash: tuple = (0, (4.0, 2.6))                       # 对照 B 的虚线相位
    ink_color: str = "ink_soft"                              # 图面文字 / 引线
    guide_color: str = "haze"                                # 经纬网 / 辅助线
    terrain_ramp: tuple[str, ...] = ("fog", "stone_light", "charcoal")   # 地形色阶：单色相、明度单调
    crystal_fill: FillStyle = FillStyle("ice", alpha=0.8)    # 晶体填充（冰蓝半透明）
    crystal_edge: str = "ice_edge"                           # 晶体线框
    sphere_fill: FillStyle = FillStyle("ice", alpha=0.24)    # 示意球（天球 / u 球 / 小球）底色
    sphere_edge: str = "ice_edge"                            # 示意球轮廓
    surface_styles: Mapping[str, SurfaceStyle] = _SURFACE_STYLES   # 着色曲面：column / lowitz / neutral

    def replace(self, **changes: Any) -> "SemanticStyleMap":
        return replace(self, **changes)


# 默认映射：以旧图观感为起点——黑线框、背面淡灰、入射红 / 出射蓝
DEFAULT_MAP = SemanticStyleMap(
    edge_visible=LineStyle("ink", linewidth=1.3),
    edge_hidden=LineStyle("ink_faint", linewidth=0.7),
    edge_ghost=LineStyle("ink", linewidth=0.8, linestyle=":", alpha=0.5),  # 旧图幽灵晶体：灰色点线
    face_fill=None,
    face_fill_hidden=None,
    face_highlight=FillStyle("highlight", alpha=0.9),
    face_highlight_hidden=FillStyle("highlight", alpha=0.5),  # 与 *_hidden 惯例一致：同色减淡（线框透明，背面也要看得出是黄的）
    ray_incident=LineStyle("accent_warm", linewidth=1.6),
    ray_internal=LineStyle("accent_warm", linewidth=1.6, alpha=0.3),
    ray_exit=LineStyle("accent_cool", linewidth=1.6),
    ray_occluded=LineStyle("accent_warm", linewidth=1.6, alpha=0.3),
    ray_unfolded=LineStyle("accent_cool", linewidth=1.6),                    # 2.5 旧图：实线蓝
    ray_folded=LineStyle("accent_warm", linewidth=1.4, linestyle=":", alpha=0.9),  # 2.5 旧图：红点线
    ray_marker=MarkerStyle("accent_warm", size=5.0),
    ray_marker_hidden=MarkerStyle("accent_warm", size=5.0, alpha=0.3),
    face_number=TextStyle("slate", fontsize=26, weight="bold"),
    face_number_hidden=TextStyle("slate", fontsize=26, weight="bold", alpha=0.2),  # 与 face_number 同字号，只靠变淡表达在背面
    face_number_ghost=TextStyle("slate", fontsize=26, weight="bold", alpha=0.45),  # 旧 2.4 幽灵上的 4 / 5 / 8：中等灰
    axis=LineStyle("accent_warm", linewidth=1.3),
    axis_occluded=LineStyle("accent_warm", linewidth=1.3, alpha=0.2),
    axis_label=TextStyle("ink", fontsize=22, style="italic"),
    # 注释文字是中文（2.2 / 2.3 / 2.8 / 3.2 的图注），默认字体族给一串含 CJK 的回退序列
    annotation=TextStyle("ink", fontsize=18, family=CJK_SANS),
)
