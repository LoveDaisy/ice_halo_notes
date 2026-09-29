#!/usr/bin/env bash
# 在临时 mirror 上演练历史重写：真实仓只读（前后核对全部 refs 不变），所有写操作都在 <输出目录>。
# 输入一律取自本地主仓（不取远端：未推送的提交与 LFS 对象只在本地），LFS 对象从本地存储补入 mirror。
# 用法：tools/history-rewrite/rehearse.sh <本地主仓路径> <输出目录> [保留的 rev，默认 main]
#   产出：<输出目录>/backup.git（完整 mirror + 全部 LFS 对象）、keep/、work-{oid,path}.git（重写结果）、
#        before.json / after-{oid,path}.json / filter-{oid,path}.json、rehearsal-report.md
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
src=$(cd "${1:?本地主仓路径}" && pwd)
out=${2:?输出目录}
rev=${3:-main}
common=$(git -C "$src" rev-parse --path-format=absolute --git-common-dir)
fr=$(command -v git-filter-repo) || { echo "需要 git-filter-repo" >&2; exit 1; }
py=$(head -1 "$fr" | sed 's/^#!//; s/^\/usr\/bin\/env //')
"$py" -c 'import git_filter_repo' || { echo "$py 里 import 不到 git_filter_repo" >&2; exit 1; }
follow=("01-symmetry/迷镜千幻不离宗.md" "06-monte-carlo-vs-integration/蒙特卡洛 vs. 直接积分.md" "08-wedge-times-fold/三种楔子-十二种折叠.md" "docs/roadmap.md")

refs_before=$(git -C "$src" for-each-ref --format='%(refname) %(objectname)' | shasum -a 256)
mkdir -p "$out"
[ ! -e "$out/backup.git" ] || { echo "$out/backup.git 已存在" >&2; exit 1; }
sha=$(git -C "$src" rev-parse "$rev^{commit}")

echo "== 1. mirror 备份（取自本地仓 ${src}）"
git clone -q --mirror "$src" "$out/backup.git"
[ "$(git -C "$out/backup.git" rev-parse "$rev^{commit}")" = "$sha" ] || { echo "mirror 的 $rev 与本地不一致" >&2; exit 1; }
find "$common/lfs/objects" -type f -not -name '*.tmp' | xargs -n1 basename | "$here/../lfs-import.sh" "$common" "$out/backup.git"

echo "== 2. 保留集（${rev} = ${sha:0:10}）"
"$py" "$here/build_keep_set.py" "$out/backup.git" --rev "$rev" --out "$out/keep"
while read -r oid; do
  [ -f "$out/backup.git/lfs/objects/${oid:0:2}/${oid:2:2}/$oid" ] || { echo "keep oid 不在 mirror LFS 存储：$oid" >&2; exit 1; }
done < "$out/keep/keep_oids.txt"

echo "== 3. 重写前体量"
"$py" "$here/measure.py" "$out/backup.git" --rev "$rev" --follow "${follow[@]}" --out "$out/before-all.json"

for mode in oid path; do
  echo "== 4. 重写（mode=${mode}）"
  work="$out/work-$mode.git"
  rm -rf "$work"
  cp -Rc "$out/backup.git" "$work" 2>/dev/null || cp -R "$out/backup.git" "$work"
  git -C "$work" update-ref refs/heads/main "$sha"
  git -C "$work" symbolic-ref HEAD refs/heads/main
  git -C "$work" for-each-ref --format='%(refname)' refs/heads refs/remotes | grep -vx 'refs/heads/main' \
    | while read -r r; do git -C "$work" update-ref -d "$r"; done
  if [ "$mode" = oid ]; then
    "$py" "$here/measure.py" "$work" --follow "${follow[@]}" --gc --out "$out/before.json"
  fi
  "$py" "$here/filter_rules.py" "$work" --keep-dir "$out/keep" --mode "$mode" --report "$out/filter-$mode.json"
  "$py" "$here/measure.py" "$work" --follow "${follow[@]}" --gc --out "$out/after-$mode.json"
done

refs_after=$(git -C "$src" for-each-ref --format='%(refname) %(objectname)' | shasum -a 256)
[ "$refs_before" = "$refs_after" ] || { echo "真实仓 refs 在演练前后不一致！" >&2; exit 1; }
"$py" "$here/report.py" "$out" --src "$src" --rev "$rev" --sha "$sha" > "$out/rehearsal-report.md"
echo "== 完成：${out}/rehearsal-report.md（真实仓 refs 前后一致）"
