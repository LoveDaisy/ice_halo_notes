# ch10 提纲的第二条独立链路：Lumice（release 版，MC 光线追迹）渲染 3-5 单光路的片晶幻日 / 柱晶切点，读出离太阳最近的亮像素，
# 与 check_parhelion.py 的 D_P 数值（LI phi）对照。需要 Lumice 二进制（首次运行从 GitHub release 拉取，之后用 .lumice/ 缓存）；
# 与确定性主脚本分开，免得网络 / 二进制问题混进主核验的失败模式。末行 OK。
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_parhelion import dp, golden_min, unit_from  # noqa: E402

from halo_notes.sim import config as C  # noqa: E402
from halo_notes.sim.fetch import LUMICE_VERSION  # noqa: E402
from halo_notes.sim.projection import rectangular_pixel_directions  # noqa: E402
from halo_notes.sim.raypath_probe import az_el, probe_config  # noqa: E402
from halo_notes.sim.run import render  # noqa: E402

RAYS = 2_000_000
RES = (1440, 720)             # rectangular 全天图：0.25°/px（2880×1440 时 projection 的 4M×3 matmul 在本机 numpy 段错误）
PLATE_H = (0, 20, 40, 60)     # 片晶：太阳高度
COLUMN_H = (20,)              # 柱晶：太阳高度
PRISM_HEIGHT = 3.0            # Lumice height = h/a（Lumice 的 a 是对角线直径）；取高棱柱，免得 60° 高度时 3-5 走廊被底面截断
# Lumice 的冰折射率按 Sellmeier 平均系数随波长变（Ice Halo 仓 src/core/optics.cpp IceRefractiveIndex，float 运算）：
# 550 nm 时 1.311013，580 nm 时 1.3100000（差 < 1e-6）——取 580 nm 让两条链路用同一个 n = 1.31（LI N_ICE）。
# 日面取 0.02°：幻日内缘 = 日面上离得最近的那点，高太阳时 dD/dh ≈ 4（h=60°），0.2° 日面会把内缘往里拉 ≈ 0.4°。
WAVELENGTH = 580.0
SUN_DIAMETER = 0.02
THIN_RATIO = 0.3              # [L3] 薄片晶：本仓 HexPrism h/a（经 hex_prism_height_ratio 换成 Lumice height）
THIN_SUN_H = 40.0
TOL_DEG = 0.25                # 半个像素对角线 0.18° + 日面半径 × dD/dh ≲ 0.05°


def inner_edge(image, render_unit, sun):
    """离太阳最近的亮像素（亮度 > 0）的角距离与方向：片晶是幻日内缘、柱晶是切点。"""
    lum = np.asarray(Image.open(image).convert("L"), float)
    dirs, _ = rectangular_pixel_directions(render_unit)
    D = np.degrees(np.arccos(np.clip(dirs @ sun, -1, 1)))
    lit = lum > 0
    k = np.argmin(np.where(lit, D, np.inf))
    return float(D.flat[k]), dirs.reshape(-1, 3)[k], int(lit.sum())


def d_min_on_circle(h):
    f = lambda t: dp(unit_from(h, t))[0][0]
    th = np.arange(0, 360, 0.01)
    D = dp(unit_from(h, th))[0]
    i = int(np.nanargmin(D))
    return f(golden_min(f, th[i] - 0.01, th[i] + 0.01))


def main():
    print(f"Lumice {LUMICE_VERSION}，{RAYS} 条光线，{RES[0]}×{RES[1]} rectangular，单波长 {WAVELENGTH:.0f} nm（n = 1.31），日面 {SUN_DIAMETER}°")
    with tempfile.TemporaryDirectory() as tmp:
        print("\n[L1] 片晶（c 轴竖直，绕 c 轴均匀）：离太阳最近的亮像素 = 幻日内缘")
        for h in PLATE_H:
            cfg = probe_config(C.prism_crystal(1, PRISM_HEIGHT, axis={"zenith": 0}), [3, 5],
                               sun_altitude=h, rays=RAYS, resolution=RES, sun_diameter=SUN_DIAMETER,
                               wavelength=WAVELENGTH)
            res = render(cfg, Path(tmp) / f"plate_{h}")
            sun = unit_from(h, 0.0)
            d_lum, v, n_lit = inner_edge(res.images[0], cfg["render"][0], sun)
            d_li = d_min_on_circle(h)
            a, e = az_el(v)
            print(f"  h={h:4.1f}°  Lumice {d_lum:8.4f}°（方位 {a:+8.3f}° 仰角 {e:7.3f}°，{n_lit} 亮像素）  LI {d_li:8.4f}°  "
                  f"差 {d_lum - d_li:+.3f}°")
            assert abs(d_lum - d_li) < TOL_DEG
            assert abs(e - h) < TOL_DEG                     # 幻日与太阳同高度
        print("\n[L2] 柱晶（c 轴水平，方位 / 自转均匀）：离太阳最近的亮像素 = 切点")
        for h in COLUMN_H:
            cfg = probe_config(C.prism_crystal(1, PRISM_HEIGHT, axis={"zenith": 90}), [3, 5],
                               sun_altitude=h, rays=RAYS, resolution=RES, sun_diameter=SUN_DIAMETER,
                               wavelength=WAVELENGTH)
            res = render(cfg, Path(tmp) / f"column_{h}")
            sun = unit_from(h, 0.0)
            d_lum, v, n_lit = inner_edge(res.images[0], cfg["render"][0], sun)
            d_li = dp(unit_from(0.0, 319.08035))[0][0]      # 主平面内最小偏向（check_parhelion [1] h=0 行）
            a, e = az_el(v)
            print(f"  h={h:4.1f}°  Lumice {d_lum:8.4f}°（方位 {a:+8.3f}° 仰角 {e:7.3f}°）  LI D_min {d_li:8.4f}°  差 {d_lum - d_li:+.3f}°")
            assert abs(d_lum - d_li) < TOL_DEG
            assert abs(a) < TOL_DEG or abs(abs(a) - 180) < TOL_DEG   # 切点在太阳所在竖直面上
        print(f"\n[L3] 薄片晶（本仓 h/a = {THIN_RATIO}）太阳高度 {THIN_SUN_H}°：3-5 直穿被底面截断，"
              "两次底面反射（M 仍 = I）落在同一个幻日")
        crystal = C.prism_crystal(1, C.hex_prism_height_ratio(THIN_RATIO), axis={"zenith": 0})
        sun = unit_from(THIN_SUN_H, 0.0)
        d_li = d_min_on_circle(THIN_SUN_H)
        for faces in ([3, 5], [3, 2, 1, 5]):          # 太阳在上、光向下走：先碰底面 2 再碰顶面 1
            cfg = probe_config(crystal, faces, sun_altitude=THIN_SUN_H, rays=RAYS, resolution=RES,
                               sun_diameter=SUN_DIAMETER, wavelength=WAVELENGTH)
            res = render(cfg, Path(tmp) / f"thin_{'-'.join(map(str, faces))}")
            d_lum, v, n_lit = inner_edge(res.images[0], cfg["render"][0], sun)
            if n_lit == 0:
                print(f"  {'-'.join(map(str, faces)):8s}  0 亮像素（走廊不通）")
                assert faces == [3, 5]
                continue
            a, e = az_el(v)
            print(f"  {'-'.join(map(str, faces)):8s}  Lumice {d_lum:8.4f}°（仰角 {e:7.3f}°，{n_lit} 亮像素）  "
                  f"LI 3-5 D_min {d_li:8.4f}°  差 {d_lum - d_li:+.3f}°")
            assert faces != [3, 5] and abs(d_lum - d_li) < TOL_DEG and abs(e - THIN_SUN_H) < TOL_DEG
    print("OK")


if __name__ == "__main__":
    main()
