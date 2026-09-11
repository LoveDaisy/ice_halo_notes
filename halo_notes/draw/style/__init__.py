"""风格四层：palette（颜色名→色值）→ mapping（语义→样式）→ geom_style（几何参数）→ presets（组合）。"""

from .geom_style import DEFAULT_GEOM, GeomStyle, HiddenEdgeMode
from .mapping import (DEFAULT_MAP, FillStyle, LineStyle, MarkerStyle,
                      SemanticStyleMap, TextStyle)
from .palette import DEFAULT_LIGHT, Palette
from .presets import DEFAULT, ICE_FILLED, PRESETS, Preset

__all__ = [
    "DEFAULT", "DEFAULT_GEOM", "DEFAULT_LIGHT", "DEFAULT_MAP", "FillStyle",
    "GeomStyle", "HiddenEdgeMode", "ICE_FILLED", "LineStyle", "MarkerStyle",
    "PRESETS", "Palette", "Preset", "SemanticStyleMap", "TextStyle",
]
