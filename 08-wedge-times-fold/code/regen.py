# 08-wedge-times-fold 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 08-wedge-times-fold/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('enumerate_signatures.py', minutes=4.5, note='确定性枚举 → data/signature_table.md + signature_table_<ha>.csv'),
        Step('check_ground_truth_signature.py', note='→ data/ground_truth_signature.md'),
        Step('analyze_energy.py', lumice=True, minutes=10, note='Lumice analyze → data/energy_table.md（现存表为 4.6.1 发版前本地 build 产出、provenance 已记；本章无其它脚本读 analysis/，默认不重跑）', default=False),
        Step('fig_b1_same_class.py', lumice=True, minutes=6, note='图 B1：3 条单光路 + 3 张参考渲染'),
        Step('fig_b2_unnamed_cell.py', lumice=True, minutes=11.5, note='图 6：globe + rect + 3 张参考渲染 → far_side_profile.csv / numbers'),
        Step('fig_cross_section_sensitivity.py', lumice=True, minutes=9.5, note='图 7：4 档 d × 2 类 → cross_section_sensitivity*.csv'),
        Step('fig_cross_section_renders.py', lumice=True, minutes=6.5, note='图 7 配图：4 档 d 全光路渲染'),
        Step('fig_unfold_wedge_fold.py'),
        Step('fig_five_wedges.py'),
        Step('fig_phi_class_grid.py', note='读 data/signature_table.md'),
        Step('fig_direction_scan.py'),
        Step('check_signature.py', note='核验 framework 定理 5′（不产出文件）', default=False),
    ),
    helpers=('_ch8_plot.py', '_ch8_sim.py', 'test_ch8_sim.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
