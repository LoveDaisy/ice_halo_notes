# 09.1-orientation-space 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 09.1-orientation-space/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_axis_angle_ball.py', minutes=0.1, note='图 1 轴角球与典型晶体姿态逐点对应（1a/b 合并，待审）'),
        Step('fig_column_torus.py', minutes=0.3, note='图 2a 环面样图（待作者审图）'),
        Step('fig_plate_lowitz.py', minutes=0.3, note='图 2b 片晶圆与 Lowitz 环面（待审）'),
        Step('fig_parry_neighborhood.py', minutes=0.1, default=False, note='历史局部邻域对照，非当前交付图'),
        Step('fig_intersecting_tori.py', minutes=0.3, default=False, note='开窗构图对照，非当前主候选'),
        Step('fig_tori_section.py', minutes=0.3, note='图 3 径向错层剖切主候选（母圆交点与完整交圈，待审）'),
        Step('fig_euler_sampling.py', minutes=0.1, note='图 4a 仅同样本数方向点云（待审）'),
        Step('fig_euler_density.py', minutes=0.1, note='图 4b 相对密度极点发散（待审）'),
        Step('fig_sun_rotation.py', minutes=0.1, note='图 5a 绕太阳转、晶体系方向不变（待审）'),
        Step('fig_angle_fibers.py', minutes=0.1, note='图 5b 最短参考姿态坏点（降为局部辅助候选，待裁定）'),
        Step('make_compare.py', minutes=0.1, note='全篇 8 张待审图版及 SHA256 清单'),
        Step('check_orientation_space.py', note='核验提纲数字（不产出文件）', default=False),
    ),
    helpers=('test_column_torus.py', 'test_parry_neighborhood.py', 'test_intersecting_tori.py',
             'test_tori_section.py', 'test_concept_figures.py', '_orientation_fig.py', '_sun_rotation.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
