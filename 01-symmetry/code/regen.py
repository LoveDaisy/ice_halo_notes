# 01-symmetry 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 01-symmetry/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_halos_3_5.py', lumice=True, minutes=1),
        Step('fig_c6.py'),
        Step('fig_c6_table.py'),
        Step('fig_d6_f.py'),
        Step('fig_d6_table_shade.py'),
        Step('fig_raypath_symmetry.py'),
    ),
    helpers=('group_table.py',),
)

if __name__ == "__main__":
    sys.exit(main(CH))
