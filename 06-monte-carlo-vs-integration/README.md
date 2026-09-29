---
type: note
---

# 06-monte-carlo-vs-integration：重生成说明

本章在 git 里只有正文、被引用的插图、代码与小体积文本数据（config / provenance / csv / numbers.json 等）；原始渲染、中间数据、未被引用的图只留在本地，需要时按下面的入口重新生成。划界规则见仓库根 `AGENTS.md`「数据约定」。

## 重生成入口

```bash
uv sync
uv run python -m halo_notes.sim.fetch            # 按钉住版本拉 Lumice release 二进制到 .lumice/（首次）
uv run python 06-monte-carlo-vs-integration/code/regen.py --dry-run   # 列步骤：是否需要 Lumice、粗估墙钟
uv run python 06-monte-carlo-vs-integration/code/regen.py             # 按序执行默认步骤
```

步骤表（顺序、参数、哪些默认不跑）的唯一权威是 `code/regen.py`，这里不复述。常用选项：`--only NAME …` 只跑某几步、`--skip-lumice` 只重画不需要 Lumice 的图、`--with-optional` 连同核验脚本等默认不跑的步骤。

## 如何验证

- Lumice 是无固定 seed 的蒙特卡洛：重渲不逐字节复现。重生成后 `git status` 会看到入库的 config / provenance / lumice.log 与派生小文本（csv / numbers.json）变化，图与数字应在 MC 统计误差内与入库版本一致；确认后提交或 `git checkout` 还原。
- `uv run python -m halo_notes.repo.layout check-tree`：确认新产物没有漏出 `.gitignore`（0 条违规）。

## 不可重生成的项

- data/column1.0_direct.jpg：直接积分条带，本仓暂无 python 实现（legacy matlab + data_251x801.bin），作为 UNREGENERABLE_INPUTS 入 git
- data/*.jpg / *.png / data_251x801.bin（其余）：旧版 matlab / mathematica 时代的中间图与数据，已被 python 重制取代，只留本地
