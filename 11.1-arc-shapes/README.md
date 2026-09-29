---
type: note
---

# 11.1-arc-shapes：重生成说明

本章在 git 里只有正文、被引用的插图、代码与小体积文本数据（config / provenance / csv / numbers.json 等）；原始渲染、中间数据、未被引用的图只留在本地，需要时按下面的入口重新生成。划界规则见仓库根 `AGENTS.md`「数据约定」。

## 重生成入口

```bash
uv sync
uv run python 11.1-arc-shapes/code/regen.py --dry-run   # 列步骤：是否需要 Lumice、粗估墙钟
uv run python 11.1-arc-shapes/code/regen.py             # 按序执行默认步骤
```

步骤表（顺序、参数、哪些默认不跑）的唯一权威是 `code/regen.py`，这里不复述。常用选项：`--only NAME …` 只跑某几步、`--skip-lumice` 只重画不需要 Lumice 的图、`--with-optional` 连同核验脚本等默认不跑的步骤。

## 如何验证

- 本章目前只有核验脚本（默认不跑，`--with-optional` 或 `--only <脚本名>` 执行），不产出入库文件；脚本自身的断言 / 打印即验证结果。
