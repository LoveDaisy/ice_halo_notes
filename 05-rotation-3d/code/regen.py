# 05-rotation-3d 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 05-rotation-3d/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_ch5_interp.py', minutes=1, note='gif 61 帧 + 静态三联'),
        Step('fig_hist01.py'),
        Step('fig_hist02.py'),
        Step('fig_numerical_err.py'),
        Step('fig_slerp_factor_explanation.py'),
    ),
    helpers=('matlab_style.py',),
)

if __name__ == "__main__":
    sys.exit(main(CH))
