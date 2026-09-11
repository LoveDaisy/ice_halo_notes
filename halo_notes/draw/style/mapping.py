"""风格第二层：语义 → 样式。

每个绘图语义（可见面线、入射光、面编号……）对应一组视觉参数；颜色字段
填的是配色板里的颜色名，不是色值，真正的色值在 :class:`presets.Preset`
组合时才解析。**所有"画成什么样"的数值只住在这一层**——后续切片要加新语义
（高亮面、展开幽灵晶体……）优先在这里加字段，不要新开第五层风格对象。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


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
    family: str | None = None


@dataclass(frozen=True)
class MarkerStyle:
    color: str
    size: float = 4.0       # 直径，pt
    alpha: float = 1.0


@dataclass(frozen=True)
class SemanticStyleMap:
    """语义 → 样式的一整套映射。字段名就是语义名。"""

    edge_visible: LineStyle
    edge_hidden: LineStyle
    face_fill: FillStyle | None          # None 表示不填充
    face_fill_hidden: FillStyle | None
    ray_incident: LineStyle
    ray_internal: LineStyle              # 晶体内部段
    ray_exit: LineStyle
    ray_occluded: LineStyle              # 外部段被晶体挡住的部分
    ray_marker: MarkerStyle              # 光路端点 / 事件点
    ray_marker_hidden: MarkerStyle
    face_number: TextStyle
    face_number_hidden: TextStyle
    axis: LineStyle
    axis_occluded: LineStyle
    axis_label: TextStyle
    annotation: TextStyle

    def replace(self, **changes: Any) -> "SemanticStyleMap":
        return replace(self, **changes)


# 默认映射：以旧图观感为起点——黑线框、背面淡灰、入射红 / 出射蓝
DEFAULT_MAP = SemanticStyleMap(
    edge_visible=LineStyle("ink", linewidth=1.3),
    edge_hidden=LineStyle("ink_faint", linewidth=0.7),
    face_fill=None,
    face_fill_hidden=None,
    ray_incident=LineStyle("accent_warm", linewidth=1.6),
    ray_internal=LineStyle("accent_warm", linewidth=1.6, alpha=0.3),
    ray_exit=LineStyle("accent_cool", linewidth=1.6),
    ray_occluded=LineStyle("accent_warm", linewidth=1.6, alpha=0.3),
    ray_marker=MarkerStyle("accent_warm", size=5.0),
    ray_marker_hidden=MarkerStyle("accent_warm", size=5.0, alpha=0.3),
    face_number=TextStyle("slate", fontsize=26, weight="bold"),
    face_number_hidden=TextStyle("slate", fontsize=26, weight="bold", alpha=0.3),
    axis=LineStyle("accent_warm", linewidth=1.3),
    axis_occluded=LineStyle("accent_warm", linewidth=1.3, alpha=0.2),
    axis_label=TextStyle("ink", fontsize=22, style="italic"),
    annotation=TextStyle("ink", fontsize=14),
)
