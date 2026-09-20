# AGENTS.md

## 项目概述

知乎专栏「光怪陆离」系列文章《现代冰晕研究漫谈》的写作工程：每章正文（导演剪辑版 markdown）、配图、画图/仿真胶水代码、数据放在一起，按章分目录，git 管理版本。
本仓是 `~/Codes/Writing-Lab/` 下的一个系列工程，主 Obsidian vault 经 `Projects/现代冰晕研究漫谈` symlink 索引本仓，正文里的 wikilink 在 Obsidian 中正常解析。

写作模式（导演剪辑版 / 公开上映版、发表与回拉流程）见 `~/Virtual-Jiajie/Jiajie-Knowledge/WRITING-WORKFLOW.md`。

## 常用命令

本仓没有构建概念；python 环境由 `uv` 管理（系列根 `pyproject.toml` + `uv.lock` 入库，`.venv/` 忽略）：

```bash
uv sync                                     # 建 .venv 并按 uv.lock 装依赖（含 dev 组 pytest；halo_notes 以可编辑方式装入）
uv run python 02-raypath-enumeration/code/fig_expand_rp132.py   # 跑画图脚本（脚本用 __file__ 定位 ../img，可在任意 cwd 运行）
uv run pytest                               # 全量单测；halo_notes/draw/tests/test_figures.py 逐图核验画出的光路语义
git lfs ls-files          # 图片/psd 全部走 LFS（见 .gitattributes）
obsidian rename file=<旧名> name=<新名>.md   # 重命名 md 必须走 Obsidian CLI（自动改 wikilink），禁裸 mv；分流判据见 skill obsidian-route
# ⚠ name= 必须带 .md，否则扩展名被吃掉；rename 后 Obsidian 会把 README 里的 markdown 链接改写成无目录的「最短路径」形式（GitHub 上会断），要改回显式相对路径
```

**每个 checkout（含 git worktree）各自 `uv sync`**，不用 `pip install -e` 装进共享的 conda 环境——editable install 只认一条源路径，多 worktree 并行时会互相踩（见 `scratchpad/learnings.md`）。

## 架构与设计

### 目标布局（规范）

```text
.
├── README.md              # 系列目录、各章状态（outline/draft/published + 知乎链接）、工具链说明
├── pyproject.toml         # 一个系列一个 python 环境
├── halo_notes/            # 系列级共享代码（晶体几何、光路渲染、调仿真器封装）
├── NN-kebab-slug/         # 一章一目录，两位零填充序号 + 英文 slug
│   ├── <副标题>.md         # 章正文，中文副标题命名（不带「现代冰晕研究漫谈(N)：」前缀）
│   ├── <笔记>.md           # 章内工作笔记（推导、归总），与正文同级，frontmatter `type: note`
│   ├── code/              # 本章专用脚本；一图一脚本：fig_<name>.py → ../img/<name>.png
│   │   └── legacy/        # 已被 python 重做的旧 matlab/mathematica 脚本（不删，作为已发表插图的出处）
│   ├── img/
│   └── data/
└── scratchpad/            # 任务管理（不入 git）
```

### 当前状态（2026-09-20）

目标布局已落地。ch0–ch8 published（ch7 2026-09-14、ch8 2026-09-20 发表，公开版已回拉进 vault `Writing/articles/`；ch8 两张曲线图共用 `code/_ch8_plot.py` 外观，`fig_b2_unnamed_cell.py` / `fig_cross_section_sensitivity.py` 支持 `--replot` 从 data/ 重画），ch12 outline；ch9 与番外「Tape 光点法 vs 矩阵法」处于写作准备（scrum `ch9-prep` / `ex-tape-prep`，见 `docs/roadmap.md`）。几何本体（`Polyhedron` / `HexPrism` / `Pyramid` / `unfold_faces`；`feasibility` 方向扫描 + 凸多边形投影求交的光路可行性判定，`enumerate` DFS 单调剪枝 + 调用方注入对称轨道去重的可行光路枚举器——ch2 枚举器的 python 复活）自 2026-09-18 起**由 `lumice_integral.geometry` 提供**（Lumice Integral 仓，本仓以指向本机 LI 仓的 git 源（`file://` 绝对 URL + 钉住 rev，见 `pyproject.toml` 注释：path 依赖在 uv.lock 里会按 checkout 相对深度改写，主仓与 worktree 互相踩）引入，`halo_notes/geometry/` 副本已删除，`draw/geometry.py` 是其 re-export shim；要用 LI 新改动须先在 LI 仓 commit 再 bump rev；LI 正式发布后换 GitHub + tag 另立任务）。`halo_notes/` 现有 `draw` / `math`（含 `ground_truth` ch3 光路清单解析；`signature`：signature 规范型、带定义域的 Φ 指纹、六棱柱 34 类全类表；ch8 `data/signature_table*` 由 `enumerate_signatures.py` 产出，五档 h/a 下界已算）/ `sim`（含 `analyze`：Lumice 4.6.x `analyze` 子命令胶水——随机朝向光路分析 CSV → Φ 类能量份额 / 与枚举器互证；ch8 `data/energy_table.md` 由 `analyze_energy.py` 产出，需本地 build `LUMICE_BIN`）四包；35 张旧图已重制 34 张（余 6.4 等直接积分项目，后排）。

### 外部依赖

- 仿真器：Lumice（`~/Codes/Ice Halo Simulation`，GitHub `LoveDaisy/ice_halo_sim`）。本仓只放调仿真器 + 画图的胶水代码和参数（`halo_notes/sim/`），**不放仿真器本身**：版本钉在 `halo_notes/sim/fetch.py` 的 `LUMICE_VERSION`，`uv run python -m halo_notes.sim.fetch` 按该版本从 GitHub release 拉 CLI 二进制到 `.lumice/`（gitignore）；`LUMICE_BIN` 环境变量可指向本地 build 做对照，正式出图一律用 release 版；`analyze` 子命令（光路分析）release v4.5.1 还没有，ch8 `analyze_energy.py` 暂靠本地 build（provenance 记 `local_build: true` + Ice Halo 仓 HEAD + 二进制 sha256），4.6.1 发版后切回 `fetch.py`。每张仿真图的 config 落 `data/<name>.lumice.json`，原始输出 + `provenance.json` 落 `data/<name>/`。真跑 Lumice CLI 的慢测试标了 `@pytest.mark.slow`，`uv run pytest` 默认跳过，需要真跑时用 `uv run pytest -m slow`（要求能拉到 / 已缓存 `.lumice/` 二进制）。旧脚本 `render_raypaths.py` 依赖的 `IceHaloEndless` 二进制已被仿真器项目删除，该脚本已失效，归 `legacy/`。
- 主 vault：`~/Virtual-Jiajie/Jiajie-Knowledge/Obsidian-Vault/`。公开上映版快照在 `Writing/articles/现代冰晕研究漫谈(N)： *.md`，系列 MOC 在 `Writing/series/现代冰晕研究漫谈.md`。

## 重要约束

### DO NOT

- 不重写已发表章节的正文；公开版冻结在 vault `Writing/`，本仓里的是导演剪辑版，只演化不回改
- 不把章正文命名为 `draft.md` 或带系列前缀的全名：前者在 Obsidian 里多章同名产生 wikilink 歧义，后者与 vault 里的公开版快照撞名
- 不裸 `mv` / `git mv` 重命名 md 文件（wikilink 会断）；重命名走 `obsidian rename`
- 不删旧 `.m/.nb` 脚本；被 python 重做后挪 `code/legacy/`
- 不把仿真器源码或二进制放进本仓
- 不改写 git 历史，一律 append commit

### DO

- 新章画图/仿真代码一律 python；跨章复用的代码上提到 `halo_notes/`，章内 `code/` 只放章专属脚本
- 一图一脚本，脚本名与图名对应
- 每章正文 md 带 frontmatter：`type: directors-cut`、`status: outline | draft | published`、发表后补 `published: "[[公开版文件名]]"` 与 `url:`；章内工作笔记只带 `type: note`，与正文同级放置（暂不设子目录，有需要再改）
- 未写章的提纲直接写在该章 md 里（`status: outline`），不用单独的 guideline.txt
- 图片/psd 等二进制走 LFS（`.gitattributes` 已配）
- 使用 `scratchpad/` 目录管理任务（详见 `scratchpad/common.md`）

## 关键文件

- `README.md` — 系列目录与各章状态，是规范的第一份载体
- `docs/roadmap.md` — 系列路线图（正向 / 反向 / 番外）与 `halo_notes/` 需求汇总
- `docs/errata.md` — 已发表各章的勘误表（发现即登记，改不改由作者裁定）
- `docs/framework.md` — 7–11 章共用的理论骨架（对象链、已核验定理、证据等级、未决）；`docs/checks/` 存放尚未起章的核验脚本（现仅 ch9 的 `check_pyramid.py`），起章时迁入该章 `code/`
- `.gitattributes` — LFS 规则
- `*/<副标题>.md` — 各章导演剪辑版正文（唯一 source）
- `~/Virtual-Jiajie/Jiajie-Knowledge/WRITING-WORKFLOW.md` — 写作工作模式约定（跨系列）
- `~/Virtual-Jiajie/Jiajie-Knowledge/Writing-Lab/README.md` — Writing-Lab 总约定

## 代码风格

- 正文：中文，知乎长文科普系列体，文风参照 skill `writing-voice`
- python：PEP 8，脚本顶部一行注释说明产出哪张图；依赖记入 `pyproject.toml`
- 旧 matlab / mathematica 代码：保持原样，不做风格改造
