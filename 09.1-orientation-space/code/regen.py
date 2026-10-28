# 09.1-orientation-space 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 09.1-orientation-space/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_column_torus.py', minutes=0.3, note='图 2a 环面样图（待作者审图）'),
        Step('fig_parry_neighborhood.py', minutes=0.1, note='图 3 局部邻域候选（非全局嵌入，待审）'),
        Step('check_orientation_space.py', note='核验提纲数字（不产出文件）', default=False),
    ),
    helpers=('test_column_torus.py', 'test_parry_neighborhood.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
