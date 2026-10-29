# 产出 ../img/column_sky.png：太阳 20° 上切弧的真实线性 MC 天图与同心角距参照。
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import _sky_fig as F
from check_parhelion import bravais, critical_height, spherical_distance
from fig_sky_comparison import PAL, obtain, panel_geometry, style, tone
from halo_notes.sim.fetch import sha256_of
from halo_notes.sim.projection import project_equal_area
from halo_notes.sim.raypath_probe import sun_direction

RADII = (22, 25, 30, 40, 50)
ALTITUDE = 20
UPPER_VIEW_BOTTOM = 500  # 保留绕到太阳水平线以下的上切弧尾；下切弧起点约 y=564。


def ring_directions(radius, position_angle):
    """以太阳为中心，位置角从上向右增加；世界方向交公共等面积投影。"""
    sun = -sun_direction(ALTITUDE)
    h = np.radians(ALTITUDE)
    up = np.array([-np.sin(h), 0, np.cos(h)])
    right = np.array([0, 1, 0])
    pa, r = np.radians(position_angle), np.radians(radius)
    return np.cos(r) * sun + np.sin(r) * (np.cos(pa)[..., None] * up + np.sin(pa)[..., None] * right)


def evidence():
    folder = F.DATA / F.name("column", ALTITUDE)
    energy, cfg, _ = F.load_scene(folder)
    d, pa, dirs = F.angular_data(cfg)
    lit = energy > 0
    uv = project_equal_area(dirs.reshape(-1, 3), cfg["render"][1]).reshape(*d.shape, 2)
    upper = uv[..., 1] < UPPER_VIEW_BOTTOM
    # 裁窗必须落在两支之间的空隙，而非正好沿太阳水平线切掉上切弧末端。
    gap = (uv[..., 1] > UPPER_VIEW_BOTTOM - 30) & (uv[..., 1] < UPPER_VIEW_BOTTOM + 30)
    if (lit & gap).any():
        raise RuntimeError("上/下切弧裁窗交界出现非零像素；不可裁掉真实光，先复查取景")
    k = int(np.argmax(np.where(lit & upper, d, -1)))
    # 掠入/掠出极限：Bravais n'=2、水平偏折120°。只作反证闸，不当成可见边缘。
    hc = critical_height()
    optical_sup = float(spherical_distance(hc, 120))
    pixel_radius_bound = np.sqrt(2) * 180 / cfg["render"][0]["resolution"][0]
    sun_radius = cfg["scene"]["light_source"]["diameter"] / 2
    report = F.measure_scene(folder)
    report.update({"upper_only": True, "upper_view_bottom_pixel": UPPER_VIEW_BOTTOM,
                   "split_gap_nonzero_pixels": int((lit & gap).sum()),
                   "optical_supremum_deg": optical_sup,
                   "pixel_center_error_bound_deg": pixel_radius_bound, "sun_radius_deg": sun_radius,
                   "upper_outermost_pixel_deg": float(d.flat[k]),
                   "upper_outermost_direction": dirs.reshape(-1, 3)[k].tolist(),
                   "rings_upper": []})
    for radius in RADII:
        shell = upper & (np.abs(d - radius) <= .3)
        angles = np.where(pa > 180, pa - 360, pa)
        hist, _ = np.histogram(angles[shell], bins=np.arange(-90, 91, 2), weights=energy[shell])
        # 两侧最亮的 2° 桶，留全部桶为真正判据，不宣称非零支持只含两点。
        peaks = []
        for start, end in ((0, 45), (45, 90)):
            j = start + int(np.argmax(hist[start:end]))
            peaks.append(None if hist[j] == 0 else -89 + 2 * j)
        report["rings_upper"].append({"radius_deg": radius, "half_width_deg": .3,
                                       "pa_edges_deg": list(range(-90, 91, 2)),
                                       "bin_Y_per_emitted_energy": hist.tolist(),
                                       "peak_pa_left_right_deg": peaks})
    report["beyond_optical_bound_pixels"] = int((lit & (d > optical_sup + sun_radius + pixel_radius_bound)).sum())
    return report, cfg


def draw(*, render=False, replot=False, output=None):
    style()
    out = Path(output) if output is not None else F.IMG / "column_sky.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    meta_path = out.with_suffix(".json") if output is not None else F.DATA / "column_sky_evidence.json"
    y, cfg, _ = obtain("column", ALTITUDE, render=render, replot=replot)
    report, _ = evidence()
    meta_path.write_text(json.dumps(report, indent=2) + "\n")
    if report["beyond_optical_bound_pixels"]:
        raise RuntimeError(f"出现超过光学外界+有限日面+像素误差的真实能量；停止图7，检查 {meta_path}")
    white = float(np.quantile(y[y > 0], .995))
    fig, ax = plt.subplots(figsize=(12, 7.1))
    fig.subplots_adjust(left=.035, right=.965, bottom=.19, top=.9)
    ax.imshow(tone(y, white), cmap="gray", vmin=0, vmax=1,
              extent=(0, F.DISPLAY_RES[0], F.DISPLAY_RES[1], 0), interpolation="none")
    unit = cfg["render"][1]
    for radius, label_pa in zip(RADII[:-1], (-43, -30, -22, -16)):
        uv = project_equal_area(ring_directions(radius, np.linspace(-110, 110, 881)), unit)
        ax.plot(*uv.T, color=PAL["slate"], lw=.8, ls=(0, (4, 4)), alpha=.85)
        pos = project_equal_area(ring_directions(radius, np.array([label_pa])), unit)[0]
        ax.text(*pos, f"{radius}°", ha="right", va="bottom", fontsize=11,
                color=PAL["ink_faint"], bbox={"facecolor": PAL["ink"], "edgecolor": "none", "pad": 1})
    panel_geometry(ax, ALTITUDE, cfg, horizon=False)
    # 只缩小垂直视窗到上切弧；左右仍含全部上半图，绝不按能量阈值裁掉外侧弱光。
    ax.set_ylim(UPPER_VIEW_BOTTOM, 0)
    ax.set_title("太阳高度 20°  ·  只看上切弧", fontsize=16, pad=13)
    bound = report['optical_supremum_deg']
    uv = project_equal_area(ring_directions(bound, np.linspace(-110, 110, 881)), unit)
    boundary, = ax.plot(*uv.T, color=PAL['ink_faint'], lw=1.0, ls=(0, (8, 4)))
    boundary.set_gid('grazing-supremum')
    target = project_equal_area(ring_directions(bound, np.array([48.])), unit)[0]
    ax.annotate(f'几何上确界 {bound:.2f}°', xy=target, xytext=(600, 350),
                ha='center', color=PAL['ink_faint'], fontsize=11,
                arrowprops={'arrowstyle': '-', 'color': PAL['ink_faint'], 'lw': .7})
    ax.annotate("相切处", xy=project_equal_area(ring_directions(bravais(0)[1], np.array([0])), unit)[0],
                xytext=(445, 285), color=PAL["ink_faint"], fontsize=11,
                arrowprops={"arrowstyle": "-", "color": PAL["ink_faint"], "lw": .7})
    fig.text(.5, .09, "虚线标角距，真实光只照亮其中的部分弧段；明亮的弧缘之外仍有弱光。\n"
             "外侧长虚线是掠射上界：透射趋零，不是最后一处可见亮像。",
             ha="center", va="center", fontsize=12, linespacing=1.8)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    report.update({"figure_sha256": sha256_of(out), "display_white": white,
                   "display_raw_sha256": sha256_of(F.DATA / F.name("column", ALTITUDE) / "img_02.npy")})
    meta_path.write_text(json.dumps(report, indent=2) + "\n")
    print(out)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group()
    group.add_argument("--render", action="store_true")
    group.add_argument("--replot", action="store_true")
    p.add_argument("--output", type=Path, help="输出图片路径；派生JSON写在同目录同名.json，不改章内成图/派生元数据")
    args = p.parse_args(argv)
    draw(render=args.render, replot=args.replot, output=args.output)


if __name__ == "__main__":
    main()
