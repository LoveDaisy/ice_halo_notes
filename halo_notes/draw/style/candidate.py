"""【暂存】#48 修图期间的候选配色方案——ch9.1 / ch10 插图颜色的唯一入口。

本模块只在 #48 迭代期间存在：作者选定方案后，由 #49 把胜出方案升格进 ``mapping``
层的正式语义 token，然后删除本模块。不要在别处引用它，也不要往这里加 ch9.1 / ch10
以外的用途。

章内脚本只读 ``scheme()`` 返回的语义槽（族、太阳、光点、地形色阶、曲面……），
不写十六进制色值，也不用 ``PAL["face_5"]`` 这类颜料名表达概念。环境变量
``HALO_FIG_SCHEME`` 切换候选（默认 ``S1``，作者已选定），``HALO_FIG_TERRAIN`` 单独覆盖地形色阶，
出 compare 时逐方案跑子进程。

第二轮（作者否掉松石 + 琥珀，2026-10-30）：族色回到系列惯用的蓝 / 红两主色及其近邻
（ch8 折叠光路、ch9 图 2/3）。三套方案共用这组概念色，差别只在曲面与晶体的表面处理：

- S1 冰蓝 + 淡珊瑚：柱晶环面冰蓝偏深、Lowitz 环面极淡的珊瑚粉，曲面本身带族身份；
- S2 冰蓝统一：曲面全用系列冰蓝（#47 作者选过的 A 方案，降低高光、mesh 更清晰）；
- S3 纸面线描：曲面几乎不填色，几何靠墨线，颜色只出现在族元素上。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Mapping

from .palette import DEFAULT_LIGHT as _PAL

# ---- 共用概念色（三套方案相同） --------------------------------------------
# 柱晶 = 蓝、片晶 = 红（与 ch10 图 1 现版一致）；族的包含关系用同色相深浅编码
# （Parry ⊂ 柱晶取深一档，片晶 ⊂ Lowitz 取浅一档），随机族中性灰。
FAMILY = MappingProxyType({
    "random": "#8C96A3",           # 石板灰
    "column": _PAL["arc_roll"],    # 蓝 #4E78BE
    "parry": "#2E4B7E",            # 蓝深一档
    "plate": _PAL["face_3"],       # 红 #E95536
    "lowitz": "#F2917C",           # 红浅一档
})
# 黑底天象上的族辉光：沿用 ch10 图 1 现版（作者认可的效果），随机族为中性白灰
SKY_GLOW = MappingProxyType({
    "random": "#D2D6DC",
    "column": _PAL["accent_cool"],
    "plate": _PAL["face_3"],
})
# 黑底天象上的中性元素：文字、等角距圈 / 地平线等辅助线、夜空底色
SKY = MappingProxyType({
    "ink": _PAL["ink_faint"],
    "ring": _PAL["slate"],
    "guide": _PAL["cloud"],
    "night": _PAL["ink"],
})
# 太阳：金色。蓝 / 红已归族，太阳若仍用入射珊瑚红会与片晶红撞色（ΔE≈7）。
SUN = "#E8A020"
POINT = _PAL["accent_cool"]     # 光点方向 x = 出射光反向
RAY_IN = _PAL["accent_warm"]
RAY_OUT = _PAL["accent_cool"]
# 非族非光线的二元对照（路线 A/B、D 与 Δφ 等）：墨实线 vs 紫虚线（ch9 图 2 的紫近邻）
PAIR = MappingProxyType({"a": "#2F3A4A", "b": _PAL["face_8"]})
PAIR_DASH = (0, (4.0, 2.6))
INK = _PAL["ink_soft"]          # 图面文字、引线
GUIDE = "#C9CFD8"               # 经纬网、辅助线
PAPER = _PAL["background"]

# 地形色阶候选（单色相、亮度单调）。冰蓝→深蓝已不再候选：会与柱晶蓝的带边界同色相。
TERRAIN_RAMPS = MappingProxyType({
    "T1": ("#F1EEF8", "#A59ACF", "#3E3470"),   # 淡紫 → 靛
    "T3": ("#F3F4F6", "#A3ABB7", "#2F3A4A"),   # 中性石板：纸白 → 墨
})


@dataclass(frozen=True)
class Surface:
    """一种着色曲面：底色、环境光占比（越高越哑光）、mesh 线色与半宽、轮廓线色。"""

    base: str
    ambient: float
    mesh: str
    mesh_width: float = 0.004
    outline: str | None = None


@dataclass(frozen=True)
class Scheme:
    name: str
    label: str
    surfaces: Mapping[str, Surface] = field(default_factory=dict)
    terrain: str = "T3"
    crystal_fill: str = _PAL["ice"]
    crystal_fill_alpha: float = 0.8
    crystal_edge: str = _PAL["ice_edge"]
    sphere_fill: str = _PAL["ice"]       # 示意球（u 球 / 小球）底色
    sphere_fill_alpha: float = 0.24
    sphere_edge: str = _PAL["ice_edge"]

    def __post_init__(self) -> None:
        object.__setattr__(self, "surfaces", MappingProxyType(dict(self.surfaces)))

    # 共用槽直接挂在方案上，脚本只需要 ``S = scheme()`` 一个入口
    family = FAMILY
    sky_glow = SKY_GLOW
    sky = SKY
    sun = SUN
    point = POINT
    ray_in = RAY_IN
    ray_out = RAY_OUT
    pair = PAIR
    pair_dash = PAIR_DASH
    ink = INK
    guide = GUIDE
    paper = PAPER

    @property
    def terrain_ramp(self) -> tuple[str, ...]:
        return TERRAIN_RAMPS[self.terrain]


SCHEMES: Mapping[str, Scheme] = MappingProxyType({s.name: s for s in (
    Scheme(
        "S1", "冰蓝 + 淡珊瑚",
        surfaces={
            "column": Surface("#C9DAEF", 0.80, "#6F88AE", 0.0042, "#3E5A86"),
            "lowitz": Surface("#F8E4DE", 0.84, "#C79A8E", 0.0042, "#9A6556"),
            "neutral": Surface("#E3EEF8", 0.84, "#7D8DA3", 0.0040, "#56677D"),
        },
        terrain="T3",
    ),
    Scheme(
        "S2", "冰蓝统一",
        surfaces={
            "column": Surface("#AFCBE6", 0.80, "#5F7896", 0.0040, "#3E5675"),
            "lowitz": Surface("#DCEFFB", 0.84, "#6F8197", 0.0040, "#56677D"),
            "neutral": Surface("#DCEFFB", 0.84, "#6F8197", 0.0040, "#56677D"),
        },
        terrain="T1",
    ),
    Scheme(
        "S3", "纸面线描",
        surfaces={
            "column": Surface("#EEF0F2", 0.90, "#B4BAC2", 0.0032, "#2F3A4A"),
            "lowitz": Surface("#FBFBFA", 0.92, "#C3C8CE", 0.0032, "#2F3A4A"),
            "neutral": Surface("#FBFBFA", 0.92, "#C3C8CE", 0.0032, "#2F3A4A"),
        },
        terrain="T3",
        crystal_fill="#FFFFFF", crystal_fill_alpha=0.9, crystal_edge="#2F3A4A",
        sphere_fill="#FFFFFF", sphere_fill_alpha=0.0, sphere_edge="#2F3A4A",
    ),
)})

DEFAULT_SCHEME = "S1"   # 2026-10-30 作者选定：曲面 S1、地形 T3、太阳金色


def scheme(name: str | None = None) -> Scheme:
    """当前候选方案；``name`` 省略时读 ``HALO_FIG_SCHEME``，再省略用 ``DEFAULT_SCHEME``。"""
    key = name or os.environ.get("HALO_FIG_SCHEME") or DEFAULT_SCHEME
    try:
        chosen = SCHEMES[key]
    except KeyError:
        raise KeyError(f"未知候选方案 {key!r}；可选 {sorted(SCHEMES)}") from None
    terrain = os.environ.get("HALO_FIG_TERRAIN")
    if terrain:
        if terrain not in TERRAIN_RAMPS:
            raise KeyError(f"未知地形色阶 {terrain!r}；可选 {sorted(TERRAIN_RAMPS)}")
        chosen = replace(chosen, terrain=terrain)
    return chosen


def crystal_preset(base=None, name: str | None = None):
    """晶体渲染预设：在 ``ice_filled`` 上换成当前方案的晶体填充 / 线框，不标背面编号，编号正放。

    小尺寸晶体的背面贴面编号是镜像变形字，缩小后成乱码，一律不标；正面的贴面编号随姿态
    转成倒置 / 侧卧（「3」读成「ε」「ω」），也改为面心水平正放（``FLAT``）。
    """
    from .geom_style import FaceNumberStyle
    from .presets import PRESETS

    s = scheme(name)
    base = base or PRESETS["ice_filled"]
    fill = base.style_map.face_fill
    return base.replace(
        name=f"{base.name}_{s.name}",
        palette=base.palette.with_colors(ice=s.crystal_fill, ice_edge=s.crystal_edge),
        style_map=base.style_map.replace(face_fill=fill.__class__(fill.color, s.crystal_fill_alpha)),
        geom=base.geom.replace(label_hidden_faces=False, face_number_style=FaceNumberStyle.FLAT),
    )
