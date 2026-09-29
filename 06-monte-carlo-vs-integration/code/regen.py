# 06-monte-carlo-vs-integration 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 06-monte-carlo-vs-integration/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_dual_fisheye.py', lumice=True, minutes=1),
        Step('fig_compare_two_methods.py', lumice=True, minutes=5, note='globe 全天 + 1e7/1e8/1e9 三条带；第四条带读入库的 data/column1.0_direct.jpg'),
        Step('fig_crystal_pose.py'),
        Step('fig_trace.py'),
    ),
    not_regenerable=(
        ('data/column1.0_direct.jpg', '直接积分条带，本仓暂无 python 实现（legacy matlab + data_251x801.bin），作为 UNREGENERABLE_INPUTS 入 git'),
        ('data/*.jpg / *.png / data_251x801.bin（其余）', '旧版 matlab / mathematica 时代的中间图与数据，已被 python 重制取代，只留本地'),
    ),
)

if __name__ == "__main__":
    sys.exit(main(CH))
