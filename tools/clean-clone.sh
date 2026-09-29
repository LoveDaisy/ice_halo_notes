#!/usr/bin/env bash
# 建一个「只有 git 内容」的干净 clone，模拟新 checkout（用于验证重生成入口与 pytest）。
# LFS 对象从本仓本地存储补入（不联网）；目标目录必须不存在。
# 用法：tools/clean-clone.sh <目标目录> [rev，默认 HEAD]
set -euo pipefail
dest=$1
rev=${2:-HEAD}
here=$(cd "$(dirname "$0")" && pwd)
src=$(git -C "$here/.." rev-parse --show-toplevel)
common=$(cd "$src" && cd "$(git rev-parse --git-common-dir)" && pwd)
sha=$(git -C "$src" rev-parse "$rev^{commit}")
[ ! -e "$dest" ] || { echo "clean-clone: $dest 已存在" >&2; exit 1; }

GIT_LFS_SKIP_SMUDGE=1 git clone -q --no-checkout "$src" "$dest"
git -C "$dest" config lfs.url "file:///dev/null"   # 防止误从远端拉对象
GIT_LFS_SKIP_SMUDGE=1 git -C "$dest" checkout -q -B clean-check "$sha"
git -C "$dest" lfs ls-files --long | awk '{print $1}' | "$here/lfs-import.sh" "$common" "$dest/.git"
git -C "$dest" lfs checkout >/dev/null
echo "clean-clone: $dest @ ${sha:0:10}（$(git -C "$dest" ls-files | wc -l | tr -d ' ') 个文件）"
