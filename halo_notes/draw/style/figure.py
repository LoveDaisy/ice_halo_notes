"""图表语义槽解析器——新章画图取色的唯一入口。

``figure_scheme()`` 把 :mod:`mapping` 里的图表语义 token 解析成一个
:class:`FigureScheme`（族、太阳、光点、二元对照、曲面、地形色阶、晶体 / 球面……），
颜色槽全部是已解析的 hex，章脚本拿 ``S = figure_scheme()`` 一个入口用全篇。
语义的权威在 :mod:`mapping`，本模块只做解析；**篇内覆盖**经 ``**overrides``
传 :class:`~mapping.SemanticStyleMap` 的字段名（颜色-语义一致的作用域是篇内，
跨篇不强制，作者 2026-10-30 裁定）。
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .mapping import DEFAULT_MAP, SemanticStyleMap
from .palette import DEFAULT_LIGHT


@dataclass(frozen=True)
class Surface:
    """一种着色曲面（已解析）：底色、环境光占比（越高越哑光）、mesh 线色与半宽、轮廓线色。"""

    base: str
    ambient: float
    mesh: str
    mesh_width: float = 0.004
    outline: str | None = None


@dataclass(frozen=True)
class FigureScheme:
    """篇内共用的图表语义槽集合；颜色槽全部是 hex，曲面槽是 :class:`Surface`。"""

    family: Mapping[str, str]                 # 取向族：random / column / parry / plate / lowitz
    sky_glow: Mapping[str, str]               # 黑底天象的族辉光：random / column / plate
    sky: Mapping[str, str]                    # 黑底天象中性元素：ink / ring / guide / night
    sun: str                                  # 太阳（金色圆点 / 箭头）
    point: str                                # 光点方向 x（出射光反向）
    ray_in: str                               # 入射光（含冰内段）
    ray_out: str                              # 出射光
    pair: Mapping[str, str]                   # 非族二元对照：a 实线 / b 虚线
    pair_dash: tuple                          # 对照 B 的虚线相位
    ink: str                                  # 图面文字 / 引线
    guide: str                                # 经纬网 / 辅助线
    paper: str                                # 纸面底色
    surfaces: Mapping[str, Surface]           # 着色曲面：column / lowitz / neutral
    terrain_ramp: tuple[str, ...]             # 地形色阶（单色相、明度单调）
    crystal_fill: str                         # 晶体填充
    crystal_fill_alpha: float
    crystal_edge: str                         # 晶体线框
    sphere_fill: str                          # 示意球（天球 / u 球 / 小球）底色
    sphere_fill_alpha: float
    sphere_edge: str                          # 示意球轮廓

    def __post_init__(self) -> None:
        for name in ("family", "sky_glow", "sky", "pair", "surfaces"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


def _resolve(style: SemanticStyleMap) -> FigureScheme:
    """把一套语义映射解析成 hex 槽；光线两槽沿用既有 ``ray_incident`` / ``ray_exit`` 语义。"""
    pal = DEFAULT_LIGHT
    surfaces = {}
    for key, s in style.surface_styles.items():
        surfaces[key] = Surface(
            base=pal[s.base], ambient=s.ambient, mesh=pal[s.mesh],
            mesh_width=s.mesh_width,
            outline=pal[s.outline] if s.outline is not None else None,
        )
    return FigureScheme(
        family={k: pal[v] for k, v in style.family_colors.items()},
        sky_glow={k: pal[v] for k, v in style.sky_glow_colors.items()},
        sky={k: pal[v] for k, v in style.sky_colors.items()},
        sun=pal[style.sun_color],
        point=pal[style.point_color],
        ray_in=pal[style.ray_incident.color],
        ray_out=pal[style.ray_exit.color],
        pair={k: pal[v] for k, v in style.pair_colors.items()},
        pair_dash=style.pair_dash,
        ink=pal[style.ink_color],
        guide=pal[style.guide_color],
        paper=pal["background"],
        surfaces=surfaces,
        terrain_ramp=tuple(pal[c] for c in style.terrain_ramp),
        crystal_fill=pal[style.crystal_fill.color],
        crystal_fill_alpha=style.crystal_fill.alpha,
        crystal_edge=pal[style.crystal_edge],
        sphere_fill=pal[style.sphere_fill.color],
        sphere_fill_alpha=style.sphere_fill.alpha,
        sphere_edge=pal[style.sphere_edge],
    )


def figure_scheme(**overrides: Any) -> FigureScheme:
    """当前图表语义槽（默认 = #48 定稿：曲面 S1、地形 T3、太阳金）。

    ``**overrides`` 是篇内覆盖的合法入口：键为 :class:`~mapping.SemanticStyleMap`
    的字段名（如 ``sun_color="accent_warm"``、``family_colors={...}``），
    传未知键会就地 ``TypeError``。
    """
    style = DEFAULT_MAP.replace(**overrides) if overrides else DEFAULT_MAP
    return _resolve(style)
