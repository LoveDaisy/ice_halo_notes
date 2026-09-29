"""tools/history-rewrite/remap_hashes.py：只替换旧仓里确为 commit 的哈希，按原长度截断；被裁剪 / 不在 map 的列清单不替换。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from halo_notes.repo import layout

SCRIPT = layout.REPO_ROOT / "tools" / "history-rewrite" / "remap_hashes.py"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def test_remap(tmp_path: Path):
    old = tmp_path / "old"
    old.mkdir()
    git(old, "init", "-q")
    git(old, "config", "user.email", "t@t")
    git(old, "config", "user.name", "t")
    shas = []
    for i in range(3):
        (old / "f.txt").write_text(str(i))
        git(old, "add", "f.txt")
        git(old, "commit", "-qm", f"c{i}")
        shas.append(git(old, "rev-parse", "HEAD"))
    blob = git(old, "rev-parse", "HEAD:f.txt")
    new = ["a" * 40, "0" * 40]
    cmap = tmp_path / "commit-map"
    cmap.write_text(f"old new\n{shas[0]} {new[0]}\n{shas[1]} {new[1]}\n")
    sha256 = "b" * 64
    doc = tmp_path / "docs" / "x.md"
    doc.parent.mkdir()
    text = (f"full {shas[0]} short {shas[0][:7]} pruned {shas[1][:10]} unmapped {shas[2][:8]} "
            f"blob {blob[:12]} sha256 {sha256} word deadbeefcafe\n")
    doc.write_text(text)
    report = tmp_path / "r.json"
    args = [sys.executable, str(SCRIPT), "--old", str(old), "--map", str(cmap), "--paths", str(tmp_path / "docs"),
            "--report", str(report)]
    subprocess.run(args, check=True, capture_output=True)
    assert doc.read_text() == text                                    # dry-run 不写
    subprocess.run(args + ["--apply"], check=True, capture_output=True)
    got = doc.read_text()
    assert f"full {'a' * 40} short {'a' * 7} " in got
    assert f"pruned {shas[1][:10]}" in got and f"unmapped {shas[2][:8]}" in got
    assert f"blob {blob[:12]}" in got and sha256 in got and "deadbeefcafe" in got
    r = json.loads(report.read_text())
    assert sum(map(len, r["replaced"].values())) == 2
    assert list(r["pruned_commits_not_replaced"].values()) == [[shas[1][:10]]]
    assert list(r["not_in_commit_map"].values()) == [[shas[2][:8]]]
