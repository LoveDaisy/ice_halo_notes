"""生成 docs/figure-style-colors.md：颜料表 + 图表语义槽表，色值现场从 palette / mapping 读。

文档不手抄色值（避免两份实现）：token 变了重跑本生成器，
``halo_notes/draw/tests/test_style_tokens.py`` 的 freshness 测试比对生成物。
用法：``uv run python -m halo_notes.draw.style.table [输出路径，默认 docs/figure-style-colors.md]``
"""
from __future__ import annotations

import sys
from pathlib import Path

from .figure import figure_scheme
from .mapping import DEFAULT_MAP
from .palette import DEFAULT_LIGHT

REPO_ROOT = Path(__file__).resolve().parents[3]


def _swatch(hex_value: str) -> str:
    return f'`{hex_value}`'


def generate() -> str:
    """渲染整份 markdown 文本（供 freshness 测试逐字节比对）。"""
    s = figure_scheme()
    lines = [
        "<!-- 由 halo_notes/draw/style/table.py 生成；改 token 后重跑该生成器。勿手改。 -->",
        "# 插图颜色对照表（由代码生成）",
        "",
        "语义的权威是 `halo_notes/draw/style/mapping.py`，颜料的权威是 `palette.py`；",
        "取色入口 `figure_scheme()`（默认 = #48 定稿：曲面 S1、地形 T3、太阳金）。",
        "版式约定的正文见 `docs/figure-style.md`。",
        "",
        "## 颜料（palette `DEFAULT_LIGHT`）",
        "",
        "| 颜料名 | 色值 |",
        "|---|---|",
    ]
    for name, hex_value in DEFAULT_LIGHT.colors.items():
        lines.append(f"| `{name}` | {_swatch(hex_value)} |")
    lines += [
        "",
        "## 图表语义槽（`figure_scheme()` 默认值）",
        "",
        "| 槽 | mapping 来源 → 颜料名 | 色值 |",
        "|---|---|---|",
    ]
    for key, pigment in DEFAULT_MAP.family_colors.items():
        lines.append(f"| `family.{key}` | `family_colors[\"{key}\"]` → `{pigment}` | {_swatch(s.family[key])} |")
    for key, pigment in DEFAULT_MAP.sky_glow_colors.items():
        lines.append(f"| `sky_glow.{key}` | `sky_glow_colors[\"{key}\"]` → `{pigment}` | {_swatch(s.sky_glow[key])} |")
    for key, pigment in DEFAULT_MAP.sky_colors.items():
        lines.append(f"| `sky.{key}` | `sky_colors[\"{key}\"]` → `{pigment}` | {_swatch(s.sky[key])} |")
    lines += [
        f"| `sun` | `sun_color` → `{DEFAULT_MAP.sun_color}` | {_swatch(s.sun)} |",
        f"| `point` | `point_color` → `{DEFAULT_MAP.point_color}`（出射光反向，语义同源） | {_swatch(s.point)} |",
        f"| `ray_in` | 沿用既有光线语义 `ray_incident` → `{DEFAULT_MAP.ray_incident.color}` | {_swatch(s.ray_in)} |",
        f"| `ray_out` | 沿用既有光线语义 `ray_exit` → `{DEFAULT_MAP.ray_exit.color}` | {_swatch(s.ray_out)} |",
        f"| `pair.a` | `pair_colors[\"a\"]` → `{DEFAULT_MAP.pair_colors['a']}`（实线） | {_swatch(s.pair['a'])} |",
        f"| `pair.b` | `pair_colors[\"b\"]` → `{DEFAULT_MAP.pair_colors['b']}`（虚线 `pair_dash`） | {_swatch(s.pair['b'])} |",
        f"| `ink` | `ink_color` → `{DEFAULT_MAP.ink_color}`（图面文字 / 引线） | {_swatch(s.ink)} |",
        f"| `guide` | `guide_color` → `{DEFAULT_MAP.guide_color}`（经纬网 / 辅助线） | {_swatch(s.guide)} |",
        f"| `paper` | palette `background` | {_swatch(s.paper)} |",
        "| `terrain_ramp` | `terrain_ramp`（明度单调） | "
        + " → ".join(_swatch(v) for v in s.terrain_ramp) + " |",
        f"| `crystal_fill` | `crystal_fill` → `{DEFAULT_MAP.crystal_fill.color}`，alpha={DEFAULT_MAP.crystal_fill.alpha} | {_swatch(s.crystal_fill)} |",
        f"| `crystal_edge` | `crystal_edge` → `{DEFAULT_MAP.crystal_edge}` | {_swatch(s.crystal_edge)} |",
        f"| `sphere_fill` | `sphere_fill` → `{DEFAULT_MAP.sphere_fill.color}`，alpha={DEFAULT_MAP.sphere_fill.alpha} | {_swatch(s.sphere_fill)} |",
        f"| `sphere_edge` | `sphere_edge` → `{DEFAULT_MAP.sphere_edge}` | {_swatch(s.sphere_edge)} |",
        "",
        "## 着色曲面（`SurfaceStyle`）",
        "",
        "| 曲面 | base（底色） | ambient | mesh（半宽） | outline |",
        "|---|---|---|---|---|",
    ]
    for key in DEFAULT_MAP.surface_styles:
        surf = s.surfaces[key]
        style = DEFAULT_MAP.surface_styles[key]
        lines.append(f"| `surfaces.{key}` | {_swatch(surf.base)} → `{style.base}` | {surf.ambient} | "
                     f"{_swatch(surf.mesh)} ({surf.mesh_width}) | {_swatch(surf.outline)} |")
    lines += [
        "",
        "## 篇内覆盖",
        "",
        "颜色-语义一致的作用域是**篇内**（作者 2026-10-30 裁定）：新章默认用上表，",
        "篇内需要不同取色时经 `figure_scheme(**overrides)` 覆盖 mapping 字段，不做全系列硬映射。",
        "",
    ]
    return "\n".join(lines)


def main(out: str | None = None) -> Path:
    path = Path(out) if out is not None else REPO_ROOT / "docs" / "figure-style-colors.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate())
    print(path)
    return path


if __name__ == "__main__":
    main(*sys.argv[1:2])
