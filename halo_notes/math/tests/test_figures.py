"""跑本库支撑的 6 个 fig 脚本（ch1 1.4 / 1.7，ch5 5.2–5.5），让脚本内嵌的机械自检真的执行，并白盒核对画出的内容：
表格图逐格与旧图转录一致、直方图脚本的样本 / L1 距离、5.4 的 16 点误差断言。``Figure.savefig`` 被空操作掉，不覆盖 img/。"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.axes  # noqa: E402
import matplotlib.figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from halo_notes.math.density import l1_distance, s2_nearest_neighbor_pdf, s3_nearest_neighbor_pdf  # noqa: E402
from halo_notes.math.group import elements, latex  # noqa: E402
from halo_notes.math.tests.test_density import numerical_error_assertions  # noqa: E402
from halo_notes.math.tests.test_group import TABLE_1_4, TABLE_1_7, parse  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CH1, CH5 = ROOT / "01-symmetry/code", ROOT / "05-rotation-3d/code"
SCRIPTS = {
    "1.4": CH1 / "fig_c6_table.py",
    "1.7": CH1 / "fig_d6_table_shade.py",
    "5.2": CH5 / "fig_slerp_factor_explanation.py",
    "5.3": CH5 / "fig_hist01.py",
    "5.4": CH5 / "fig_numerical_err.py",
    "5.5": CH5 / "fig_hist02.py",
}


def run_script(path: Path, monkeypatch, capsys) -> dict:
    """像命令行那样跑脚本（脚本目录进 sys.path 以便 import 章内 helper），返回模块命名空间。"""
    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", lambda self, *a, **k: None)
    monkeypatch.syspath_prepend(str(path.parent))
    for name in ("group_table", "matlab_style"):
        sys.modules.pop(name, None)   # 两章各有自己的 helper，别串
    ns = runpy.run_path(str(path), run_name="__main__")
    plt.close("all")
    capsys.readouterr()
    return ns


@pytest.mark.parametrize("key", list(SCRIPTS))
def test_script_runs_with_its_own_assertions(key, monkeypatch, capsys):
    run_script(SCRIPTS[key], monkeypatch, capsys)


def drawn_table(path: Path, monkeypatch, capsys) -> list[list[str]]:
    """抓脚本实际 ``ax.text`` 到每个格子的字符串，按格坐标（单位 = 一格，y 向下）重组成 (n+1)×(n+1) 表。"""
    cells: dict[tuple[int, int], str] = {}
    original = matplotlib.axes.Axes.text

    def spy(self, x, y, s, *a, **k):
        cells[(int(y), int(x))] = s
        return original(self, x, y, s, *a, **k)

    monkeypatch.setattr(matplotlib.axes.Axes, "text", spy)
    run_script(path, monkeypatch, capsys)
    n = max(r for r, _ in cells) + 1
    assert set(cells) == {(r, c) for r in range(n) for c in range(n)} - {(0, 0)}
    return [[cells[(r, c)] for c in range(1, n)] for r in range(1, n)], [cells[(0, c)] for c in range(1, n)]


@pytest.mark.parametrize("key, transcription, count", [("1.4", TABLE_1_4, 6), ("1.7", TABLE_1_7, 12)])
def test_table_scripts_draw_the_published_tables(key, transcription, count, monkeypatch, capsys):
    """1.4 / 1.7 画上去的每一格（含表头）= 旧图转录（经 latex() 转成画出的记号）。"""
    body, header = drawn_table(SCRIPTS[key], monkeypatch, capsys)
    by_name = {g.name: latex(g) for g in elements()}
    assert header == [latex(g) for g in elements()[:count]]
    assert body == [[by_name[n] for n in row] for row in parse(transcription)]


def test_hist_scripts_samples_match_pdf(monkeypatch, capsys):
    ns = run_script(SCRIPTS["5.3"], monkeypatch, capsys)
    dm = ns["sample"](np.random.default_rng(ns["SEED"]))
    assert dm.shape == (ns["PTS_NUM"] * ns["REP_NUM"],)
    edges = np.linspace(0, np.sqrt(4 / ns["PTS_NUM"]) * 3, 101)
    c = (edges[:-1] + edges[1:]) / 2
    h, _ = np.histogram(dm, edges, density=True)
    assert l1_distance(h, s2_nearest_neighbor_pdf(c, ns["PTS_NUM"]), edges[1] - edges[0]) < ns["L1_THRESHOLD"]

    ns = run_script(SCRIPTS["5.5"], monkeypatch, capsys)
    dm = ns["sample"](np.random.default_rng(ns["SEED"]))
    assert dm.shape == (2 * ns["PTS_NUM"] * ns["REP_NUM"],)
    edges = np.linspace(0, (4 / ns["PTS_NUM"]) ** 0.33 * 2, 101)
    c = (edges[:-1] + edges[1:]) / 2
    h, _ = np.histogram(dm, edges, density=True)
    assert l1_distance(h, s3_nearest_neighbor_pdf(c, 2 * ns["PTS_NUM"]), edges[1] - edges[0]) < ns["L1_THRESHOLD"]


def test_numerical_err_script_points(monkeypatch, capsys):
    ns = run_script(SCRIPTS["5.4"], monkeypatch, capsys)
    num, err_power, err_exp = ns["errors"]()
    numerical_error_assertions(num, err_power, err_exp)
    assert np.allclose(np.log10(num), np.arange(4, 7.01, 0.2))
