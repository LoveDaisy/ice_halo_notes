"""按钉住的版本号从 GitHub release 拉 Lumice CLI 二进制（不入 git，落 ``<repo>/.lumice/<version>/Lumice``）。

``python -m halo_notes.sim.fetch`` 打印二进制路径与 sha256；删掉 ``.lumice/`` 后重跑应得到同一 sha256。
"""

from __future__ import annotations

import hashlib
import os
import platform
import stat
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

LUMICE_VERSION = "v4.6.1"  # 唯一权威常量；升级只改这里
LUMICE_REPO = "LoveDaisy/ice_halo_sim"
BIN_NAME = "Lumice"

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / ".lumice"


def platform_tag(machine: str | None = None, system: str | None = None) -> str:
    """把 ``platform.machine()`` / ``sys.platform`` 映射成 release 资产名里的平台段；只认 macOS arm64。"""
    machine = machine if machine is not None else platform.machine()
    system = system if system is not None else sys.platform
    if system == "darwin" and machine == "arm64":
        return "macos-arm64"
    raise NotImplementedError(
        f"只支持 macOS arm64 的 Lumice release 资产，当前平台 {system}/{machine}；"
        f"其他平台请自行编译并用 LUMICE_BIN 环境变量指过去"
    )


def asset_url(version: str = LUMICE_VERSION, tag: str | None = None) -> str:
    tag = tag or platform_tag()
    return f"https://github.com/{LUMICE_REPO}/releases/download/{version}/lumice-{version}-{tag}.tar.gz"


def download(url: str, dest: Path) -> None:
    """下载到 ``dest``；网络 / HTTP 错误原样抛出（带 url 上下文），不静默回退。"""
    try:
        with urllib.request.urlopen(url, timeout=60) as resp, dest.open("wb") as fh:
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
    except Exception as exc:  # noqa: BLE001 —— 统一加 url 上下文再抛
        raise RuntimeError(f"下载 Lumice release 资产失败：{url}") from exc


def extract_binary(tarball: Path, dest: Path) -> None:
    """只从 tarball 里抽 ``Lumice`` 单文件到 ``dest``（忽略 ``include/`` ``lib/`` ``LumiceGUI.app/``）。"""
    with tarfile.open(tarball, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile() and Path(m.name).name == BIN_NAME and "/" not in m.name.strip("./")]
        if not members:
            names = [m.name for m in tar.getmembers()][:20]
            raise RuntimeError(f"tarball 顶层没有 {BIN_NAME} 可执行文件：{tarball}；前 20 个成员 {names}")
        src = tar.extractfile(members[0])
        assert src is not None
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            fh.write(src.read())
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if not os.access(dest, os.X_OK):
        raise RuntimeError(f"chmod +x 后仍不可执行：{dest}")


def cached_binary(version: str = LUMICE_VERSION) -> Path:
    return CACHE_DIR / version / BIN_NAME


def ensure_lumice(version: str = LUMICE_VERSION) -> Path:
    """返回可用的 Lumice 二进制路径：``LUMICE_BIN`` 环境变量 > 本地缓存 > 下载。"""
    override = os.environ.get("LUMICE_BIN")
    if override:
        path = Path(override)
        if not path.is_file():
            raise FileNotFoundError(f"LUMICE_BIN 指向的文件不存在：{path}")
        return path
    target = cached_binary(version)
    if target.is_file():
        return target
    url = asset_url(version)
    with tempfile.TemporaryDirectory() as tmp:
        tarball = Path(tmp) / "lumice.tar.gz"
        download(url, tarball)
        extract_binary(tarball, target)
    return target


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    path = ensure_lumice()
    print(f"{path}\nsha256 {sha256_of(path)}")


if __name__ == "__main__":
    main()
