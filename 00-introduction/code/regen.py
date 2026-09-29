# 00-introduction 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 00-introduction/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_all_halos.py', lumice=True, minutes=1.5, note='2e8 光线 dual fisheye → img/all_halos.jpg'),
        Step('fig_crystal03.py'),
    ),
)

if __name__ == "__main__":
    sys.exit(main(CH))
