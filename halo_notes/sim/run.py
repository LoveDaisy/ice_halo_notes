"""调 Lumice CLI：写 ``config.json`` → ``subprocess.run`` → 收图 + ``lumice.log`` + ``provenance.json``。

``provenance.json`` 是可复现性契约（Lumice 版本 / 二进制 sha256 / config sha256 / 墙钟 / 平台 / workers / backend / 命令行），
图像本身只留本地（git 只收 config / provenance / log，见 AGENTS.md「数据约定」），二进制走 ``.lumice/``（gitignore），三者职责不重叠。
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .fetch import LUMICE_VERSION, ensure_lumice, sha256_of

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".npy")
FORMATS = ("png", "jpg", "npy")
# Lumice 的 `--backend metal` 不可用时会静默回落 CPU；真走了 Metal 时日志里同时有这两句（v4.6.1 实测）
METAL_MARKERS = ("routing via MetalTraceBackend", "gpu_route=true")


class LumiceError(RuntimeError):
    """Lumice 非零退出；message 带 log 尾部。"""


@dataclass
class RenderResult:
    images: list[Path]
    provenance: dict[str, Any]
    wall_clock_s: float
    out_dir: Path
    config_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.config_path = self.out_dir / "config.json"


def config_sha256(config: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render(
    config: Mapping[str, Any],
    out_dir: Path | str,
    *,
    fmt: str = "png",
    workers: int | None = None,
    backend: str | None = None,
    timeout: float | None = None,
    quality: int | None = None,
    bin: Path | None = None,
) -> RenderResult:
    """跑一次 Lumice。``out_dir`` 会被创建；图片按 Lumice 命名（``img_01.<fmt>`` …，与 ``render`` 段顺序一致）。
    ``fmt="npy"`` 得到未曝光的线性 XYZ 累加器 ``(H, W, 3)``，同名 ``img_XX.json`` sidecar（含 ``emitted_energy``）由 Lumice 写在旁边。
    ``backend="metal"`` 时核对日志确实走了 Metal，没走（静默回落 CPU）抛 :class:`LumiceError`；结果记入 ``provenance["gpu_route"]``。"""
    if fmt not in FORMATS:
        raise ValueError(f"fmt 只能是 {'/'.join(FORMATS)}，收到 {fmt!r}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = Path(bin) if bin is not None else ensure_lumice()
    cfg_path = out_dir / "config.json"
    cfg_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")

    # out_dir 归本次渲染独占：先清掉上次的图，免得旧图（尤其上次 render 段更长时多出来的）混进结果
    for stale in out_dir.iterdir():
        if stale.suffix.lower() in IMAGE_SUFFIXES:
            stale.unlink()
    cmd = [str(binary), "-f", str(cfg_path), "-o", str(out_dir), "--format", fmt]
    if workers is not None:
        cmd += ["--workers", str(workers)]
    if backend is not None:
        cmd += ["--backend", backend]
    if quality is not None:
        cmd += ["--quality", str(quality)]

    t0 = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    wall = time.monotonic() - t0
    log_path = out_dir / "lumice.log"
    log = f"$ {' '.join(cmd)}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    log_path.write_text(log.rstrip() + "\n")
    if proc.returncode != 0:
        tail = "\n".join(log_path.read_text().splitlines()[-30:])
        raise LumiceError(f"Lumice 退出码 {proc.returncode}（命令 {' '.join(cmd)}）；log 尾部：\n{tail}")

    gpu_route = all(m in proc.stdout + proc.stderr for m in METAL_MARKERS)
    if backend == "metal" and not gpu_route:
        raise LumiceError(f"要求 --backend metal，但日志里没有走 Metal（回落 CPU？），见 {log_path}")

    images = sorted(p for p in out_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        raise LumiceError(f"Lumice 退出码 0 但 {out_dir} 下没有新图片；log：{log_path}")

    provenance = {
        "lumice_version": LUMICE_VERSION,
        "lumice_bin": str(binary),
        "lumice_bin_sha256": sha256_of(binary),
        "config_sha256": config_sha256(config),
        "wall_clock_s": round(wall, 3),
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "workers": workers,
        "backend": backend,
        "gpu_route": gpu_route,
        "format": fmt,
        "cli_args": cmd[1:],
        "images": [p.name for p in images],
        "ray_num": config.get("scene", {}).get("ray_num"),
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    return RenderResult(images=images, provenance=provenance, wall_clock_s=wall, out_dir=out_dir)


def load_provenance(out_dir: Path | str) -> dict[str, Any]:
    return json.loads((Path(out_dir) / "provenance.json").read_text())
