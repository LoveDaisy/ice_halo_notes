"""风格第一层：配色板——颜色名 → 色值。

颜色名是"这块颜料叫什么"（ink / ice / accent_warm），不是"用在哪"；
"用在哪"由第二层 :mod:`mapping` 决定。换主题只换这一层。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Palette:
    name: str
    colors: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "colors", MappingProxyType(dict(self.colors)))

    def __getitem__(self, name: str) -> str:
        try:
            return self.colors[name]
        except KeyError:
            raise KeyError(f"palette {self.name!r} has no color {name!r}") from None

    def __contains__(self, name: str) -> bool:
        return name in self.colors

    def with_colors(self, name: str | None = None, **overrides: str) -> "Palette":
        """派生一套只改若干颜色的新配色板。"""
        return Palette(name or self.name, {**self.colors, **overrides})


# 浅色主题：色值取自旧图（4.1 / 3.3 / 0.2）的主色采样
DEFAULT_LIGHT = Palette("default_light", {
    "background": "#FFFFFF",
    "ink": "#000000",          # 可见线框
    "ink_faint": "#CCCCCC",    # 不可见线框
    "ice": "#D5EFFD",          # 晶体填充（0.2 旧图）
    "ice_edge": "#767B8B",     # 0.2 旧图的灰蓝线框
    "slate": "#848897",        # 面编号
    "accent_warm": "#FC5D53",  # 入射光 / 坐标轴（4.1 / 3.3 旧图的珊瑚红）
    "accent_cool": "#3C7DD9",  # 出射光
    "highlight": "#F8E66F",    # 高亮面（2.5 旧图光走廊的黄色填充）
    # 侧面 3–8 的固定配色（1.3 / 1.6 旧图采样：读者靠颜色追踪同一个面）
    "face_3": "#E95536",       # 红
    "face_4": "#5E81B5",       # 蓝
    "face_5": "#E19C24",       # 橙
    "face_6": "#8FB032",       # 绿
    "face_7": "#EB6235",       # 橙红
    "face_8": "#8778B3",       # 紫
    "reference": "#D6DCE6",    # 对称操作的参考幽灵线框 / 弧箭头 / 翻转轴（1.3 / 1.6 旧图的淡灰蓝）
    "plate": "#DCE4F5",        # 6.2 平板填充（旧图采样）
    "plate_edge": "#5B6FB0",   # 6.2 平板界面线
    "medium": "#D3D3D3",       # 3.1 楔形介质填充（旧图灰）
})

# 面号 → 颜色名：挂到 ``SemanticStyleMap.face_number_colors`` 上即启用"按面号取色"
FACE_COLORS: dict[int, str] = {k: f"face_{k}" for k in range(3, 9)}
