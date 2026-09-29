# 12.1-liljequist 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 12.1-liljequist/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('check_liljequist_sensitivity.py', note='核验（不产出文件）', default=False),
    ),
)

if __name__ == "__main__":
    sys.exit(main(CH))
