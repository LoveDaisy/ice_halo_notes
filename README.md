# 现代冰晕研究漫谈

知乎专栏「[光怪陆离](https://www.zhihu.com/column/OpticPhantasm)」系列文章《现代冰晕研究漫谈》的写作工程。每章的正文（导演剪辑版）、配图、画图/仿真胶水代码和数据放在一起，按章分目录，用 git 管理版本。

本仓是 `~/Codes/Writing-Lab/` 下的一个系列工程；主 Obsidian vault 经 `Projects/现代冰晕研究漫谈` symlink 索引本仓。公开上映版快照冻结在 vault `Writing/articles/`，本仓正文只演化不回改。

## 目录

| 章 | 目录 | 正文 | 状态 | 知乎 | 公开版快照 |
|---|---|---|---|---|---|
| 0 | `00-introduction/` | [风起青萍之末](00-introduction/风起青萍之末.md) | published | [p/461810067](https://zhuanlan.zhihu.com/p/461810067) | `[[现代冰晕研究漫谈(0)： 风起青萍之末]]` |
| 1 | `01-symmetry/` | [迷镜千幻不离宗](01-symmetry/迷镜千幻不离宗.md) | published | [p/462717356](https://zhuanlan.zhihu.com/p/462717356) | `[[现代冰晕研究漫谈(1)： 迷镜千幻不离宗]]` |
| 2 | `02-raypath-enumeration/` | [计算机遍历、搜索、优化](02-raypath-enumeration/计算机遍历-搜索-优化.md) | published | [p/469793197](https://zhuanlan.zhihu.com/p/469793197) | `[[现代冰晕研究漫谈(2)： 计算机遍历、搜索、优化]]` |
| 3 | `03-parallel-raypaths/` | [平行光路的各种弧和晕](03-parallel-raypaths/平行光路的各种弧和晕.md) | published | [p/485848284](https://zhuanlan.zhihu.com/p/485848284) | `[[现代冰晕研究漫谈(3)： 平行光路的各种弧和晕]]` |
| 4 | `04-render-equation/` | [冰晕模拟仿真的朴素(naive)思路](04-render-equation/冰晕模拟仿真的朴素思路.md) | published | [p/512594144](https://zhuanlan.zhihu.com/p/512594144) | `[[现代冰晕研究漫谈(4)： 冰晕模拟仿真的朴素(naive)思路]]` |
| 5 | `05-rotation-3d/` | [三维旋转](05-rotation-3d/三维旋转.md) | published | [p/516883186](https://zhuanlan.zhihu.com/p/516883186) | `[[现代冰晕研究漫谈(5)： 三维旋转]]` |
| 6 | `06-monte-carlo-vs-integration/` | [蒙特卡洛 vs. 直接积分](06-monte-carlo-vs-integration/蒙特卡洛%20vs.%20直接积分.md) | published | [p/536772578](https://zhuanlan.zhihu.com/p/536772578) | `[[现代冰晕研究漫谈(6)： 蒙特卡洛 vs. 直接积分]]` |
| 7 | `07-reflection-group/` | [为什么恰好是十二个](07-reflection-group/为什么恰好是十二个.md) | draft | — | — |
| 12 | `12-halo-detection/` | [变换法探测冰晕](12-halo-detection/变换法探测冰晕.md) | outline | — | — |

状态取值：`outline`（只有提纲）/ `draft`（写作中）/ `published`（已发表，正文冻结为导演剪辑版）。每章 md 的 frontmatter 是状态与链接的权威来源，本表随之同步。

## 布局

```text
NN-kebab-slug/         # 一章一目录
├── <副标题>.md         # 章正文（导演剪辑版），中文副标题命名
├── code/              # 本章专用画图/仿真脚本；一图一脚本：fig_<name>.py → ../img/<name>.png
│   └── legacy/        # 已失效或待 python 重做的旧 .m/.nb/.py（不删，作为已发表插图的出处）
├── img/               # 正文引用的图（含 .psd 源文件），正文中以 img/<file> 相对路径引用
└── data/              # 仿真输出、中间产物、数据表
halo_notes/            # 系列级共享 python 包（晶体几何、光路渲染、仿真器封装）
pyproject.toml         # 一个系列一个 python 环境
```

完整规范（DO / DO NOT）见 [AGENTS.md](AGENTS.md)。

## 工具链

- **git LFS**：图片、视频、psd、eps、svg 等二进制全部走 LFS（规则见 `.gitattributes`）。克隆后 `git lfs pull`；`git lfs ls-files` 应全部为 `*`（本地完整）。
- **Obsidian**：重命名 / 移动 md 文件必须走 `obsidian rename` / `obsidian move`（自动改写 wikilink），禁止裸 `mv` / `git mv`。只改目录名、不改 md 文件名时不受此限。
- **Python 环境**：`uv` 管理——系列根 `pyproject.toml` + `uv.lock`，每个 checkout（含 worktree）各自 `uv sync`，`uv run python <脚本>` / `uv run pytest`；不用 `pip install -e` 装进共享环境。新章画图/仿真代码一律 python，跨章复用的上提到 `halo_notes/`。
- **仿真器**：`~/Codes/Ice Halo Simulation`，本仓只放调用它的胶水代码与参数，不放仿真器本身。旧的 `render_raypaths.py`（ch2 / ch3 `code/legacy/`）依赖已删除的 `IceHaloEndless` 二进制，已失效。
- **旧脚本**：`.m` / `.nb` 保持原样放在各章 `code/`，被 python 重做后挪进 `code/legacy/`。
