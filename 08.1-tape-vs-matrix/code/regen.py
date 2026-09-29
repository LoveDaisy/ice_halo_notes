# 08.1-tape-vs-matrix 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 08.1-tape-vs-matrix/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('crosscheck_a.py', note='→ data/crosscheck_a_*.csv + summary'),
        Step('crosscheck_b.py', note='→ data/crosscheck_b_*.csv'),
        Step('fig_kaleidoscope.py'),
        Step('fig_concentric_projection.py'),
        Step('fig_unfold_3457.py'),
        Step('fig_plate_vs_column.py'),
        Step('fig_two_matrices.py', note='读 ch8 data/signature_table.md'),
    ),
    helpers=('_ex_fig.py', 'crosscheck_bridge.py', 'tape_halo_function.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
