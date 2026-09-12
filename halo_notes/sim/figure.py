"""章级 ``fig_<name>.py`` 的公共骨架：config 落 ``data/<name>.lumice.json``（入 git，"当年参数"的新载体）、
Lumice 原始输出 + provenance 落 ``data/<name>/``（LFS）、正式图落 ``img/<name>.<ext>``。

脚本通过 ``--ray-num`` / ``--out`` 显式覆盖光线数与输出根目录（单测用小光线数跑到临时目录，不碰正式产物）。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .run import RenderResult, render


def parse_args(argv: Sequence[str] | None, *, default_ray_num: int, description: str) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--ray-num", type=int, default=default_ray_num, help=f"全波长总光线数（默认 {default_ray_num:,}）")
    p.add_argument("--out", type=Path, default=None, help="输出根目录（默认章目录：data/ 与 img/ 落在其下）；单测用临时目录")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--backend", default=None)
    return p.parse_args(argv)


def with_ray_num(config: Mapping[str, Any], ray_num: int) -> dict[str, Any]:
    cfg = json.loads(json.dumps(config))
    cfg["scene"]["ray_num"] = int(ray_num)
    return cfg


def sim_figure(name: str, chapter_dir: Path, config: Mapping[str, Any], *, out_root: Path | None = None,
               fmt: str = "png", workers: int | None = None, backend: str | None = None, variant: str | None = None) -> RenderResult:
    """跑一次 Lumice：``data/<name>[.<variant>].lumice.json`` + ``data/<name>[/<variant>]/{img_*, config.json, lumice.log, provenance.json}``。"""
    root = out_root or chapter_dir
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    stem = name if variant is None else f"{name}.{variant}"
    (data_dir / f"{stem}.lumice.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    out_dir = data_dir / name if variant is None else data_dir / name / variant
    return render(config, out_dir, fmt=fmt, workers=workers, backend=backend)


def img_path(name: str, chapter_dir: Path, ext: str, out_root: Path | None = None) -> Path:
    root = out_root or chapter_dir
    (root / "img").mkdir(parents=True, exist_ok=True)
    return root / "img" / f"{name}.{ext}"
