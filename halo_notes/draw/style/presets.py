"""风格第四层：预设——把配色板、语义映射、几何风格三者组合成一个可按名取用的对象。

画图脚本只指定预设名；预设负责把样式里的颜色名解析成色值并转成 matplotlib
关键字参数。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .geom_style import DEFAULT_GEOM, GeomStyle
from .mapping import (DEFAULT_MAP, FillStyle, LineStyle, MarkerStyle,
                      SemanticStyleMap, TextStyle)
from .palette import DEFAULT_LIGHT, Palette


@dataclass(frozen=True)
class Preset:
    name: str
    palette: Palette
    style_map: SemanticStyleMap
    geom: GeomStyle

    def replace(self, **changes: Any) -> "Preset":
        return replace(self, **changes)

    # ---- 语义 → matplotlib kwargs -------------------------------------------
    def style(self, semantic: str):
        """按语义名取出映射里的样式对象（未解析颜色）。"""
        return getattr(self.style_map, semantic)

    def line_kwargs(self, semantic: str | LineStyle) -> dict[str, Any]:
        s = self.style(semantic) if isinstance(semantic, str) else semantic
        return dict(color=self.palette[s.color], linewidth=s.linewidth,
                    linestyle=s.linestyle, alpha=s.alpha)

    def fill_kwargs(self, semantic: str | FillStyle | None) -> dict[str, Any] | None:
        s = self.style(semantic) if isinstance(semantic, str) else semantic
        if s is None:
            return None
        return dict(facecolor=self.palette[s.color], alpha=s.alpha, edgecolor="none")

    def text_kwargs(self, semantic: str | TextStyle) -> dict[str, Any]:
        s = self.style(semantic) if isinstance(semantic, str) else semantic
        kw = dict(color=self.palette[s.color], fontsize=s.fontsize, alpha=s.alpha,
                  fontweight=s.weight, fontstyle=s.style)
        if s.family:
            kw["fontfamily"] = list(s.family) if isinstance(s.family, tuple) else s.family
        return kw

    def marker_kwargs(self, semantic: str | MarkerStyle) -> dict[str, Any]:
        s = self.style(semantic) if isinstance(semantic, str) else semantic
        return dict(color=self.palette[s.color], markersize=s.size, alpha=s.alpha,
                    marker="o", linestyle="none")


DEFAULT = Preset("default", DEFAULT_LIGHT, DEFAULT_MAP, DEFAULT_GEOM)

# 0.2 旧图观感：淡蓝半透明填充 + 灰蓝线框，供 fig_crystal03 使用
ICE_FILLED = DEFAULT.replace(
    name="ice_filled",
    style_map=DEFAULT_MAP.replace(
        edge_visible=LineStyle("ice_edge", linewidth=1.3),
        edge_hidden=LineStyle("ice_edge", linewidth=0.7, alpha=0.5),
        face_fill=FillStyle("ice", alpha=0.8),   # 只填可见面：半透明让背面线框/编号隐约透出
        face_fill_hidden=None,
        # 背面编号压在 0.8 的填充之下只透出两成，alpha 要比无填充预设高得多才看得见
        face_number_hidden=replace(DEFAULT_MAP.face_number_hidden, alpha=0.7),
    ),
)

PRESETS: dict[str, Preset] = {p.name: p for p in (DEFAULT, ICE_FILLED)}
