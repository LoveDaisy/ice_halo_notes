# 07-reflection-group 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 07-reflection-group/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('sim_pose_to_sky_backdrop.py', lumice=True, minutes=3, note='7.5 右栏两张 Lumice 底图'),
        Step('fig_halos_columns.py', lumice=True, minutes=5, note='图 6a/6b 三个矩阵类各自仿真'),
        Step('fig_pose_to_sky.py', note='读 sim_pose_to_sky_backdrop 的底图'),
        Step('fig_pose_to_sky_gif.py', minutes=3),
        Step('fig_conjugate_rot90.py'),
        Step('fig_four_mirrors.py'),
        Step('fig_grid_6x2.py'),
        Step('fig_two_mirrors_120.py'),
        Step('check_group.py', note='核验 framework 定理 1/2/3/5（不产出文件）', default=False),
    ),
    helpers=('_ch7_sim.py', '_pose_to_sky.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
