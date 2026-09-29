#!/usr/bin/env bash
# 把 repo-slim pre-push 包装装进 git common dir 的 hooks/pre-push（主仓与全部 worktree 共享这一份）。
# 包装先跑推送所在 worktree 的 tools/hooks/pre-push（体积闸），通过后再 git lfs pre-push——LFS 上传一步绝不省略。
# 用法：tools/hooks/install.sh            安装（幂等；首次安装把原 pre-push 备份为 pre-push.bak-<时间戳>）
#       tools/hooks/install.sh --uninstall 卸载（恢复最近一次备份；无备份则写回标准 git-lfs 钩子）
set -euo pipefail
hooks="$(git rev-parse --path-format=absolute --git-common-dir)/hooks"
target="$hooks/pre-push"
marker="REPO_SLIM_PREPUSH_WRAPPER"
mkdir -p "$hooks"

lfs_hook='#!/bin/sh
command -v git-lfs >/dev/null 2>&1 || { echo >&2 "\nThis repository is configured for Git LFS but '"'"'git-lfs'"'"' was not found on your path. If you no longer wish to use Git LFS, remove this hook by deleting '"'"'.git/hooks/pre-push'"'"'.\n"; exit 2; }
git lfs pre-push "$@"'

if [ "${1:-}" = "--uninstall" ]; then
  if [ -f "$target" ] && ! grep -q "$marker" "$target"; then
    echo "pre-push 不是 repo-slim 包装，未改动：$target"; exit 0
  fi
  bak=$(ls -1 "$hooks"/pre-push.bak-* 2>/dev/null | sort | tail -1 || true)
  if [ -n "$bak" ]; then mv "$bak" "$target"; echo "已恢复 $bak → $target"
  else printf '%s\n' "$lfs_hook" > "$target"; chmod +x "$target"; echo "无备份，已写回标准 git-lfs pre-push"; fi
  exit 0
fi

if [ -f "$target" ] && ! grep -q "$marker" "$target"; then
  cp -p "$target" "$target.bak-$(date +%Y%m%d%H%M%S)"
fi
cat > "$target" <<'WRAP'
#!/usr/bin/env bash
# REPO_SLIM_PREPUSH_WRAPPER —— 由 tools/hooks/install.sh 生成，勿手改；卸载：tools/hooks/install.sh --uninstall
# git 只向钩子写一次 ref 列表：先存下 stdin，体积闸与 git lfs pre-push 各读一份完整副本（否则 lfs 读到空 stdin 会静默不传对象）。
set -u
tmp=$(mktemp "${TMPDIR:-/tmp}/repo-slim-prepush.XXXXXX")
cat > "$tmp"
top=$(git rev-parse --show-toplevel 2>/dev/null || true)
check="$top/tools/hooks/pre-push"
if [ -n "$top" ] && [ -x "$check" ]; then
  if ! "$check" "$@" < "$tmp"; then rm -f "$tmp"; exit 1; fi
else
  echo "repo-slim pre-push：$check 不存在（旧分支？），跳过体积闸，照常上传 LFS" >&2
fi
exec 3< "$tmp"
rm -f "$tmp"
command -v git-lfs >/dev/null 2>&1 || { echo >&2 "This repository is configured for Git LFS but 'git-lfs' was not found on your path."; exit 2; }
exec git lfs pre-push "$@" <&3
WRAP
chmod +x "$target"
echo "已安装 repo-slim pre-push 包装：$target"
