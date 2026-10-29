<!-- 由 halo_notes/draw/style/table.py 生成；改 token 后重跑该生成器。勿手改。 -->
# 插图颜色对照表（由代码生成）

语义的权威是 `halo_notes/draw/style/mapping.py`，颜料的权威是 `palette.py`；
取色入口 `figure_scheme()`（默认 = #48 定稿：曲面 S1、地形 T3、太阳金）。
版式约定的正文见 `docs/figure-style.md`。

## 颜料（palette `DEFAULT_LIGHT`）

| 颜料名 | 色值 |
|---|---|
| `background` | `#FFFFFF` |
| `ink` | `#000000` |
| `ink_faint` | `#CCCCCC` |
| `ice` | `#D5EFFD` |
| `ice_edge` | `#767B8B` |
| `slate` | `#848897` |
| `accent_warm` | `#FC5D53` |
| `accent_cool` | `#3C7DD9` |
| `highlight` | `#F8E66F` |
| `face_3` | `#E95536` |
| `face_4` | `#5E81B5` |
| `face_5` | `#E19C24` |
| `face_6` | `#8FB032` |
| `face_7` | `#EB6235` |
| `face_8` | `#8778B3` |
| `reference` | `#D6DCE6` |
| `plate` | `#DCE4F5` |
| `plate_edge` | `#5B6FB0` |
| `medium` | `#D3D3D3` |
| `ink_soft` | `#455775` |
| `arc_roll` | `#4E78BE` |
| `arc_tilt` | `#8CB43C` |
| `arc_azimuth` | `#E6AA32` |
| `grid` | `#9A9A9A` |
| `cloud` | `#555555` |
| `sphere_curve` | `#5E81B5` |
| `cone` | `#BFBFBF` |
| `sample_1` | `#8E44AD` |
| `sample_2` | `#E67E22` |
| `sample_3` | `#16A085` |
| `gold` | `#E8A020` |
| `navy` | `#2E4B7E` |
| `stone` | `#8C96A3` |
| `coral_pale` | `#F2917C` |
| `mist` | `#D2D6DC` |
| `charcoal` | `#2F3A4A` |
| `haze` | `#C9CFD8` |
| `fog` | `#F3F4F6` |
| `stone_light` | `#A3ABB7` |
| `glacier` | `#C9DAEF` |
| `glacier_mesh` | `#6F88AE` |
| `glacier_deep` | `#3E5A86` |
| `blush` | `#F8E4DE` |
| `blush_mesh` | `#C79A8E` |
| `blush_deep` | `#9A6556` |
| `frost` | `#E3EEF8` |
| `frost_mesh` | `#7D8DA3` |
| `frost_deep` | `#56677D` |

## 图表语义槽（`figure_scheme()` 默认值）

| 槽 | mapping 来源 → 颜料名 | 色值 |
|---|---|---|
| `family.random` | `family_colors["random"]` → `stone` | `#8C96A3` |
| `family.column` | `family_colors["column"]` → `arc_roll` | `#4E78BE` |
| `family.parry` | `family_colors["parry"]` → `navy` | `#2E4B7E` |
| `family.plate` | `family_colors["plate"]` → `face_3` | `#E95536` |
| `family.lowitz` | `family_colors["lowitz"]` → `coral_pale` | `#F2917C` |
| `sky_glow.random` | `sky_glow_colors["random"]` → `mist` | `#D2D6DC` |
| `sky_glow.column` | `sky_glow_colors["column"]` → `accent_cool` | `#3C7DD9` |
| `sky_glow.plate` | `sky_glow_colors["plate"]` → `face_3` | `#E95536` |
| `sky.ink` | `sky_colors["ink"]` → `ink_faint` | `#CCCCCC` |
| `sky.ring` | `sky_colors["ring"]` → `slate` | `#848897` |
| `sky.guide` | `sky_colors["guide"]` → `cloud` | `#555555` |
| `sky.night` | `sky_colors["night"]` → `ink` | `#000000` |
| `sun` | `sun_color` → `gold` | `#E8A020` |
| `point` | `point_color` → `accent_cool`（出射光反向，语义同源） | `#3C7DD9` |
| `ray_in` | 沿用既有光线语义 `ray_incident` → `accent_warm` | `#FC5D53` |
| `ray_out` | 沿用既有光线语义 `ray_exit` → `accent_cool` | `#3C7DD9` |
| `pair.a` | `pair_colors["a"]` → `charcoal`（实线） | `#2F3A4A` |
| `pair.b` | `pair_colors["b"]` → `face_8`（虚线 `pair_dash`） | `#8778B3` |
| `ink` | `ink_color` → `ink_soft`（图面文字 / 引线） | `#455775` |
| `guide` | `guide_color` → `haze`（经纬网 / 辅助线） | `#C9CFD8` |
| `paper` | palette `background` | `#FFFFFF` |
| `terrain_ramp` | `terrain_ramp`（明度单调） | `#F3F4F6` → `#A3ABB7` → `#2F3A4A` |
| `crystal_fill` | `crystal_fill` → `ice`，alpha=0.8 | `#D5EFFD` |
| `crystal_edge` | `crystal_edge` → `ice_edge` | `#767B8B` |
| `sphere_fill` | `sphere_fill` → `ice`，alpha=0.24 | `#D5EFFD` |
| `sphere_edge` | `sphere_edge` → `ice_edge` | `#767B8B` |

## 着色曲面（`SurfaceStyle`）

| 曲面 | base（底色） | ambient | mesh（半宽） | outline |
|---|---|---|---|---|
| `surfaces.column` | `#C9DAEF` → `glacier` | 0.8 | `#6F88AE` (0.0042) | `#3E5A86` |
| `surfaces.lowitz` | `#F8E4DE` → `blush` | 0.84 | `#C79A8E` (0.0042) | `#9A6556` |
| `surfaces.neutral` | `#E3EEF8` → `frost` | 0.84 | `#7D8DA3` (0.004) | `#56677D` |

## 篇内覆盖

颜色-语义一致的作用域是**篇内**（作者 2026-10-30 裁定）：新章默认用上表，
篇内需要不同取色时经 `figure_scheme(**overrides)` 覆盖 mapping 字段，不做全系列硬映射。
