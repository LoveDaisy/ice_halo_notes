# 09.1-orientation-space 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 09.1-orientation-space/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_axis_angle_ball.py', minutes=0.1, note='图 1a 轴角球对径认同（待审）'),
        Step('fig_rotation_seam.py', minutes=0.1, note='图 1b 固定轴连续转动与坐标跳边（待审）'),
        Step('fig_column_torus.py', minutes=0.3, note='图 2a 环面样图（待作者审图）'),
        Step('fig_plate_lowitz.py', minutes=0.3, note='图 2b 片晶圆与 Lowitz 环面（待审）'),
        Step('fig_parry_neighborhood.py', minutes=0.1, note='图 3 局部邻域候选（非全局嵌入，待审）'),
        Step('fig_intersecting_tori.py', minutes=0.3, note='图 3 两环面开窗扩展候选（两条原始交圈，待审）'),
        Step('fig_tori_section.py', minutes=0.3, note='图 3 径向错层剖切主候选（母圆交点与完整交圈，待审）'),
        Step('fig_euler_sampling.py', minutes=0.1, note='图 4a 同样本数方向点云与同桶份额（待审）'),
        Step('fig_euler_density.py', minutes=0.1, note='图 4b 相对密度极点发散（待审）'),
        Step('fig_sun_rotation.py', minutes=0.1, note='图 5a 绕太阳转、晶体系方向不变（待审）'),
        Step('fig_angle_fibers.py', minutes=0.1, note='图 5b 角纤维与相对卷绕（待审）'),
        Step('make_compare.py', minutes=0.1, note='全篇 9 张必需图待审比较版及 SHA256 清单'),
        Step('check_orientation_space.py', note='核验提纲数字（不产出文件）', default=False),
    ),
    helpers=('test_column_torus.py', 'test_parry_neighborhood.py', 'test_intersecting_tori.py',
             'test_tori_section.py', 'test_concept_figures.py', '_orientation_fig.py', '_sun_rotation.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
