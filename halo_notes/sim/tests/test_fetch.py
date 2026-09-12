"""fetch.py 单测：不真下载——用假 tarball fixture + monkeypatch 掉网络。"""

from __future__ import annotations

import io
import os
import tarfile
from pathlib import Path

import pytest

from halo_notes.sim import fetch


def _fake_tarball(path: Path, *, with_binary: bool = True) -> Path:
    with tarfile.open(path, "w:gz") as tar:
        def add(name: str, data: bytes) -> None:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        add("include/lumice.h", b"// header")
        add("lib/liblumice.a", b"\x00" * 8)
        add("LumiceGUI.app/Contents/MacOS/LumiceGUI", b"#!/bin/sh\n")
        if with_binary:
            add("Lumice", b"#!/bin/sh\necho fake lumice\n")
    return path


@pytest.fixture
def cache(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "CACHE_DIR", tmp_path / ".lumice")
    monkeypatch.delenv("LUMICE_BIN", raising=False)
    return tmp_path


def test_lumice_bin_env_has_top_priority(cache, monkeypatch, tmp_path):
    override = tmp_path / "my-lumice"
    override.write_text("#!/bin/sh\n")
    monkeypatch.setenv("LUMICE_BIN", str(override))
    monkeypatch.setattr(fetch, "download", lambda *a, **k: pytest.fail("不该下载"))
    assert fetch.ensure_lumice() == override


def test_lumice_bin_env_missing_file_raises(cache, monkeypatch, tmp_path):
    monkeypatch.setenv("LUMICE_BIN", str(tmp_path / "nope"))
    with pytest.raises(FileNotFoundError):
        fetch.ensure_lumice()


def test_cache_hit_skips_download(cache, monkeypatch):
    target = fetch.cached_binary()
    target.parent.mkdir(parents=True)
    target.write_text("#!/bin/sh\n")
    monkeypatch.setattr(fetch, "download", lambda *a, **k: pytest.fail("缓存命中不该下载"))
    assert fetch.ensure_lumice() == target


def test_download_extracts_only_binary(cache, monkeypatch, tmp_path):
    fake = _fake_tarball(tmp_path / "asset.tar.gz")
    calls: list[str] = []

    def fake_download(url: str, dest: Path) -> None:
        calls.append(url)
        dest.write_bytes(fake.read_bytes())

    monkeypatch.setattr(fetch, "download", fake_download)
    monkeypatch.setattr(fetch, "platform_tag", lambda *a, **k: "macos-arm64")
    path = fetch.ensure_lumice()
    assert path == fetch.CACHE_DIR / fetch.LUMICE_VERSION / "Lumice"
    assert calls == [f"https://github.com/LoveDaisy/ice_halo_sim/releases/download/{fetch.LUMICE_VERSION}/lumice-{fetch.LUMICE_VERSION}-macos-arm64.tar.gz"]
    assert os.access(path, os.X_OK)
    assert sorted(p.name for p in path.parent.iterdir()) == ["Lumice"]  # include/ lib/ GUI 都没落地


def test_tarball_without_binary_raises(cache, monkeypatch, tmp_path):
    fake = _fake_tarball(tmp_path / "asset.tar.gz", with_binary=False)
    monkeypatch.setattr(fetch, "download", lambda url, dest: dest.write_bytes(fake.read_bytes()))
    monkeypatch.setattr(fetch, "platform_tag", lambda *a, **k: "macos-arm64")
    with pytest.raises(RuntimeError, match="没有 Lumice"):
        fetch.ensure_lumice()


def test_download_failure_is_explicit(cache, monkeypatch):
    monkeypatch.setattr(fetch, "platform_tag", lambda *a, **k: "macos-arm64")

    def boom(url, dest):
        raise RuntimeError(f"下载 Lumice release 资产失败：{url}")

    monkeypatch.setattr(fetch, "download", boom)
    with pytest.raises(RuntimeError, match="下载 Lumice release 资产失败"):
        fetch.ensure_lumice()
    assert not fetch.cached_binary().exists()


@pytest.mark.parametrize("machine,system", [("x86_64", "darwin"), ("arm64", "linux"), ("AMD64", "win32")])
def test_unsupported_platform(machine, system):
    with pytest.raises(NotImplementedError):
        fetch.platform_tag(machine, system)


def test_supported_platform():
    assert fetch.platform_tag("arm64", "darwin") == "macos-arm64"
