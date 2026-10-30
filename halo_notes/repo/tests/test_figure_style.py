"""插图风格的三道机械闸（task-figure-style-codify Step 5；issue D 节：只拦已证实发生的失误）。

- 闸 1 十六进制字面量（实例：#47 ch9.1 `fig_column_torus.py` 的 `SURFACES`、ch10 `fig_plate_terrain.py`）：
  颜色的唯一权威在 `halo_notes/draw/style/`（palette → mapping → `figure_scheme()`），
  章内再写 hex 就是第二权威（a56）。
- 闸 2 图面裸下标（实例：#47 ch10 图 3c `h_c`、3d `|u_z|` 以未渲染的下划线出图）：
  数学下标一律 mathtext，图面可见文字里不许有 `$...$` 之外的 `_`。
- 闸 3 字号下限（实例：#47 脚注档 ≈10 pt @2300 px ≈ 8 px 显示高，知乎栏内不可读，#48 B.6）：
  显示 px = pt × dpi / 72 × 栏宽 / 图宽，机械折算。

闸 2/3 共用运行时捕获（`halo_notes/repo/figure_audit.py`，逐图独立子进程——签核版出自
regen 的逐图子进程，同进程批量会互相污染 rc）。闸内新章的图加一行 `REGISTRY`
（循 regen 步骤表惯例）；豁免章逐条带原因与解除条件。
"""
from __future__ import annotations

import errno
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from halo_notes.repo.layout import is_chapter_dir

REPO_ROOT = Path(__file__).resolve().parents[3]

# 知乎桌面端正文栏宽假设（未实测；出处 #48 dispositions B.6，作者发布预览时核对一张）。
# 阈值核对后只改这里的常量，不动机制。
COLUMN_WIDTH_PX = 690.0
# 显示高下限：≈ #47 脚注档失误线；#48 签核现状最小 8.2 px。
MIN_DISPLAY_PX = 8.0

# 改革（#49 风格 token + 闸）之前的已发表 / 在制作品：列清单不强改。
# 解除条件：该章插图因其他原因重制时顺手迁移（届时从本表删除）。
EXEMPT_CHAPTERS: dict[str, str] = {
    "00-introduction": "已发表（ch0）",
    "01-symmetry": "已发表（ch1）",
    "02-raypath-enumeration": "已发表（ch2）",
    "03-parallel-raypaths": "已发表（ch3）",
    "04-render-equation": "已发表（ch4）",
    "05-rotation-3d": "已发表（ch5）",
    "06-monte-carlo-vs-integration": "已发表（ch6）",
    "07-reflection-group": "已发表（ch7）",
    "08-wedge-times-fold": "已发表（ch8，2026-09-20）；共享外观已上提 chart.py，其余不动",
    "08.1-tape-vs-matrix": "番外在制（outline），图未起",
    "09-pyramid": "在制（outline），图沿用改革前外观",
}

# 确需越过的文件逐条带理由（当前应为空——有豁免需求时先问「是不是又一个已证实实例」）
HEX_WHITELIST: dict[str, str] = {}

# 闸 2/3 的图清单（新章加一行）：(章, 图脚本 stem, 透传参数)。
# ch10 图 1/7 走 --replot（读 git 内 sky json，不跑 Lumice），回读 gitignored 的原始
# .npy：挂 local_data mark（pytest.param 形态），缺文件时由根 conftest 钩子转 skip。
# pytest 9 未公开 ParameterSet 类型，注解只能写 Any。
REGISTRY: list[tuple[str, str, tuple[str, ...]] | Any] = [
    ("09.1-orientation-space", "fig_axis_angle_ball", ()),
    ("09.1-orientation-space", "fig_column_torus", ()),
    ("09.1-orientation-space", "fig_plate_lowitz", ()),
    ("09.1-orientation-space", "fig_tori_section", ()),
    ("09.1-orientation-space", "fig_euler_sampling", ()),
    ("09.1-orientation-space", "fig_euler_density", ()),
    ("09.1-orientation-space", "fig_sun_rotation", ()),
    ("09.1-orientation-space", "fig_angle_fibers", ()),
    pytest.param("10-radius-and-azimuth", "fig_sky_comparison", ("--replot",),
                 marks=pytest.mark.local_data),
    ("10-radius-and-azimuth", "fig_solar_circle", ()),
    ("10-radius-and-azimuth", "fig_terrain_domain", ()),
    ("10-radius-and-azimuth", "fig_random_terrain", ()),
    ("10-radius-and-azimuth", "fig_plate_terrain", ()),
    ("10-radius-and-azimuth", "fig_column_terrain", ()),
    ("10-radius-and-azimuth", "fig_bravais_prism", ()),
    ("10-radius-and-azimuth", "fig_parhelion_rulers", ()),
    ("10-radius-and-azimuth", "fig_tangent_direction", ()),
    pytest.param("10-radius-and-azimuth", "fig_column_sky", ("--replot",),
                 marks=pytest.mark.local_data),
]

HEX_RE = re.compile(r"""['"]#[0-9a-fA-F]{3,8}['"]""")


def _entry_values(entry: Any) -> tuple:
    """pytest.param(...) 解出底层三元组、普通 tuple 原样返回，供 ids 推导：
    ParameterSet 按 (values, marks, id) 三字段迭代，直接解包会把 marks 当图名。"""
    return tuple(entry.values) if hasattr(entry, "values") else tuple(entry)


def in_scope_chapters() -> list[Path]:
    return sorted(d for d in REPO_ROOT.iterdir()
                  if d.is_dir() and is_chapter_dir(d.name) and d.name not in EXEMPT_CHAPTERS)


def find_hex_literals(text: str) -> list[tuple[int, str]]:
    """返回 (行号, 行内容)：字符串字面量里的十六进制色值。"""
    return [(i + 1, line.strip()) for i, line in enumerate(text.splitlines())
            if HEX_RE.search(line)]


def strip_mathtext(s: str) -> str:
    return re.sub(r"\$[^$]*\$", "", s)


def bare_underscore_texts(records: list[dict]) -> list[str]:
    """闸 2：可见文字里 `$...$` 之外还带 `_` 的。"""
    return [r["t"] for r in records if "_" in strip_mathtext(r["t"])]


def min_display_px(records: list[dict], width_px: float, dpi: float) -> float:
    """闸 3：最小字的知乎栏内显示高（em px）。"""
    scale = dpi / 72 * COLUMN_WIDTH_PX / width_px
    return min(r["pt"] for r in records) * scale


def audit_figure(chapter: str, script_stem: str, args: tuple[str, ...] = ()) -> tuple[dict, Path]:
    """子进程渲染并抓取文字清单；返回 (记录, 输出目录)。

    一律传 ``--output`` 把脚本引向临时目录（sky 图的 sha256 回读等副产物也跟着进 tmp）；
    runner 里另有「落回 checkout 就强制重定向」的保险。
    """
    script = REPO_ROOT / chapter / "code" / f"{script_stem}.py"
    out_png = Path(tempfile.mkdtemp(prefix="figure_audit_")) / f"{script_stem}.png"
    proc = subprocess.run(
        [sys.executable, "-m", "halo_notes.repo.figure_audit", str(script), *args,
         "--output", str(out_png)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        missing = _missing_from_stdout(proc.stdout)
        if missing:
            # 子进程的 FileNotFoundError 跨进程只剩退出码；按 stdout 末行的结构化上报
            # 还原同型异常，交给根 conftest 的 local_data 钩子分类转 skip。
            raise FileNotFoundError(errno.ENOENT, "子进程渲染缺本地数据", missing)
    assert proc.returncode == 0, f"{script_stem} 渲染失败：\n{proc.stderr[-2000:]}"
    return json.loads(proc.stdout.strip().splitlines()[-1]), script.parent


def _missing_from_stdout(stdout: str) -> str | None:
    """子进程 FileNotFoundError 的结构化上报（stdout 末行 JSON 的 ``figure_audit_missing``）；无则 None。"""
    lines = stdout.strip().splitlines()
    if not lines:
        return None
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError:
        return None
    return payload.get("figure_audit_missing") if isinstance(payload, dict) else None


# ---- 闸 1：十六进制字面量 ---------------------------------------------------

def test_gate1_no_hex_literals_in_scope():
    for chapter in in_scope_chapters():
        for path in sorted((chapter / "code").glob("*.py")):   # 不递归 → legacy/ 自动跳过
            rel = str(path.relative_to(REPO_ROOT))
            if rel in HEX_WHITELIST:
                continue
            hits = find_hex_literals(path.read_text())
            assert not hits, f"{rel} 发现十六进制色值字面量（语义请走 figure_scheme；豁免须写进 HEX_WHITELIST 带理由）：{hits}"


def test_gate1_detects_injected_hex(tmp_path):
    """反证：闸 1 对人工注入的 hex 能红。"""
    probe = tmp_path / "fig_probe.py"
    probe.write_text('SURFACES = {"column": "#C9DAEF"}\n')
    assert find_hex_literals(probe.read_text()) == [(1, 'SURFACES = {"column": "#C9DAEF"}')]
    assert find_hex_literals('S = figure_scheme()\ncolor = S.family["plate"]\n') == []


# ---- 闸 2 / 闸 3：运行时捕获 -------------------------------------------------

def test_gate_pure_functions(tmp_path):
    """反证：闸 2/3 的判据函数对人工违例能红、对合法输入不误报。"""
    good = [{"t": "$h_c$ 与 $|u_z|$"}, {"t": "太阳高度 40°"}, {"t": "x 绕 s 扫出的圆"}]
    assert bare_underscore_texts(good) == []
    bad = [{"t": "h_c 与 |u_z|"}, {"t": "半径 r_0"}]
    assert bare_underscore_texts(bad) == ["h_c 与 |u_z|", "半径 r_0"]
    assert min_display_px([{"t": "a", "pt": 11}], width_px=1600, dpi=200) == pytest.approx(11 * 200 / 72 * 690 / 1600)
    assert min_display_px([{"t": "a", "pt": 8}], width_px=2160, dpi=200) < MIN_DISPLAY_PX


@pytest.mark.parametrize("chapter, script_stem, args", REGISTRY,
                         ids=[_entry_values(e)[1] for e in REGISTRY])
def test_gates_2_and_3_figure_text(chapter, script_stem, args):
    """每张注册图：图面文字无裸下标（闸 2）、最小显示高 ≥ 8 px（闸 3）。"""
    record, _ = audit_figure(chapter, script_stem, args)
    texts = record["texts"]
    assert texts, f"{script_stem}: 审计抓不到任何可见文字，harness 失效"
    bare = bare_underscore_texts(texts)
    assert not bare, f"{script_stem}: 图面出现未渲染的下划线（数学下标请用 mathtext）：{bare}"
    lo = min_display_px(texts, record["width_px"], record["dpi"])
    assert lo >= MIN_DISPLAY_PX, (
        f"{script_stem}: 最小字显示高 {lo:.1f} px < {MIN_DISPLAY_PX} px"
        f"（宽 {record['width_px']:.0f} px @ {record['dpi']:.0f} dpi；690 px 栏宽假设待作者发布预览核对）")
