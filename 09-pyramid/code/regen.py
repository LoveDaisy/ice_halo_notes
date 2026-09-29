# 09-pyramid 重生成入口：下面的步骤表是「从 git 内容重新得到本章全部图与数据」的唯一权威（按序执行）。
# 用法：uv run python 09-pyramid/code/regen.py [--dry-run | --only NAME … | --skip-lumice | --with-optional]；说明见 ../README.md。
import sys
from pathlib import Path

from halo_notes.repo.regen import Chapter, Step, main

CH = Chapter(
    code_dir=Path(__file__).resolve().parent,
    steps=(
        Step('enumerate_signatures.py', minutes=5, note='确定性枚举 → signature_table*.md/csv + raypaths_<tier>.csv'),
        Step('analyze_energy.py', lumice=True, minutes=15, note='Lumice analyze → energy_table.md + data/analysis/（top-3 / 逐族互证要读 analysis/rows_*.csv）；重跑会在 MC 误差内改写 energy_table.md'),
        Step('render_zenith.py', lumice=True, minutes=17, note='十景太阳天顶 dual 渲染 → data/zenith/<scene>.zip（图 4/5/6/8/9/10 取数）'),
        Step('fig_odd_radius_families.py', lumice=True, minutes=13),
        Step('fig_odd_radius_panorama.py', args=('--tier', 'h1_t0.5'), lumice=True, minutes=3),
        Step('fig_odd_radius_panorama.py', args=('--tier', 'h3_t0.25'), lumice=True, minutes=3),
        Step('fig_odd_radius_panorama.py', args=('--tier', 'h0.3_t0.85'), lumice=True, minutes=3),
        Step('fig_odd_radius_remainder.py', lumice=True, minutes=5),
        Step('fig_odd_radius_top3.py', lumice=True, minutes=3),
        Step('fig_plate_arcs.py', lumice=True, minutes=3, note='图 11 → data/plate_arcs.zip + img/plate_arcs.png'),
        Step('fig_pyramid_faces.py'),
        Step('fig_direct_wedges.py'),
        Step('fig_closure_growth.py'),
        Step('fig_corridor_1_3.py'),
        Step('fig_family_remainder.py'),
        Step('fig_isolated_ring.py'),
        Step('fig_panorama_triptych.py'),
        Step('fig_crowded_profiles.py'),
        Step('fig_off_family_ring.py'),
        Step('fig_fold_edge_density.py', args=('--recompute',), minutes=5, note='几何直接积分'),
        Step('check_pyramid.py', note='核验 framework 定理 6/7（不产出文件）', default=False),
        Step('make_compare.py', note='签核总览 → scratchpad（不入 git）', default=False),
    ),
    helpers=('_ch9_fig.py', '_ch9_sim.py', 'test_ch9_figs.py', 'test_odd_radius.py'),
)

if __name__ == "__main__":
    sys.exit(main(CH))
