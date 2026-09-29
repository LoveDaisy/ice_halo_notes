# 02-raypath-enumeration 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 02-raypath-enumeration/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_rp1_3_note.py', lumice=True, minutes=1),
        Step('fig_expand_rp132.py'),
        Step('fig_geo_validation.py'),
        Step('fig_light_corridor_rp132_00.py'),
        Step('fig_light_corridor_rp132_01.py'),
        Step('fig_light_corridor_rp132_02_note.py'),
        Step('fig_light_corridor_rp132_03.py'),
        Step('fig_light_corridor_rp31574.py'),
        Step('fig_tricker_arc_raypath.py'),
    ),
    helpers=('_light_corridor_rp132.py',),
)

if __name__ == "__main__":
    sys.exit(main(CH))
