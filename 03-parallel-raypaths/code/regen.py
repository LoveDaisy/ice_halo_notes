# 03-parallel-raypaths 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 03-parallel-raypaths/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_ch3_standard_frame.py'),
        Step('fig_ch3_wedge_path.py'),
        Step('fig_rotation_steps.py'),
        Step('fig_tricker_arc_plot.py'),
        Step('fig_tricker_arc_cone_plot.py'),
        Step('fig_tricker_arc_raypath_expand.py'),
    ),
    not_regenerable=(
        ('data/raypath_ground_truth.txt、data/labeled_raypaths_5.csv', '原始出处（ch3 当年的光路清单），入 git，不由脚本生成'),
    ),
    helpers=('_tricker_arc.py',),
)

if __name__ == "__main__":
    sys.exit(main(CH))
