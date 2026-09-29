"""划界规则：引用扫描、classify、.gitignore 受管块（与 git 自身的 ignore 判定互证）、check-tree。"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from halo_notes.repo import layout as L

GITATTR = "*.png filter=lfs diff=lfs merge=lfs -text\n*.jpg filter=lfs diff=lfs merge=lfs -text\n*.gif filter=lfs diff=lfs merge=lfs -text\n*.psd filter=lfs diff=lfs merge=lfs -text\n"
EXTS = (".png", ".jpg", ".gif", ".psd")


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def write(root: Path, rel: str, data: str | bytes = "x") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        p.write_bytes(data)
    else:
        p.write_text(data, encoding="utf-8")
    return p


def make_view(files: dict[str, str]) -> L.RepoView:
    return L.RepoView(files.keys(), lambda p: files[p], EXTS)


# ------------------------------------------------------------------ 引用扫描


def test_extract_and_resolve_link_forms():
    md = "\n".join([
        "![a](img/plain.png)",
        "![b](img/with%20space.png \"title\")",
        "![c](<img/带 空格 的图.jpg>)",
        '<img src="img/html.png" width="300">',
        "![[wiki.gif|300]]",
        "![[img/wiki_dir.png]]",
        "[下载](img/linked.psd)",
        "`![inline](img/in_code.png)`",
        "```",
        "![fenced](img/in_fence.png)",
        "```",
        "![ext](https://example.com/x.png)",
        "[[另一篇笔记]]",
    ])
    files = {"01-a/正文.md": md}
    for f in ["plain.png", "with space.png", "带 空格 的图.jpg", "html.png", "wiki.gif", "wiki_dir.png", "linked.psd",
              "in_code.png", "in_fence.png"]:
        files["01-a/img/" + f] = ""
    refs, errors = L.referenced_files(make_view(files))
    assert errors == []
    assert refs == {"01-a/img/" + f for f in
                    ["plain.png", "with space.png", "带 空格 的图.jpg", "html.png", "wiki.gif", "wiki_dir.png", "linked.psd"]}


def test_unresolved_and_ambiguous_are_errors():
    files = {
        "01-a/正文.md": "![x](img/missing.png)\n![[dup.png]]\n[[不存在的笔记]]\n",
        "01-a/img/dup.png": "",
        "02-b/img/dup.png": "",
    }
    refs, errors = L.referenced_files(make_view(files))
    assert refs == set()
    msgs = sorted(e for _, e in errors)
    assert len(msgs) == 2 and "找不到" in msgs[1 if "多义" in msgs[0] else 0]
    assert any("多义" in m for m in msgs)


def test_md_skip_dirs():
    files = {"scratchpad/x.md": "![a](../01-a/img/a.png)", ".venv/y.md": "![a](../01-a/img/a.png)", "01-a/img/a.png": ""}
    refs, errors = L.referenced_files(make_view(files))
    assert refs == set() and errors == []


# ------------------------------------------------------------------ classify


@pytest.mark.parametrize("path,size,expect", [
    ("01-a/img/ref.png", None, "keep"),
    ("01-a/img/other.png", None, "ignore"),
    ("01-a/img/legacy/old.png", None, "ignore"),
    ("01-a/img/.gitkeep", None, "keep"),
    ("08.1-x/img/a.psd", None, "ignore"),
    ("01-a/data/a.lumice.json", 100, "keep"),
    ("01-a/data/run/provenance.json", 100, "keep"),
    ("01-a/data/run/lumice.log", 100, "keep"),
    ("01-a/data/big.csv", L.DATA_TEXT_MAX_BYTES + 1, "ignore"),
    ("01-a/data/edge.csv", L.DATA_TEXT_MAX_BYTES, "keep"),
    ("01-a/data/run/img_01.png", None, "ignore"),
    ("01-a/data/x.npy", None, "ignore"),
    ("01-a/data/analysis.zip", None, "ignore"),
    ("01-a/data/analysis/rows.csv", 10, "ignore"),
    ("01-a/data/.gitkeep", None, "keep"),
    ("halo_notes/sim/tests/data/fixture.png", None, "keep"),
    ("halo_notes/draw/foo.py", None, "keep"),
    ("01-a/code/legacy/x.nb", None, "keep"),
    ("docs/pic.png", None, "ignore"),
    ("01-a/正文.md", None, "keep"),
    ("06-monte-carlo-vs-integration/data/column1.0_direct.jpg", None, "keep"),
    ("01-a/data/analysis_0.2/analysis.csv", 10, "ignore"),
    ("01-a/data/analysis_0.2.lumice.json", 10, "keep"),
    ("halo6. Differentiable Render/data/data_251x801.bin", None, "ignore"),
    ("halo6. Differentiable Render/data/x.csv", 10, "keep"),
    ("halo1. Symmetry/c6.png", None, "ignore"),
    ("halo5.1. Spherical Distribution/a.m", None, "keep"),
    ("ex-tape-vs-matrix/img/a.png", None, "ignore"),
    ("06-monte-carlo-vs-integration/data/data_251x801.bin", None, "ignore"),
])
def test_classify(path, size, expect):
    assert L.classify(path, {"01-a/img/ref.png"}, size, EXTS)[0] == expect


def test_lfs_binary_without_media_ext_is_ignored():
    assert L.classify("halo2. All Possible Raypaths/IceHaloEndless", set(), 1_000_000, EXTS, lfs=True)[0] == "ignore"
    assert L.classify("halo2. All Possible Raypaths/IceHaloEndless", set(), 1_000_000, EXTS)[0] == "keep"
    assert L.classify("halo_notes/sim/tests/data/f.png", set(), 10, EXTS, lfs=True)[0] == "keep"
    assert L.classify("01-a/img/ref.png", {"01-a/img/ref.png"}, 10, EXTS, lfs=True)[0] == "keep"


def test_referenced_overrides_everything():
    assert L.classify("01-a/data/run/img_01.png", {"01-a/data/run/img_01.png"}, None, EXTS)[0] == "keep"


# ------------------------------------------------------------------ .gitignore 与 git 自身判定互证


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    write(root, ".gitattributes", GITATTR)
    return root


def test_gitignore_block_matches_classify(repo: Path):
    refs = {"01-a/img/ref.png", "01-a/img/legacy/kept old.png", "01-a/img/[x]*?.png", "01-a/data/run/used.png"}
    paths = sorted(refs | {
        "01-a/img/other.png", "01-a/img/legacy/old.png", "01-a/img/.gitkeep", "01-a/data/cfg.json",
        "01-a/data/run/img_01.png", "01-a/data/run/lumice.log", "01-a/data/analysis/rows.csv",
        "01-a/data/analysis.zip", "01-a/data/deep/er/x.csv", "01-a/data/analysis_0.2/a.csv", "01-a/data/analysis_0.2.lumice.json", "01-a/code/fig_a.py", "halo_notes/x/tests/data/f.png",
    })
    for p in paths:
        write(repo, p)
    write(repo, ".gitignore", L.splice_gitignore("scratchpad/\n", L.render_gitignore_block(refs)))
    out = subprocess.run(["git", "-C", str(repo), "check-ignore", "--no-index", "--stdin"], input="\n".join(paths) + "\n",
                         capture_output=True, text=True).stdout.split("\n")
    ignored = {p for p in out if p}
    for p in paths:
        verdict = L.classify(p, refs, 10, EXTS)[0]
        assert (p in ignored) == (verdict == "ignore"), (p, verdict)


def test_splice_is_idempotent():
    block = L.render_gitignore_block({"01-a/img/a.png"})
    once = L.splice_gitignore("head\n", block)
    assert L.splice_gitignore(once, block) == once
    assert once.startswith("head\n")
    block2 = L.render_gitignore_block({"01-a/img/b.png"})
    twice = L.splice_gitignore(once, block2)
    assert "a.png" not in twice and "b.png" in twice and twice.startswith("head\n")


def test_check_tree(repo: Path):
    write(repo, "01-a/正文.md", "![a](img/a.png)\n![b](img/b.png)\n")
    write(repo, "01-a/img/a.png")
    write(repo, "01-a/img/b.png")
    write(repo, "01-a/img/unused.png")
    write(repo, "01-a/data/run/img_01.png")
    write(repo, "01-a/data/cfg.json", "{}")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    problems = L.check_tree(repo)
    joined = "\n".join(problems)
    assert "已跟踪但应 ignore：01-a/img/unused.png" in joined
    assert "已跟踪但应 ignore：01-a/data/run/img_01.png" in joined
    assert "受管块过期" in joined
    assert L._cmd_sync(repo, check=False) == 0
    git(repo, "rm", "-q", "--cached", "01-a/img/unused.png", "01-a/data/run/img_01.png")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "slim")
    assert L.check_tree(repo) == []
    # 大文本未被 .gitignore 覆盖 → 由 check-tree 兜底报出
    write(repo, "01-a/data/huge.csv", "x" * (L.DATA_TEXT_MAX_BYTES + 1))
    assert any("未被 .gitignore 覆盖但应 ignore：01-a/data/huge.csv" in p for p in L.check_tree(repo))
    (repo / "01-a/data/huge.csv").unlink()
    # 被引用却未跟踪
    write(repo, "01-a/正文.md", "![a](img/a.png)\n![b](img/b.png)\n![c](img/c.png)\n")
    write(repo, "01-a/img/c.png")
    assert L._cmd_sync(repo, check=False) == 0
    assert any("被引用但未跟踪：01-a/img/c.png" in p for p in L.check_tree(repo))


def test_real_repo_referenced_no_errors():
    """真实仓：所有 md 里的媒体引用都能解析（断链会在这里暴露）。"""
    refs, errors = L.referenced_files(L.worktree_view(L.REPO_ROOT))
    assert errors == [], errors
    assert refs, "真实仓至少有一张被引用的图"
