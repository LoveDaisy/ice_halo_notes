"""pre-push 体积闸端到端：临时 bare 远端 + 临时仓，装上 tools/hooks/install.sh 生成的包装，用桩 git-lfs 记录它收到的 stdin。"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from halo_notes.repo import layout as L

ROOT = L.REPO_ROOT
GITATTR = "*.png filter=lfs diff=lfs merge=lfs -text\n*.jpg filter=lfs diff=lfs merge=lfs -text\n"


def git(repo: Path, *args: str, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=check)


def write(repo: Path, rel: str, data: str | bytes = "x") -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data) if isinstance(data, bytes) else p.write_text(data, encoding="utf-8")


def commit(repo: Path, msg: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg)


@pytest.fixture
def env(tmp_path: Path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for k, v in [("user.email", "t@t"), ("user.name", "t"), ("filter.lfs.clean", "cat"), ("filter.lfs.smudge", "cat"),
                 ("filter.lfs.process", ""), ("filter.lfs.required", "false"), ("core.hooksPath", str(repo / ".git" / "hooks"))]:
        git(repo, "config", k, v)
    git(repo, "remote", "add", "origin", str(remote))
    for rel in ["halo_notes/__init__.py", "halo_notes/repo/__init__.py", "halo_notes/repo/layout.py",
                "tools/hooks/pre-push", "tools/hooks/install.sh"]:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, repo / rel)
    write(repo, ".gitattributes", GITATTR)
    write(repo, "01-a/正文.md", "![a](img/a.png)\n")
    write(repo, "01-a/img/a.png", b"\x89PNG" + b"0" * 100)
    write(repo, "01-a/data/a.lumice.json", "{}")
    commit(repo, "init")
    # 桩 git-lfs：把 argv 与 stdin 追加进记录文件
    stub = tmp_path / "bin"
    stub.mkdir()
    log = tmp_path / "lfs.log"
    (stub / "git-lfs").write_text(f"#!/bin/sh\necho \"ARGS $*\" >> '{log}'\ncat >> '{log}'\necho END >> '{log}'\n")
    (stub / "git-lfs").chmod(0o755)
    install = subprocess.run(["bash", str(repo / "tools/hooks/install.sh")], cwd=repo, capture_output=True, text=True)
    assert install.returncode == 0, install.stderr
    base_env = dict(os.environ, PATH=f"{stub}{os.pathsep}{os.environ['PATH']}")
    for k in ("SLIM_PUSH_OVERRIDE", "SLIM_PUSH_BUDGET_MB"):
        base_env.pop(k, None)
    return repo, remote, log, base_env


def push(repo: Path, env: dict, **extra: str) -> subprocess.CompletedProcess:
    return git(repo, "push", "-q", "origin", "main", env=dict(env, **extra), check=False)


def test_normal_push_passes_and_lfs_gets_full_stdin(env):
    repo, remote, log, e = env
    r = push(repo, e)
    assert r.returncode == 0, r.stderr
    sha = git(repo, "rev-parse", "HEAD").stdout.strip()
    text = log.read_text()
    assert f"refs/heads/main {sha} refs/heads/main {'0' * 40}" in text      # lfs 桩拿到完整 ref 行
    assert text.startswith("ARGS pre-push origin ")


def test_ignored_path_is_rejected_and_listed(env):
    repo, remote, log, e = env
    assert push(repo, e).returncode == 0
    write(repo, "01-a/data/run/img_01.png", b"raw")
    write(repo, "01-a/img/unused.png", b"u")
    git(repo, "add", "-f", "01-a")
    git(repo, "commit", "-qm", "bad")
    r = push(repo, e)
    assert r.returncode != 0
    assert "01-a/data/run/img_01.png" in r.stderr and "01-a/img/unused.png" in r.stderr
    assert git(remote, "rev-parse", "main").stdout.strip() != git(repo, "rev-parse", "HEAD").stdout.strip()


def test_over_budget_is_rejected_and_override_passes(env):
    repo, remote, log, e = env
    assert push(repo, e).returncode == 0
    write(repo, "01-a/code/big.py", "#" * 20_000)
    commit(repo, "big")
    r = push(repo, e, SLIM_PUSH_BUDGET_MB="0.01")
    assert r.returncode != 0 and "超预算" in r.stderr
    r = push(repo, e, SLIM_PUSH_BUDGET_MB="0.01", SLIM_PUSH_OVERRIDE="测试放行")
    assert r.returncode == 0 and "测试放行" in r.stderr
    assert git(remote, "rev-parse", "main").stdout.strip() == git(repo, "rev-parse", "HEAD").stdout.strip()


def test_image_then_reference_in_same_push_is_accepted(env):
    """图先提交、引用它的 md 后提交、同一次推送：引用集合按被推送的 local_sha 树计算，不误拦。"""
    repo, remote, log, e = env
    assert push(repo, e).returncode == 0
    write(repo, "01-a/img/b.png", b"b")
    git(repo, "add", "-f", "01-a/img/b.png")
    git(repo, "commit", "-qm", "img first")
    write(repo, "01-a/正文.md", "![a](img/a.png)\n![b](img/b.png)\n")
    commit(repo, "then md")
    r = push(repo, e)
    assert r.returncode == 0, r.stderr


def test_lfs_pointer_counts_real_size(env):
    repo, remote, log, e = env
    assert push(repo, e).returncode == 0
    pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{'a' * 64}\nsize 50000000\n"
    write(repo, "01-a/img/big.png", pointer)
    write(repo, "01-a/正文.md", "![a](img/a.png)\n![b](img/big.png)\n")
    commit(repo, "big lfs")
    r = push(repo, e)
    assert r.returncode != 0 and "单文件超" in r.stderr and "50.00 MB" in r.stderr


def test_missing_checker_warns_and_still_runs_lfs(env):
    repo, remote, log, e = env
    (repo / "tools/hooks/pre-push").unlink()
    r = push(repo, e)
    assert r.returncode == 0
    assert "跳过体积闸" in r.stderr and "ARGS pre-push" in log.read_text()


def test_install_is_idempotent_and_uninstall_restores(env):
    repo, remote, log, e = env
    hooks = repo / ".git" / "hooks"
    baks = sorted(hooks.glob("pre-push.bak-*"))
    subprocess.run(["bash", "tools/hooks/install.sh"], cwd=repo, check=True, capture_output=True)
    assert sorted(hooks.glob("pre-push.bak-*")) == baks                     # 重装不再备份
    assert "REPO_SLIM_PREPUSH_WRAPPER" in (hooks / "pre-push").read_text()
    subprocess.run(["bash", "tools/hooks/install.sh", "--uninstall"], cwd=repo, check=True, capture_output=True)
    assert "REPO_SLIM_PREPUSH_WRAPPER" not in (hooks / "pre-push").read_text()
    assert "git lfs pre-push" in (hooks / "pre-push").read_text()
