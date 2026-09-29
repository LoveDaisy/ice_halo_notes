#!/usr/bin/env bash
# 把 LFS 对象从一个本地 git 目录的 lfs 存储拷进另一个仓库（不联网）。stdin：每行一个 sha256 oid。
# 用法：tools/lfs-import.sh <源 git common dir> <目标 git dir>
# 缺失的 oid 打印到 stderr 并以 1 退出（拷贝其余照做）。clean-clone.sh 与 history-rewrite/rehearse.sh 共用这一份实现。
set -euo pipefail
src=$1
dst=$2
missing=0
n=0
while read -r oid; do
  [ -n "$oid" ] || continue
  rel="lfs/objects/${oid:0:2}/${oid:2:2}/$oid"
  if [ -f "$dst/$rel" ]; then continue; fi
  if [ -f "$src/$rel" ]; then
    mkdir -p "$(dirname "$dst/$rel")"
    cp "$src/$rel" "$dst/$rel"
    n=$((n + 1))
  else
    echo "lfs-import: 源存储缺对象 $oid" >&2
    missing=$((missing + 1))
  fi
done
echo "lfs-import: 拷入 $n 个对象，缺 $missing 个" >&2
[ "$missing" -eq 0 ]
