# 10-radius-and-azimuth 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 10-radius-and-azimuth/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_plate_terrain.py', minutes=0.2, note='图 3c 地形样图（待作者审图）'),
        Step('check_parhelion.py', note='核验（不产出文件）', default=False),
        Step('check_parhelion_lumice.py', lumice=True, note='Lumice 对照核验（不产出文件）', default=False),
    ),
    helpers=('test_plate_terrain.py',),
)

if __name__ == "__main__":
    sys.exit(main(CH))
