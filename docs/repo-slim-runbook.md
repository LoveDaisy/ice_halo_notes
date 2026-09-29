---
type: note
---

# repo-slim 执行手册：重写历史 → 删库 → 同名重建

> 本手册只写不执行；由主会话逐步执行，**每个标 ⛔ 的步骤先让作者确认**。
> 工具在 `tools/history-rewrite/`，划界规则的唯一实现是 `halo_notes/repo/layout.py`（AGENTS.md「数据约定」）。
> 演练记录：`scratchpad/task-repo-slim/rehearsal-report.md`（2026-09-29，输入为本地主仓，`task/repo-slim` 当作 `main`）。

## 演练结论（供裁定）

| | 提交数 | LFS 对象 | LFS 总量 | 本地缺的 LFS 对象 | git 包 |
|---|---|---|---|---|---|
| 重写前（本地 mirror，全部 refs） | 339 | 399 | 479.4 MB | 100 | 24.7 MiB |
| 重写后 · oid 精确保留（默认） | 336 | 69 | 42.0 MB | 0 | 4.3 MiB |
| 重写后 · 仅按路径保留 | 339 | 153 | 98.7 MB | 36 | 7.8 MiB |

「本地缺的 LFS 对象」= 历史 pointer 引用、但本地 LFS 存储里没有的对象（可能只在 GitHub 上，也可能已丢失）；oid 模式保留的对象本地全有，
path 模式要先从 GitHub 补齐这 36 个才能完整推送。

- 「被引用插图」**按 HEAD 时刻的引用集合、精确到内容 oid** 判定（默认）。理由：
  (a) 目标是瘦身，按每个提交当时的引用会把所有被替换过的旧版图都留下，体量接近现状；
  (b) 只按 HEAD 路径保留时，同一路径反复覆盖的旧版本仍被历史 pointer 引用，`git lfs push --all` 会全部上传（演练：98.7 MB vs 42.0 MB）；
  (c) 旧提交里的 md 图链在旧版本图缺失时会「断」，但没人 checkout 旧提交看图，要保的是 md / 代码的演化历史。
  另外，oid 模式下内容 oid 在保留集里的文件连改名前的旧路径也保留（不增加 LFS 体量），重组前的旧提交里这些图照常可看。
- md 历史完整：抽查 4 个文件（ch1 / ch6 / ch8 正文与 `docs/roadmap.md`）的 `git log --follow`，重写前后提交数与标题序列逐条一致。
- 被丢弃的还有 2022 年曾用 LFS 跟踪的仿真器可执行文件 `halo2. All Possible Raypaths/IceHaloEndless`（规则：LFS 存储的二进制且未被引用）。
- 3 个提交在重写后变空（只改了被丢弃的文件），由 filter-repo 自动裁剪；它们在 commit-map 里映射为全 0。
- 被保留的非 LFS 大 blob 只有 legacy `plot_figures.nb`（2.06 MB，AGENTS 规定不删旧 `.nb`）；没有按大小一刀切的兜底删除（演练实测那样会误删它）。
- commit message 里的旧短哈希由 filter-repo 默认改写为新哈希（不加 `--preserve-commit-hashes`）。

## 远端旧分支 ch2–ch5

核对（2026-09-29）：

```bash
for b in ch2 ch3 ch4 ch5; do
  git merge-base --is-ancestor origin/$b origin/main && echo "$b 已并入 main，领先 $(git rev-list --count origin/main..origin/$b) 个提交"
done
```

四条都已并入 `origin/main`、领先 0 个提交。**建议删除**：重建的新库只推 `main`（本仓没有 tag），这四条自然消失；本地同名分支（`ch2`–`ch5`）同样可以删除。

## 步骤

以下 `$MAIN` = 本地主仓（`~/Codes/Writing-Lab/现代冰晕研究漫谈`），`$B` = 备份目录（放在仓库之外，例如 `~/Backups/ice_halo_notes-<日期>`）。

### (0) 前置

```bash
cd $MAIN
git worktree list                  # 只剩主仓一行；其余 worktree 先合并或放弃、git worktree remove
git status --short                 # 干净
git branch --no-merged main        # 为空；非空则逐个确认合并或放弃
git log origin/main..main --oneline | wc -l   # 本地待推提交数（演练时 131），这些只在本地——备份必须取自本地
```

task/repo-slim 已合入 main；`uv run python -m halo_notes.repo.layout check-tree` 为 0 条违规。

### (1) 备份（输入取自本地主仓，不取远端）

```bash
mkdir -p $B
git clone --mirror $MAIN $B/backup.git
tools/lfs-import.sh "$(git -C $MAIN rev-parse --path-format=absolute --git-common-dir)" $B/backup.git \
  < <(find $MAIN/.git/lfs/objects -type f -not -name '*.tmp' -exec basename {} \;)
git -C $B/backup.git remote add github git@github.com:LoveDaisy/ice_halo_notes.git
git -C $B/backup.git lfs fetch --all github      # 补齐只在 GitHub 上的对象（本地已删的旧版本）
```

**可恢复性验证**：

```bash
git clone file://$B/backup.git $B/verify         # smudge 从备份拉 HEAD 的 LFS 对象
cd $B/verify
git lfs fsck                                     # OK
git lfs fetch --all                              # 全部历史对象；缺失的逐个列出（演练中 1 个：2022 年的旧版 rp31_01.png，
                                                 # 本地与备份都没有，且不在保留集里——重写时本就丢弃）
diff <(git -C $MAIN for-each-ref --format='%(refname) %(objectname)' refs/heads refs/tags) \
     <(git -C $B/backup.git for-each-ref --format='%(refname) %(objectname)' refs/heads refs/tags)   # 无输出
```

`fetch --all` 报缺的对象要逐个查（`git log --all -S<oid> --name-only`）：只要不在 `keep/keep_oids.txt` 里就不影响重写结果。

### (2) ⛔ 在 mirror 副本上重写

作者先据上面两套数字裁定 **oid 精确保留（默认）** 还是 **仅按路径保留**。然后：

```bash
tools/history-rewrite/rehearse.sh $MAIN $B/run main   # 重新做一遍全流程（含两种模式），产出 $B/run/work-{oid,path}.git
```

或只做选定模式（等价于 rehearse.sh 里的一段）：

```bash
PY=$(head -1 "$(command -v git-filter-repo)" | sed 's/^#!//')   # 装了 git_filter_repo 的 python
$PY tools/history-rewrite/build_keep_set.py $B/backup.git --rev main --out $B/keep
cp -Rc $B/backup.git $B/work.git
git -C $B/work.git for-each-ref --format='%(refname)' refs/heads refs/remotes | grep -vx refs/heads/main \
  | while read -r r; do git -C $B/work.git update-ref -d "$r"; done
$PY tools/history-rewrite/filter_rules.py $B/work.git --keep-dir $B/keep --mode oid --report $B/filter.json
```

- HEAD 若在演练之后新增了引用图，`build_keep_set.py` 必须重跑（`keep_oids.txt` 与 HEAD 同基线）。
- 重写后、删库前，逐一确认保留下来的 pointer 在本地都有对象：

```bash
git -C $B/work.git lfs ls-files --all --long | awk '{print $1}' | sort -u | while read -r oid; do
  [ -f "$B/work.git/lfs/objects/${oid:0:2}/${oid:2:2}/$oid" ] || echo "缺 $oid"
done                                                  # 无输出
```

- 核对：`git -C $B/work.git log --oneline | wc -l`、`git log --follow` 抽查若干 md、报告里「被保留的非 LFS 大 blob」清单。

### (3) 哈希替换

```bash
MAP=$B/work.git/filter-repo/commit-map
python3 tools/history-rewrite/remap_hashes.py --old $B/backup.git --map $MAP \
  --paths docs README.md AGENTS.md [0-9]*/ scratchpad/ --report $B/remap.json          # dry-run：看清单
```

演练（dry-run）：扫描 4775 个文件，320 个十六进制词是旧仓 commit，759 处（359 个文件）待替换；2 处指向被裁剪的空提交、139 处是旧仓里已不可达的提交（被 amend / rebase 掉的），均不替换、列入清单。确认后：

- `scratchpad/` 是本地文件（不入 git）：在 `$MAIN` 上 `--apply` 即可。
- 入 git 的 `docs/`、各章 md / 代码注释：在重写后的仓库上改。先 `git clone $B/work.git $B/wc`，对 `$B/wc` 跑 `remap_hashes.py --apply`（`--old` 仍指向备份），在 `$B/wc` 提交一次 `docs: 旧 commit 哈希替换为重写后的哈希`，`git -C $B/wc push origin main` 回到 `$B/work.git`（LFS 对象已在 work.git 里）。

### (4) ⛔ 删库、同名重建、推送

1. GitHub 上删除 `LoveDaisy/ice_halo_notes`（不可逆；备份与 `$B/verify` 验证通过之后才做）。
2. 新建同名空仓库（不勾选 README / license），可见性与原库一致。
3. 推送（新库尚未装 pre-push 闸；若已装，首推约 42 MB 会超 30 MB 预算，需 `SLIM_PUSH_OVERRIDE="repo rebuild"`）：

```bash
cd $B/work.git
git remote remove origin 2>/dev/null; git remote add origin git@github.com:LoveDaisy/ice_halo_notes.git
git push origin main
git lfs push --all origin main
```

### (5) 推送后校验

```bash
git clone git@github.com:LoveDaisy/ice_halo_notes.git $B/fresh && cd $B/fresh
git lfs ls-files | awk '{print $2}' | sort | uniq -c        # 全部 "*"
git lfs fsck
git rev-list --count main                                   # 与 work.git 一致
du -sh .git
uv sync && uv run pytest -q                                 # 全绿，local_data 测试 skip 并写明原因
uv run python -m halo_notes.repo.layout check-tree          # 0 条违规
```

另在 GitHub 仓库 Settings → Billing / LFS 看存储用量（预期 ≈ 42 MB），README 里的链接逐个点开。

### (6) 本地 checkout 的处理

重写后所有提交哈希都变了：**重新 clone，不要在旧 clone 上 pull**。

```bash
mv $MAIN $MAIN.pre-slim                                     # 旧 clone 暂留，确认无误后再删
git clone git@github.com:LoveDaisy/ice_halo_notes.git $MAIN
# 把只留本地的产物（data/ 原始渲染、未被引用的图、scratchpad/、.lumice/）从旧 clone 搬过来：
rsync -a --ignore-existing $MAIN.pre-slim/ $MAIN/ --exclude .git --exclude .venv
cd $MAIN && uv sync && tools/hooks/install.sh               # 装 pre-push 闸（首推已完成，之后按预算走）
git status --short                                          # 应为空：搬回来的本地产物都被 .gitignore 覆盖
```

Obsidian vault 的 `Projects/现代冰晕研究漫谈` symlink 指向的是目录路径，重新 clone 到同一路径后无需改动。

### (7) 回退

`$B/backup.git`（含全部 LFS 对象）即回退点：如需回到重写前，新建仓库后 `git -C $B/backup.git push --mirror <url>` 并 `git -C $B/backup.git lfs push --all <url>`。在作者确认新库稳定之前不删 `$B`。
