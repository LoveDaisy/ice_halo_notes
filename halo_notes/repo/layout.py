"""git 划界规则的唯一权威实现：哪些文件进 git，哪些只留本地（gitignore）。

规则（按顺序判定，先中先得）：

1. 被任一 ``.md`` 引用的文件 → 进 git（「被正文引用的插图」；引用集合由 :func:`referenced_files` 扫描得出）；
   ``UNREGENERABLE_INPUTS`` 显式列出的「重生成被引用插图所需、本身无法重生成」的输入同样进 git
2. ``halo_notes/**/tests/data/**`` → 进 git（测试夹具）
3. 章目录（``NN-slug`` / ``NN.k-slug``）下 ``img/**``：``.gitkeep`` 进 git，其余一律 ignore
4. 章目录下 ``data/**``：``data/analysis*/**``（光路分析中间缓存目录）ignore；文本（``DATA_TEXT_EXTS``）且单文件
   ≤ ``DATA_TEXT_MAX_BYTES`` 进 git；其余（二进制 / 超限文本）ignore
5. 其余路径带媒体扩展名（``.gitattributes`` 里的 LFS 扩展名），或内容本身是 LFS pointer（``lfs=True``，历史上曾用 LFS 跟踪的
   无扩展名二进制，如 2022 年的仿真器可执行文件）→ ignore
6. 其余 → 进 git（md、代码、配置……）

``.gitignore`` 受管块只能表达路径 + 扩展名（规则 1、3、4 的路径部分、5 不表达）；大小阈值与规则 5 由
``check-tree`` / ``check-push`` 兜底。

CLI（``python -m halo_notes.repo.layout <cmd>``）：

- ``referenced``：列出被引用的文件与解析失败的引用
- ``classify PATH...``：逐个给出 keep / ignore 与理由
- ``sync-gitignore [--check]``：重写 ``.gitignore`` 受管块（``--check`` 只比对，不一致返回 1）
- ``check-tree``：工作区全量核对（已跟踪却应 ignore、未被 gitignore 覆盖、被引用却未跟踪 / 被 ignore、断链）
- ``check-push``：pre-push 钩子调用，stdin 为 git 传入的 ref 行（见 ``tools/hooks/pre-push``）

只用标准库，兼容 Python ≥ 3.9。
"""

from __future__ import annotations

import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Set, Tuple
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[2]

CHAPTER_RE = re.compile(r"^\d\d(\.\d+)?-[^/]+$")
CHAPTER_GLOB = "[0-9][0-9]*-*"  # .gitignore 里与 CHAPTER_RE 对应的通配（`*` 不跨 `/`）
# 2026-09 布局重组前的章目录名（`halo6. Differentiable Render`、`ex-tape-vs-matrix`）：HEAD 上已不存在，只让历史重写按同一套规则判定
LEGACY_CHAPTER_RE = re.compile(r"^(halo\d+(\.\d+)*\. .+|ex-[a-z0-9-]+)$")

DATA_TEXT_EXTS = (".json", ".csv", ".txt", ".md", ".log", ".tsv")
DATA_TEXT_MAX_BYTES = 512 * 1024
DATA_CACHE_DIR_RE = re.compile(r"^analysis(_.*)?$")  # data/analysis/、历史上的 data/analysis_<ha>/：光路分析中间缓存目录
KEEP_NAMES = (".gitkeep",)

# 重生成被引用插图所需、但本身无法用本仓脚本重生成的输入（逐条写理由；增补须有被引用图依赖它的证据）
UNREGENERABLE_INPUTS = {
    "06-monte-carlo-vs-integration/data/column1.0_direct.jpg":
        "compare_two_methods.jpg 第四条带（直接积分）；直接积分项目尚未用 python 重做，源数据只有 legacy matlab 的 data_251x801.bin",
}

# 扫描 md 时跳过的顶层目录（本地任务管理 / 环境 / 缓存）；任何层级的隐藏目录也跳过
MD_SKIP_TOP = ("scratchpad", ".venv", ".lumice", "node_modules")

MANAGED_BEGIN = "# >>> repo-slim 受管块：由 `python -m halo_notes.repo.layout sync-gitignore` 生成，勿手改 >>>"
MANAGED_END = "# <<< repo-slim 受管块 <<<"

PUSH_BUDGET_MB = 30.0
PUSH_FILE_MAX_MB = 10.0
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/"


def media_exts(root: Path = REPO_ROOT) -> Tuple[str, ...]:
    """``.gitattributes`` 里走 LFS 的扩展名（``*.png filter=lfs ...``），即「媒体 / 二进制」扩展名集合。"""
    ga = root / ".gitattributes"
    return media_exts_from_text(ga.read_text(encoding="utf-8") if ga.exists() else "")


def media_exts_from_text(text: str) -> Tuple[str, ...]:
    exts = []
    for line in text.splitlines():
        m = re.match(r"^\*(\.[A-Za-z0-9]+)\s.*\bfilter=lfs\b", line.strip())
        if m:
            exts.append(m.group(1).lower())
    return tuple(exts)


# ---------------------------------------------------------------- 引用扫描


class Ref(NamedTuple):
    md: str       # 引用所在 md（仓内相对路径，posix）
    line: int
    raw: str      # 原始目标文本
    kind: str     # md-link / html / wikilink


_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
# ![alt](target) / [text](target)；target 为 <...> 或不含空白的串，后可跟 "title"
_MD_LINK_RE = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*(<[^>]*>|[^\s()]*(?:\([^\s()]*\)[^\s()]*)*)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)")
_HTML_SRC_RE = re.compile(r"<(?:img|video|source)\b[^>]*?\bsrc\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
_WIKI_RE = re.compile(r"!?\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")


def extract_refs(md_path: str, text: str) -> List[Ref]:
    """从一份 md 文本里抽出所有链接目标（跳过围栏代码块与行内代码）。"""
    refs: List[Ref] = []
    fence: Optional[str] = None
    for i, line in enumerate(text.splitlines(), 1):
        m = _FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(2)
            continue
        line = _INLINE_CODE_RE.sub("", line)
        for m in _MD_LINK_RE.finditer(line):
            target = m.group(1)
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            refs.append(Ref(md_path, i, target, "md-link"))
        for m in _HTML_SRC_RE.finditer(line):
            refs.append(Ref(md_path, i, m.group(1).strip("\"'"), "html"))
        for m in _WIKI_RE.finditer(line):
            refs.append(Ref(md_path, i, m.group(1).strip(), "wikilink"))
    return refs


class RepoView:
    """「文件清单 + 读文本」的抽象：工作区实现与 git 树实现共享同一套解析规则。"""

    def __init__(self, files: Iterable[str], read_text: Callable[[str], str], exts: Tuple[str, ...]):
        self.files: Set[str] = set(files)
        self.exts = exts
        self.read_text = read_text
        self._by_name: Dict[str, List[str]] = {}
        for f in self.files:
            self._by_name.setdefault(posixpath.basename(f), []).append(f)

    def md_files(self) -> List[str]:
        out = []
        for f in sorted(self.files):
            if not f.endswith(".md"):
                continue
            parts = f.split("/")
            if parts[0] in MD_SKIP_TOP or any(p.startswith(".") for p in parts[:-1]):
                continue
            out.append(f)
        return out

    def by_basename(self, name: str) -> List[str]:
        return self._by_name.get(name, [])


def worktree_view(root: Path = REPO_ROOT) -> RepoView:
    """工作区实现：磁盘上存在的已跟踪 / 未跟踪文件（含已被 ignore 的章目录文件，供引用解析），读磁盘。"""
    files = _visible_files(root)
    chapters = [d.name for d in root.iterdir() if d.is_dir() and is_chapter_dir(d.name)]
    if chapters:
        out = _git(root, "ls-files", "-z", "-o", "-i", "--exclude-standard", "--", *chapters)
        files += [f for f in out.decode("utf-8").split("\0") if f and (root / f).is_file()]
    return RepoView(files, lambda p: (root / p).read_text(encoding="utf-8", errors="replace"), media_exts(root))


def _visible_files(root: Path) -> List[str]:
    """已跟踪 + 未跟踪未忽略、且在磁盘上存在的文件（``git ls-files -co --exclude-standard``）。"""
    out = _git(root, "ls-files", "-z", "-co", "--exclude-standard")
    return [f for f in dict.fromkeys(out.decode("utf-8").split("\0")) if f and (root / f).is_file()]


def tree_view(rev: str, root: Path = REPO_ROOT) -> RepoView:
    """git 树实现：``rev`` 的完整文件树，读 blob。"""
    entries = ls_tree(rev, root)
    blobs = {p: e[0] for p, e in entries.items()}

    def read(p: str) -> str:
        return _git(root, "cat-file", "blob", blobs[p]).decode("utf-8", errors="replace")

    ga = blobs.get(".gitattributes")
    exts = media_exts_from_text(_git(root, "cat-file", "blob", ga).decode("utf-8")) if ga else ()
    return RepoView(entries.keys(), read, exts)


def _is_external(target: str) -> bool:
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target)) or target.startswith("#") or target.startswith("//")


def resolve_ref(view: RepoView, ref: Ref) -> Tuple[Optional[str], Optional[str]]:
    """把一条引用解析为仓内路径；返回 ``(path, error)``，二者至多一个非空；两者皆空表示「不关心的引用」。"""
    target = ref.raw.strip()
    if not target or _is_external(target):
        return None, None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0]).strip()
    if not target:
        return None, None
    base = posixpath.dirname(ref.md)
    cands: List[str] = []
    if target.startswith("/"):
        cands.append(posixpath.normpath(target.lstrip("/")))
    else:
        cands.append(posixpath.normpath(posixpath.join(base, target)))
        if ref.kind == "wikilink":
            cands.append(posixpath.normpath(target))
    for c in cands:
        if c in view.files:
            return c, None
    if ref.kind == "wikilink" and "/" not in target:
        hits = view.by_basename(target)
        if len(hits) == 1:
            return hits[0], None
        if len(hits) > 1:
            return None, "basename 多义：" + ", ".join(sorted(hits))
    ext = posixpath.splitext(target)[1].lower()
    if ext in view.exts:
        return None, "找不到目标文件"
    return None, None  # 非媒体目标（md 页面、wikilink 笔记名等）解析不到不报错


def referenced_files(view: RepoView) -> Tuple[Set[str], List[Tuple[Ref, str]]]:
    """扫描全部 md，返回 ``(被引用的非 md 文件集合, [(引用, 错误)])``。"""
    refs: Set[str] = set()
    errors: List[Tuple[Ref, str]] = []
    for md in view.md_files():
        for ref in extract_refs(md, view.read_text(md)):
            path, err = resolve_ref(view, ref)
            if err:
                errors.append((ref, err))
            elif path and not path.endswith(".md"):
                refs.add(path)
    return refs, errors


# ---------------------------------------------------------------- 分类


def is_chapter_dir(name: str) -> bool:
    return bool(CHAPTER_RE.match(name))


def _is_any_chapter_dir(name: str) -> bool:
    return bool(CHAPTER_RE.match(name) or LEGACY_CHAPTER_RE.match(name))


def classify(path: str, referenced: Set[str], size: Optional[int] = None,
             exts: Optional[Tuple[str, ...]] = None, lfs: bool = False) -> Tuple[str, str]:
    """返回 ``("keep" | "ignore", 理由)``。``size`` 为文件字节数（LFS 文件取真实大小），未知时不做大小判定；
    ``lfs`` 为该版本内容是否 LFS pointer（未知时 False）。"""
    exts = media_exts() if exts is None else exts
    parts = path.split("/")
    name = parts[-1]
    ext = posixpath.splitext(name)[1].lower()
    if path in referenced:
        return "keep", "被 md 引用"
    if path in UNREGENERABLE_INPUTS:
        return "keep", "不可重生成的输入"
    if parts[0] == "halo_notes" and any(parts[i] == "tests" and parts[i + 1] == "data" for i in range(len(parts) - 2)):
        return "keep", "测试夹具"
    if len(parts) >= 3 and _is_any_chapter_dir(parts[0]) and parts[1] == "img":
        if name in KEEP_NAMES:
            return "keep", "占位文件"
        return "ignore", "img 下未被引用"
    if len(parts) >= 3 and _is_any_chapter_dir(parts[0]) and parts[1] == "data":
        if len(parts) >= 4 and DATA_CACHE_DIR_RE.match(parts[2]):
            return "ignore", "data 中间缓存目录"
        if name in KEEP_NAMES:
            return "keep", "占位文件"
        if ext in DATA_TEXT_EXTS:
            if size is not None and size > DATA_TEXT_MAX_BYTES:
                return "ignore", f"data 文本超限（{size} > {DATA_TEXT_MAX_BYTES} B）"
            return "keep", "data 小体积文本"
        return "ignore", "data 下非文本"
    if ext in exts:
        return "ignore", "img 之外的媒体文件且未被引用"
    if lfs:
        return "ignore", "LFS 存储的二进制且未被引用"
    return "keep", "md / 代码 / 配置"


# ---------------------------------------------------------------- .gitignore 受管块


def _gi_escape(path: str) -> str:
    out = re.sub(r"([\\\[\]*?])", r"\\\1", path)
    if out.endswith(" "):
        out = out[:-1] + "\\ "
    return out


def render_gitignore_block(referenced: Iterable[str]) -> str:
    ch = "/" + CHAPTER_GLOB
    lines = [
        MANAGED_BEGIN,
        "# 划界规则见 halo_notes/repo/layout.py 模块文档与 AGENTS.md「数据约定」；大小阈值由 check-tree / pre-push 兜底",
        f"{ch}/img/**",
        f"!{ch}/img/**/",
        f"{ch}/data/**",
        f"!{ch}/data/**/",
    ]
    for e in DATA_TEXT_EXTS:
        lines.append(f"!{ch}/data/**/*{e}")
    for n in KEEP_NAMES:
        lines.append(f"!{ch}/img/**/{n}")
        lines.append(f"!{ch}/data/**/{n}")
    lines.append(f"{ch}/data/analysis/")
    lines.append(f"{ch}/data/analysis_*/")
    lines.append("# 被 md 引用的文件 + UNREGENERABLE_INPUTS（放行）")
    lines += ["!/" + _gi_escape(p) for p in sorted(set(referenced) | set(UNREGENERABLE_INPUTS))]
    lines.append(MANAGED_END)
    return "\n".join(lines) + "\n"


def splice_gitignore(text: str, block: str) -> str:
    """把受管块替换进 ``.gitignore`` 文本（无则追加到末尾）。"""
    if MANAGED_BEGIN in text and MANAGED_END in text:
        head, rest = text.split(MANAGED_BEGIN, 1)
        _, tail = rest.split(MANAGED_END, 1)
        return head + block + tail.lstrip("\n")
    if text and not text.endswith("\n"):
        text += "\n"
    return text + ("\n" if text else "") + block


# ---------------------------------------------------------------- git 辅助


def _git(root: Path, *args: str, input: Optional[bytes] = None, ok_codes: Tuple[int, ...] = (0,)) -> bytes:
    proc = subprocess.run(["git", "-C", str(root), *args], input=input, stdout=subprocess.PIPE)
    if proc.returncode not in ok_codes:
        raise subprocess.CalledProcessError(proc.returncode, ["git", *args], proc.stdout)
    return proc.stdout


def ls_tree(rev: str, root: Path = REPO_ROOT) -> Dict[str, Tuple[str, int]]:
    """``rev`` 树的 ``{path: (blob sha, git 对象大小)}``。"""
    out = _git(root, "ls-tree", "-r", "-z", "-l", "--full-tree", rev)
    entries = {}
    for rec in out.decode("utf-8").split("\0"):
        if not rec:
            continue
        meta, path = rec.split("\t", 1)
        mode, typ, sha, size = meta.split()
        if typ == "blob":
            entries[path] = (sha, int(size))
    return entries


def parse_lfs_pointer(data: bytes) -> Optional[Tuple[str, int]]:
    """LFS pointer → ``(oid, size)``；非 pointer 返回 None。"""
    if not data.startswith(LFS_POINTER_PREFIX) or len(data) > 1024:
        return None
    oid = size = None
    for line in data.decode("utf-8", "replace").splitlines():
        if line.startswith("oid sha256:"):
            oid = line.split(":", 1)[1].strip()
        elif line.startswith("size "):
            size = int(line.split()[1])
    return (oid, size) if oid and size is not None else None


def blob_real_sizes(shas: Iterable[str], root: Path = REPO_ROOT) -> Dict[str, Tuple[int, bool]]:
    """blob sha → ``(真实大小, 是否 LFS)``：LFS pointer 取 ``size`` 字段，普通 blob 取对象大小。"""
    shas = sorted(set(shas))
    if not shas:
        return {}
    proc = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"], input="".join(s + "\n" for s in shas).encode(),
                          stdout=subprocess.PIPE, check=True)
    buf, pos, out = proc.stdout, 0, {}
    for sha in shas:
        nl = buf.index(b"\n", pos)
        header = buf[pos:nl].split()
        if header[-1] == b"missing":      # gitlink / 子模块条目等本仓没有的对象：不计体积
            pos = nl + 1
            continue
        size = int(header[2])
        data = buf[nl + 1:nl + 1 + min(size, 1024)]
        pos = nl + 1 + size + 1
        ptr = parse_lfs_pointer(data) if size <= 1024 else None
        out[sha] = (ptr[1], True) if ptr else (size, False)
    return out


# ---------------------------------------------------------------- check-tree


def check_tree(root: Path = REPO_ROOT) -> List[str]:
    """工作区全量核对，返回违规描述列表（空 = 通过）。"""
    problems: List[str] = []
    view = worktree_view(root)
    refs, errors = referenced_files(view)
    for ref, err in errors:
        problems.append(f"断链：{ref.md}:{ref.line} → {ref.raw}（{err}）")
    exts = media_exts(root)
    tracked = set(f for f in _git(root, "ls-files", "-z").decode("utf-8").split("\0") if f)
    for f in sorted(_visible_files(root)):
        size = (root / f).stat().st_size
        verdict, why = classify(f, refs, size, exts)
        if verdict == "ignore":
            if f in tracked:
                problems.append(f"已跟踪但应 ignore：{f}（{why}）")
            else:
                problems.append(f"未被 .gitignore 覆盖但应 ignore：{f}（{why}）")
    for f in sorted(refs - tracked):
        problems.append(f"被引用但未跟踪：{f}")
    for f in sorted(set(UNREGENERABLE_INPUTS) - tracked):
        if not (root / f.split("/", 1)[0]).is_dir():
            continue  # 该章不在此仓（合成测试仓）
        problems.append(f"不可重生成的输入未跟踪：{f}")
    keep_tracked = [f for f in sorted(tracked) if classify(f, refs, None, exts)[0] == "keep"]
    if keep_tracked:
        out = _git(root, "check-ignore", "--no-index", "--stdin", "-z", input="\0".join(keep_tracked).encode() + b"\0",
                   ok_codes=(0, 1))
        for f in out.decode("utf-8").split("\0"):
            if f:
                problems.append(f"应进 git 却被 .gitignore 命中：{f}")
    gi = root / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if splice_gitignore(text, render_gitignore_block(refs)) != text:
        problems.append(".gitignore 受管块过期：运行 `python -m halo_notes.repo.layout sync-gitignore`")
    return problems


# ---------------------------------------------------------------- check-push

ZERO_SHA = "0" * 40


def _rev_exists(root: Path, sha: str) -> bool:
    return subprocess.run(["git", "-C", str(root), "cat-file", "-e", sha + "^{commit}"],
                          stderr=subprocess.DEVNULL).returncode == 0


def pushed_commits(root: Path, local_sha: str, remote_sha: str) -> List[str]:
    if remote_sha != ZERO_SHA and _rev_exists(root, remote_sha):
        args = ["rev-list", f"{remote_sha}..{local_sha}"]
    else:
        args = ["rev-list", local_sha, "--not", "--remotes"]
    return [c for c in _git(root, *args).decode().split() if c]


def changed_blobs(root: Path, commits: Iterable[str]) -> Set[Tuple[str, str]]:
    """范围内提交新增 / 修改的 ``{(path, blob sha)}``（同一路径多次修改各计一次）。"""
    out: Set[Tuple[str, str]] = set()
    for c in commits:
        raw = _git(root, "diff-tree", "-r", "--root", "--no-commit-id", "--no-renames", "-z", "--diff-filter=AMT", c)
        items = raw.decode("utf-8").split("\0")
        for i in range(0, len(items) - 1, 2):
            meta, path = items[i], items[i + 1]
            if not meta:
                continue
            new_sha = meta.split()[3]
            out.add((path, new_sha))
    return out


def check_push(lines: Iterable[str], root: Path = REPO_ROOT, env: Optional[Dict[str, str]] = None) -> Tuple[int, List[str]]:
    """pre-push 核对；返回 ``(退出码, 输出行)``。"""
    env = dict(os.environ if env is None else env)
    try:
        budget = float(env.get("SLIM_PUSH_BUDGET_MB") or PUSH_BUDGET_MB)
    except ValueError:
        raise ValueError(f"SLIM_PUSH_BUDGET_MB 不是数字：{env.get('SLIM_PUSH_BUDGET_MB')!r}") from None
    file_max = PUSH_FILE_MAX_MB
    exts = media_exts(root)
    problems: List[str] = []
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = parts
        if local_sha == ZERO_SHA:
            continue
        refs, _errors = referenced_files(tree_view(local_sha, root))
        commits = pushed_commits(root, local_sha, remote_sha)
        changed = changed_blobs(root, commits)
        sizes = blob_real_sizes([sha for _, sha in changed], root)
        seen: Set[str] = set()
        total = 0
        for path, sha in sorted(changed):
            if sha not in sizes:          # gitlink 等本仓没有的对象，不计体积
                continue
            size, is_lfs = sizes[sha]
            verdict, why = classify(path, refs, size, exts, lfs=is_lfs)
            if verdict == "ignore":
                problems.append(f"{local_ref}: 按规则应 ignore：{path}（{why}，{size / 1e6:.2f} MB）")
            if size > file_max * 1e6:
                problems.append(f"{local_ref}: 单文件超 {file_max:g} MB：{path}（{size / 1e6:.2f} MB）")
            if sha not in seen:
                seen.add(sha)
                total += size
        if total > budget * 1e6:
            problems.append(f"{local_ref}: 本次推送新增 blob 共 {total / 1e6:.2f} MB，超预算 {budget:g} MB"
                            f"（{len(commits)} 个提交）")
    if not problems:
        return 0, []
    msg = ["repo-slim pre-push 体积闸：拒绝推送"] + ["  - " + p for p in problems] + [
        "规则见 AGENTS.md「数据约定」。确需推送：SLIM_PUSH_OVERRIDE=\"<理由>\" git push ...；"
        "只调预算：SLIM_PUSH_BUDGET_MB=<N> git push ..."]
    override = env.get("SLIM_PUSH_OVERRIDE", "").strip()
    if override:
        msg[0] = f"repo-slim pre-push 体积闸：已被 SLIM_PUSH_OVERRIDE 放行（理由：{override}）"
        return 0, msg
    return 1, msg


# ---------------------------------------------------------------- CLI


def _cmd_referenced(root: Path) -> int:
    refs, errors = referenced_files(worktree_view(root))
    for p in sorted(refs):
        print(p)
    for ref, err in errors:
        print(f"ERROR {ref.md}:{ref.line} → {ref.raw}（{err}）", file=sys.stderr)
    print(f"# {len(refs)} 个被引用文件，{len(errors)} 条解析失败", file=sys.stderr)
    return 1 if errors else 0


def _cmd_classify(root: Path, paths: List[str]) -> int:
    refs, _ = referenced_files(worktree_view(root))
    for p in paths:
        f = root / p
        size = f.stat().st_size if f.is_file() else None
        verdict, why = classify(p, refs, size, media_exts(root))
        print(f"{verdict}\t{p}\t{why}")
    return 0


def _cmd_sync(root: Path, check: bool) -> int:
    refs, errors = referenced_files(worktree_view(root))
    for ref, err in errors:
        print(f"ERROR {ref.md}:{ref.line} → {ref.raw}（{err}）", file=sys.stderr)
    gi = root / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    new = splice_gitignore(text, render_gitignore_block(refs))
    if check:
        if new != text:
            print(".gitignore 受管块过期", file=sys.stderr)
            return 1
        return 0
    if new != text:
        gi.write_text(new, encoding="utf-8")
        print(f"已更新 .gitignore（放行 {len(refs)} 个被引用文件）")
    return 1 if errors else 0


def _cmd_check_tree(root: Path) -> int:
    problems = check_tree(root)
    for p in problems:
        print(p)
    print(f"# check-tree：{len(problems)} 条违规", file=sys.stderr)
    return 1 if problems else 0


def _cmd_check_push(root: Path) -> int:
    try:
        code, msg = check_push(sys.stdin.read().splitlines(), root)
    except Exception as e:                # 内部错误 fail-closed，但 SLIM_PUSH_OVERRIDE 仍可放行
        override = os.environ.get("SLIM_PUSH_OVERRIDE", "").strip()
        if override:
            print(f"repo-slim pre-push 体积闸：内部错误（{type(e).__name__}: {e}），已被 SLIM_PUSH_OVERRIDE 放行（理由：{override}）",
                  file=sys.stderr)
            return 0
        print(f"repo-slim pre-push 体积闸：内部错误（{type(e).__name__}: {e}）；这不是体积违规，"
              "确需推送请设 SLIM_PUSH_OVERRIDE=\"<理由>\"", file=sys.stderr)
        return 1
    for m in msg:
        print(m, file=sys.stderr)
    return code


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="python -m halo_notes.repo.layout", description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=None, help="仓库根（默认当前目录所在 git 仓）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("referenced")
    p = sub.add_parser("classify")
    p.add_argument("paths", nargs="+")
    p = sub.add_parser("sync-gitignore")
    p.add_argument("--check", action="store_true")
    sub.add_parser("check-tree")
    sub.add_parser("check-push")
    a = ap.parse_args(argv)
    root = a.root or Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    if a.cmd == "referenced":
        return _cmd_referenced(root)
    if a.cmd == "classify":
        return _cmd_classify(root, a.paths)
    if a.cmd == "sync-gitignore":
        return _cmd_sync(root, a.check)
    if a.cmd == "check-tree":
        return _cmd_check_tree(root)
    return _cmd_check_push(root)


if __name__ == "__main__":
    sys.exit(main())
