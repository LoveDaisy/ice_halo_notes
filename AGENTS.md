# AGENTS.md

## 项目概述

知乎专栏「光怪陆离」系列文章《现代冰晕研究漫谈》的写作工程：每章正文（导演剪辑版 markdown）、配图、画图/仿真胶水代码、数据放在一起，按章分目录，git 管理版本。
本仓是 `~/Codes/Writing-Lab/` 下的一个系列工程，主 Obsidian vault 经 `Projects/现代冰晕研究漫谈` symlink 索引本仓，正文里的 wikilink 在 Obsidian 中正常解析。

写作模式（导演剪辑版 / 公开上映版、发表与回拉流程）见 `~/Virtual-Jiajie/Jiajie-Knowledge/WRITING-WORKFLOW.md`。

## 常用命令

本仓没有构建/测试概念。相关操作：

```bash
git lfs ls-files          # 图片/psd 全部走 LFS（见 .gitattributes）
obsidian rename file=<旧名> name=<新名>.md   # 重命名 md 必须走 Obsidian CLI（自动改 wikilink），禁裸 mv；分流判据见 skill obsidian-route
# ⚠ name= 必须带 .md，否则扩展名被吃掉；rename 后 Obsidian 会把 README 里的 markdown 链接改写成无目录的「最短路径」形式（GitHub 上会断），要改回显式相对路径
```

新章 python 画图代码的环境：系列根 `pyproject.toml`（待建，见「架构与设计」）。

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

### 当前状态（2026-09-11）

仍是 2022 年的旧布局：`halo0. Introduction and Motivation` ~ `halo7. Halo Detection by Transform`，图片/代码裸放在章根或 `img/`，代码为 `.m/.nb/.py` 混用。ch0–ch6 已发表，ch7 只有提纲。迁移到目标布局是 scratchpad 第一个任务。

### 外部依赖

- 仿真器：`~/Codes/Ice Halo Simulation`。本仓只放调仿真器 + 画图的胶水代码和参数，**不放仿真器本身**。旧脚本 `render_raypaths.py` 依赖的 `IceHaloEndless` 二进制已被仿真器项目删除，该脚本已失效，归 `legacy/`。
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
- `docs/framework.md` — 7–11 章共用的理论骨架（对象链、已核验定理、证据等级、未决）；`docs/checks/` 是其数值核验脚本，各章 bootstrap 时迁入 `code/`
- `.gitattributes` — LFS 规则
- `*/<副标题>.md` — 各章导演剪辑版正文（唯一 source）
- `~/Virtual-Jiajie/Jiajie-Knowledge/WRITING-WORKFLOW.md` — 写作工作模式约定（跨系列）
- `~/Virtual-Jiajie/Jiajie-Knowledge/Writing-Lab/README.md` — Writing-Lab 总约定

## 代码风格

- 正文：中文，知乎长文科普系列体，文风参照 skill `writing-voice`
- python：PEP 8，脚本顶部一行注释说明产出哪张图；依赖记入 `pyproject.toml`
- 旧 matlab / mathematica 代码：保持原样，不做风格改造
