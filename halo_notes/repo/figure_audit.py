"""图面审计 runner：子进程内渲染一张注册图，抓取 savefig 时刻的全部可见文字。

供 ``halo_notes/repo/tests/test_figure_style.py`` 的闸 2（裸下标）/ 闸 3（字号下限）使用：
逐图独立子进程（签核版出自 regen 的逐图子进程，同进程批量会互相污染 rc——learnings）。
savefig 目标一律重定向到临时目录：闸只读不写，绝不碰正式 `img/` 与 `data/`。
用法：``python -m halo_notes.repo.figure_audit <fig脚本路径> [透传参数...]``，stdout 末行是 JSON：
``{"texts": [{"t": str, "pt": float}...], "width_px": float, "dpi": float}``（只含可见非空 Text）。
"""
from __future__ import annotations

import json
import runpy
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.text import Text  # noqa: E402


def main() -> None:
    script = Path(sys.argv[1])
    chapter = script.parent.parent          # <章>/code/<fig>.py → <章>/
    out_dir = Path(tempfile.mkdtemp(prefix="figure_audit_"))
    record: dict = {}
    original = Figure.savefig

    def capture(fig, fname, *args, **kwargs):
        fname = Path(str(fname))
        # 调用方应已传 --output 把脚本引向临时目录；这里是保险：目标若落回 checkout 内则强制重定向。
        if chapter.resolve() in fname.resolve().parents:
            fname = out_dir / fname.name
        original(fig, fname, *args, **kwargs)
        dpi = kwargs.get("dpi", fig.dpi)
        record["width_px"] = fig.get_figwidth() * dpi
        record["dpi"] = dpi
        record["texts"] = [
            {"t": t.get_text(), "pt": t.get_fontsize()}
            for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()
        ]

    Figure.savefig = capture
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *sys.argv[2:]]
    runpy.run_path(str(script), run_name="__main__")
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
