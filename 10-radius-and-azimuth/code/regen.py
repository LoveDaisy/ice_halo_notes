# 10-radius-and-azimuth 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 10-radius-and-azimuth/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('fig_sky_comparison.py', lumice=True, minutes=1.2,
             note='图 1：同路径三族四高度；缺同配置缓存时跑 release'),
        Step('fig_solar_circle.py', minutes=0.1, note='图 2：同源绕太阳动作与等角距轨迹'),
        Step('fig_terrain_domain.py', minutes=0.1, note='图 3a：光学定义域与等值线'),
        Step('fig_random_terrain.py', minutes=0.1, note='图 3b：随机取向的整球'),
        Step('fig_plate_terrain.py', minutes=0.2, note='图 3c：片晶纬线与临界闭包切点'),
        Step('fig_column_terrain.py', minutes=0.1, note='图 3d：柱晶可取带'),
        Step('fig_bravais_prism.py', minutes=0.1, note='图 4：沿棱守恒与水平截面'),
        Step('fig_parhelion_rulers.py', minutes=0.1, note='图 5：角距离与方位差'),
        Step('fig_tangent_direction.py', minutes=0.1, note='图 6：真实柱晶姿态与几何切点'),
        Step('fig_column_sky.py', lumice=True, minutes=0.2,
             note='图 7：复用图1的20°柱晶原始数据；缺缓存时仅重渲该景'),
        Step('make_compare.py', minutes=0.1, note='十图拼版及当前版本清单；不是作者签核'),
        Step('check_parhelion.py', note='核验（不产出文件）', default=False),
        Step('check_parhelion_lumice.py', lumice=True, note='Lumice 对照核验（不产出文件）', default=False),
    ),
    helpers=('test_plate_terrain.py', '_terrain_layers.py', 'test_ch10_geometry.py',
             'test_prism_figures.py', '_sky_fig.py', 'test_sky_figures.py',
             'test_bravais_revision.py', 'test_rulers_revision.py',
             'test_tangent_revision.py', 'test_review_revision.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
