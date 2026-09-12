# 产出 ../img/compare_two_methods.jpg（3381×1620）：蒙特卡洛 vs. 直接积分。
# 左：柱晶全天晕的**天球外视图**（Lumice `globe` 镜头，负片：白底、晕呈深色，灰经纬网格），叠加标注——
#     "幻日环 / 上切弧 / 下切弧" 引线、"太阳" 橙点、"地平线" 红线、下切弧处红框；
# 右：四条竖条带（251×801）"1000万光线 / 1亿光线 / 10亿光线 / 直接积分"——前三条 Lumice 以 linear 窄视场对准下切弧局部，
#     ray_num 1e7 / 1e8 / 1e9，同一 ev_mode="absolute" + 同一 intensity_factor（跨光线数亮度可比，有单测断言）；
#     第四条直接引用现成的 ../data/column1.0_direct.jpg（直接积分另行立项，本任务不重算）。
# 重制 6.5 旧图 img/legacy/compare_two_methods.jpg。正文第 83 行"10 亿光线运行了 72 秒"是旧渲染器；本机墙钟见各 provenance.json。
#
# 参数来源（旧图无源 config；旧数据名 column1.0_rp35_180+15 / all_sky_column1.0_sph 提供线索）：
# - 晶体：柱晶 h/a = 1.0（"column1.0"），zenith σ=0.5°；全天图不加过滤器，条带只留 3-5 光路（"rp35"，symmetry PBD）
# - 太阳高度 15°（"+15"，与旧图地平线位置一致）；D65 光谱（旧图灰度负片，色彩无关）；`sun(diameter=0)` 严格点光源
#   （旧图条带/globe 均有清晰切边，旧 template.json 也是 diameter 0.0；`config.py::sun()` 默认 0.5 会把切边晕开，2026-09-12 改回 0）
# - 天球外视图：观察者略高于地平线、偏太阳一侧 35°（猜：旧图太阳在球心右侧约 0.5R、地平线椭圆开口向下），见 GLOBE_VIEW
# - 条带窗口：linear 短边视场 6°，视线指向 (az 0, el −15)，即下切弧顶点（太阳下 22° = −7°）下方 8°（猜，对齐旧直接积分条带）
# - 标注锚点不手填：同一 config 里加一个"标记"render（同视角，黑底，只画纯色经纬线：0° 经线 + 15° / 37° / −7° 纬线），
#   太阳 = 经线 0 ∩ 纬线 15、上切弧顶点 = 经线 0 ∩ 纬线 15+22、下切弧顶点 = 经线 0 ∩ 纬线 15−22、幻日环左端 = 纬线 15 最左像素——
#   锚点来自 Lumice 自己的投影而非人眼估计（angular_dist 圆在 globe 镜头下不画，v4.5.1 实测，所以用经纬线交点）
# - 负片：网格颜色按"反相后的目标色"写进 config（negative()），渲染后整图 invert；地平线用 0° 纬线（horizon=true 是固定暗红）
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

NAME = "compare_two_methods"
CHAPTER = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 3381, 1620
SUN_ALTITUDE = 15.0
COLUMN_HEIGHT = 1.0
GLOBE_PX = 1500                     # 球体直径 ≈ 0.96 × 1500 = 1440 px，与旧图 ≈ 1436 px 一致
GLOBE_BOX = (264, 61, GLOBE_PX, GLOBE_PX)
# globe 的 view 语义实测与 doc 直觉相反：{az 215, el −22} 才得到"观察者在太阳一侧、略高于地平线俯视、太阳在球心右侧"的
# 旧图构图（{az 35, el 22} 看到的是背面且经线 0 被遮）——2026-09-12 标记 render 逐一验证
GLOBE_VIEW = {"azimuth": 215, "elevation": -22}
BAND_W, BAND_H = 251, 801           # = column1.0_direct.jpg 的尺寸
BAND_X0, BAND_PITCH, BAND_Y = 1952, 350, 405
BAND_RAY_NUMS = {"1e7": 10_000_000, "1e8": 100_000_000, "1e9": 1_000_000_000}
BAND_TITLES = {"1e7": "1000万光线", "1e8": "1亿光线", "1e9": "10亿光线", "direct": "直接积分"}
BAND_EV_MODE, BAND_INTENSITY = "absolute", 16.0   # 16 = 让 1e9 条带峰值与 column1.0_direct.jpg 的峰值（≈240/255）齐平（1.0 时实测峰值 ≈65）
GLOBE_RAY_NUM = 200_000_000
GLOBE_INTENSITY = 0.5   # relative 曝光下压半档：反相后底色接近纯白（1.0 时全球泛灰），弧仍清晰
ORANGE, RED, INK = "#F26A1B", "#D42020", "#1A1A1A"
MARK_MERIDIAN, MARK_SUN_EL, MARK_UTA_EL, MARK_LTA_EL = (0, 0, 1), (0, 1, 0), (1, 0, 0), (1, 0, 1)  # 标记 render 的纯色


def negative(rgb):
    """整图反相后想要的颜色 → 写进 config 的颜色。"""
    return [round(1 - c, 3) for c in rgb]


def column():
    return C.prism_crystal(1, COLUMN_HEIGHT, axis=C.column_axis(0.5))


def build_globe() -> dict:
    grey = negative([0.55, 0.55, 0.55])
    grid = C.grid(
        elevation=[C.grid_line(v, opacity=0.9, color=grey) for v in range(-75, 90, 15) if v != 0]
                  + [C.grid_line(0, opacity=1.0, color=negative([0.83, 0.13, 0.13]))],   # 地平线：反相后红
        longitude=[C.grid_line(v, opacity=0.9, color=grey) for v in range(-165, 181, 15)],
    )
    picture = C.render_unit(1, C.lens("globe", fov=30), [GLOBE_PX, GLOBE_PX], view=GLOBE_VIEW, visible="full",
                            background=[0, 0, 0], ray_color=[1, 1, 1], grid=grid,
                            intensity_factor=GLOBE_INTENSITY)
    # 光线涂黑（ray_color 0）只留网格；intensity_factor 不能给 0（实测整图全黑连网格都没了）
    markers = C.render_unit(2, C.lens("globe", fov=30), [GLOBE_PX, GLOBE_PX], view=GLOBE_VIEW, visible="full",
                            background=[0, 0, 0], ray_color=[0, 0, 0],
                            grid=C.grid(longitude=[C.grid_line(0, color=MARK_MERIDIAN)],
                                        elevation=[C.grid_line(SUN_ALTITUDE, color=MARK_SUN_EL),
                                                   C.grid_line(SUN_ALTITUDE + 22, color=MARK_UTA_EL),
                                                   C.grid_line(SUN_ALTITUDE - 22, color=MARK_LTA_EL)]))
    sc = C.scene(C.sun(SUN_ALTITUDE, diameter=0), GLOBE_RAY_NUM, [C.entry(1)], max_hits=7)
    return C.build_config([column()], [], sc, [picture, markers])


def build_band(ray_num: int) -> dict:
    flt = C.raypath_filter(1, [3, 5], "PBD")
    sc = C.scene(C.sun(SUN_ALTITUDE, diameter=0), ray_num, [C.entry(1, filter=1)], max_hits=3)
    band = C.render_unit(1, C.lens("linear", fov=6), [BAND_W, BAND_H], view={"azimuth": 0, "elevation": -15},
                         visible="full", background=[0, 0, 0], ray_color=[1, 1, 1],
                         ev_mode=BAND_EV_MODE, intensity_factor=BAND_INTENSITY)
    return C.build_config([column()], [flt], sc, [band])


# ---------- 标注锚点：从标记 render 的像素颜色反推 ----------


def _pixels(img: np.ndarray, rgb) -> np.ndarray:
    """颜色匹配到的像素坐标 (N, 2)=(x, y)。"""
    target = np.array(rgb) * 255
    ys, xs = np.nonzero(np.all(np.abs(img.astype(int) - target) < 60, axis=-1))
    if len(xs) == 0:
        raise RuntimeError(f"标记 render 里找不到颜色 {rgb} 的网格线")
    return np.stack([xs, ys], axis=1).astype(float)


def _crossing(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """两条像素线的交点：取最近像素对的中点（线宽 1–2 px，误差 ≤ 1 px）。"""
    d = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    i, j = np.unravel_index(d.argmin(), d.shape)
    if d[i, j] > 9:
        raise RuntimeError(f"两条网格线不相交（最近距离 {np.sqrt(d[i, j]):.1f} px）")
    m = (a[i] + b[j]) / 2
    return float(m[0]), float(m[1])


def anchors(marker_image: Path) -> dict[str, tuple[float, float]]:
    """返回球面图（本地像素）里的锚点：sun / uta（上切弧顶点）/ lta（下切弧顶点）/ pc_left（幻日环最左端）。"""
    img = np.asarray(X.Image.open(marker_image).convert("RGB"))
    meridian = _pixels(img, MARK_MERIDIAN)
    sun_el, uta_el, lta_el = (_pixels(img, c) for c in (MARK_SUN_EL, MARK_UTA_EL, MARK_LTA_EL))
    k = sun_el[:, 0].argmin()
    return {
        "sun": _crossing(meridian, sun_el),
        "uta": _crossing(meridian, uta_el),
        "lta": _crossing(meridian, lta_el),
        "pc_left": (float(sun_el[k, 0]), float(sun_el[k, 1])),
    }


def to_canvas(p, box=GLOBE_BOX):
    return (box[0] + p[0], box[1] + p[1])


def compose_figure(globe_image: Path, marker_image: Path, bands: dict[str, Path], out: Path) -> Path:
    a = {k: to_canvas(v) for k, v in anchors(marker_image).items()}
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "white")
    X.paste_image(ax, X.invert(globe_image), GLOBE_BOX)

    X.add_leader(ax, a["pc_left"], (a["pc_left"][0] - 80, a["pc_left"][1] - 280), "幻日环",
                 text_end=(a["pc_left"][0] - 80, a["pc_left"][1] - 280), color=INK, size_px=54, ha="right")
    X.add_leader(ax, a["uta"], (a["uta"][0] + 380, a["uta"][1] - 290), "上切弧",
                 text_end=(a["uta"][0] + 600, a["uta"][1] - 290), color=INK, size_px=54)
    X.add_dot(ax, a["sun"], radius_px=13, color=ORANGE)
    X.add_text(ax, (a["sun"][0] - 70, a["sun"][1] - 75), "太阳", size_px=54, color=ORANGE)
    X.add_text(ax, (a["sun"][0] - 330, a["sun"][1] + 165), "地平线", size_px=54, color=RED)
    box = (a["lta"][0] - 52, a["lta"][1] - 30, 105, 220)
    X.add_box(ax, box, color=RED, width_px=4)
    X.add_leader(ax, (box[0] + box[2] * 0.4, box[1] + box[3]), (box[0] + 250, box[1] + box[3] + 150), "下切弧",
                 text_end=(box[0] + 420, box[1] + box[3] + 150), color=INK, size_px=54)

    for i, key in enumerate(("1e7", "1e8", "1e9", "direct")):
        if key not in bands:
            continue
        x = BAND_X0 + i * BAND_PITCH
        X.paste_image(ax, bands[key], (x, BAND_Y, BAND_W, BAND_H))
        X.add_text(ax, (x + BAND_W / 2, BAND_Y + BAND_H + 100), BAND_TITLES[key], size_px=50, color=INK)
    return X.save_canvas(fig, out)


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=GLOBE_RAY_NUM, description=NAME)
    scale = args.ray_num / GLOBE_RAY_NUM          # --ray-num 同比例缩放全天图与三条带（单测用）
    res = sim_figure(NAME, CHAPTER, with_ray_num(build_globe(), args.ray_num), out_root=args.out,
                     workers=args.workers, backend=args.backend)
    print(f"globe {res.wall_clock_s:.1f} s")
    bands: dict[str, Path] = {}
    for key, n in BAND_RAY_NUMS.items():
        r = sim_figure(NAME, CHAPTER, build_band(max(1000, int(n * scale))), out_root=args.out, variant=f"band{key}",
                       workers=args.workers, backend=args.backend)
        bands[key] = r.images[0]
        print(f"band {key}: {r.wall_clock_s:.1f} s")
    direct = CHAPTER / "data" / "column1.0_direct.jpg"
    if direct.exists():
        bands["direct"] = direct
    out = compose_figure(res.images[0], res.images[1], bands, img_path(NAME, CHAPTER, "jpg", args.out))
    print(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
