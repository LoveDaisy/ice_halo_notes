# 产出 ../img/light_corridor_rp132_02_note.png：光路 1-3-2 的光线走廊里，三面质心连线满足几何约束却违反光学约束。
# 重制 2.8 旧图 img/legacy/light_corridor_rp132_02_note.png。
# 读者要看出（作者原话）：走廊看似允许一条直线通过，但这条直线在第一个面上就不对了——折射路径无法折射出这个角度
# （从外面射向入射点的光，折进晶体后最多只能偏到临界角 49.8°，到不了这条直线的 65°）；全反射路径能产生这个角度，
# 但它要求光从晶体内部来，而这是第一个面，光只能从外面来。
import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402

from _light_corridor_rp132 import CAMERA, CRYSTAL, PRESET, centroid_line, new_corridor_figure, save  # noqa: E402
from halo_notes.draw import RayPath, SegmentKind, annotate, draw_raypath  # noqa: E402
from halo_notes.draw.geometry import unit  # noqa: E402
from halo_notes.draw.raypath import N_ICE, EventKind, RayEvent, reflect, refract  # noqa: E402
from halo_notes.draw.style import DEFAULT_MAP, LineStyle  # noqa: E402

# 几何候选线本身是 sketch；折射束是真实的"折入面 1"半程光路（只到晶体内为止），面序列 [1]
PATHS = {"refract-in": [1]}
SKETCH = PRESET.replace(style_map=DEFAULT_MAP.replace(
    ray_unfolded=LineStyle("accent_cool", linewidth=1.6, linestyle="--", alpha=0.75)))


def main() -> None:
    fig, ax, chain = new_corridor_figure()
    line = centroid_line(chain)
    draw_raypath(ax, line, chain[0], camera=CAMERA, preset=SKETCH, semantic="ray_unfolded")

    geom = PRESET.geom
    top = CRYSTAL.face(1)
    n = CRYSTAL.normal(top)                                  # 面 1 外法向（朝上）
    entry, d = line.points[0], unit(line.points[1] - line.points[0])   # 直线在晶体内的方向
    theta_line = np.degrees(np.arccos(-(n @ d)))             # 直线与面 1 法向的夹角
    theta_c = np.degrees(np.arcsin(1 / N_ICE))               # 临界角
    assert N_ICE * np.sin(np.radians(theta_line)) > 1, "逆 Snell 有解——图的论点就不成立了"
    t = unit(d - (n @ d) * n)                                # 入射面内、沿直线倾斜方向的切向

    # (a) 折射路径：从外面以一组入射角射向入射点的光，折进晶体后的方向都压在临界角以内，
    # 扇面到不了直线的方向。每条都是真实追迹的半程光路（REFRACT_IN 事件，Snell 成立）；
    # 等长的入射段让五个锥体排成一条弧（旧图观感），不画端点圆点
    fan_preset = PRESET.replace(geom=geom.replace(end_markers=False))
    tail, stub = 1.2, 0.7
    for theta_i in (20.0, 40.0, 60.0, 80.0, 89.0):
        th = np.radians(theta_i)
        d_in = -np.cos(th) * n + np.sin(th) * t
        d_t = refract(d_in, n, 1.0, N_ICE)
        ray = RayPath([entry - d_in * tail, entry, entry + d_t * stub],
                      (SegmentKind.INCIDENT, SegmentKind.INTERNAL),
                      (RayEvent(1, 1, EventKind.REFRACT_IN),))
        draw_raypath(ax, ray, camera=CAMERA, preset=fan_preset, semantic="ray_folded")
    top = entry - (-np.cos(np.radians(20)) * n + np.sin(np.radians(20)) * t) * tail
    annotate(ax, f"折射路径：折射角最大 {theta_c:.1f}°，\n折不到这条直线的 {theta_line:.0f}°",
             top, (0.45, 0.25), camera=CAMERA, preset=PRESET, ha="left", va="center", arrow=True)

    # (b) 全反射路径：要在面 1 内反射后得到方向 d，入射光得是 d 关于面 1 的镜像——它从晶体内部
    # 射向面 1；而面 1 是第一个面，光只能从外面来，矛盾。示意线（sketch）：只画晶体内部那一段
    # （起点取在它穿出侧面之前），线型沿用旧图（实线）
    d_pre = reflect(d, -n)
    assert n @ d_pre > 0                                     # 确实从晶体内部朝面 1 走
    _, _, t_side, _ = CRYSTAL.intersect_ray(entry - n * 1e-6, -d_pre)   # 反向走多远穿出晶体
    start = entry - d_pre * (0.85 * t_side)
    assert CRYSTAL.contains(start, eps=1e-9)
    tir = RayPath([start, entry], (SegmentKind.INCIDENT,), sketch=True)
    draw_raypath(ax, tir, camera=CAMERA, preset=PRESET, semantic="ray_incident")
    annotate(ax, "全反射路径：能给出这个角度，\n但要求光从晶体内部射向面 1", start,
             (-0.2, -0.6), camera=CAMERA, preset=PRESET, ha="center", va="top", arrow=True)

    save(fig, "light_corridor_rp132_02_note.png")


if __name__ == "__main__":
    main()
