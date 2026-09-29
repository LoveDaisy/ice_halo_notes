# 返工 R1（R2 补三景）的数据产出（不出图）：随机取向的十景「太阳天顶 + 一景两渲」→ ../data/zenith/<scene>.zip + ../data/zenith/<scene>/（config /
# provenance / lumice.log / img_XX.json）。图 4 / 5 / 6 / 9 / 10 的天空图与剖面都从这里取，不再从已入库的 rectangular 重投影；
# 上一轮的 `data/odd_radius_*` 产物与 `data/notes.md` 是历史记录，不覆盖、不改写。
# 十景（全部 max_hits 4、D65、ZENITH_RAY_NUM 条光线（13-15-26-28 例外，见 RAY_NUM_OVERRIDE），与上一轮同一过滤器构造——`_ch9_sim` 的 family_filters / remainder_filter / single_raypath_filter）：
#   panorama / panorama_h3_t0.25 / panorama_h0.3_t0.85：三档锥晶全景（无过滤器）；
#   remainder：参考几何，9 族 ≤ 4 面全部代表 `filter_out`（族外多次反射 + 单面外反射）；
#   w52.4 / w56 / w60 / w62 / w63.8：参考几何，只留 18° / 20° / 22° / 23° / 24° 晕一族（w56 / w60 / w62 返工 R2 补渲，图 8 与图 6 同源）；
#   13-15-26-28：参考几何，只留这一条族外光路（PBD 对称像全留）。
# 渲染走 Lumice release（`_ch9_sim.ensure_lumice_version()`，拒绝 LUMICE_BIN）+ `--backend metal`（`halo_notes.sim.run.render` 核对日志里真走了
# Metal，回落 CPU 即报错）；两种投影全天总能量一致性闸（< 2%）在打包时硬断言（`_ch9_fig.pack_dual`）。
# Lumice 是无固定 seed 的 MC，重渲不逐字节复现（`--seed` 会把 GPU 路线降成单线程，不用）。
# 用法：`uv run python 09-pyramid/code/render_zenith.py [scene ...]`（缺省全部十景）。
from __future__ import annotations

import argparse
import json

import _ch9_fig as F
import _ch9_sim as S
from halo_notes.sim import run

TIER_H3, TIER_H03 = (3.0, 0.25), (0.3, 0.85)
TOP_PATH = (13, 15, 26, 28)
SCENES = {
    "panorama": lambda: (S.crystal(S.TIER), []),
    "panorama_h3_t0.25": lambda: (S.crystal(TIER_H3), []),
    "panorama_h0.3_t0.85": lambda: (S.crystal(TIER_H03), []),
    "remainder": lambda: (S.crystal(S.TIER), S.remainder_filter()),
    "w52.4": lambda: (S.crystal(S.TIER), S.family_filters(52.4)),
    "w56": lambda: (S.crystal(S.TIER), S.family_filters(56.0)),
    "w60": lambda: (S.crystal(S.TIER), S.family_filters(60.0)),
    "w62": lambda: (S.crystal(S.TIER), S.family_filters(62.0)),
    "w63.8": lambda: (S.crystal(S.TIER), S.family_filters(63.8)),
    "13-15-26-28": lambda: (S.crystal(S.TIER), S.single_raypath_filter(TOP_PATH)),
}
RAY_NUM_OVERRIDE = {"13-15-26-28": 10_000_000_000}   # 单条族外光路只分到 0.07% 的能量：10⁹ 光线时反日半球每像素只有零星几条，色散噪声满屏；GPU 上 ×10 只要几分钟
TIERS = {"panorama": S.TIER, "panorama_h3_t0.25": TIER_H3, "panorama_h0.3_t0.85": TIER_H03}


def scene_name(scene: str) -> str:
    """`DualScene` / `data/` 下的名字：``zenith/<scene>``。"""
    return f"zenith/{scene}"


def render(scene: str, ray_num: int = F.ZENITH_RAY_NUM) -> dict:
    binary = S.ensure_lumice_version()
    crystal, filters = SCENES[scene]()
    cfg = F.dual_config(crystal, filters, ray_num=ray_num)
    out = F.DATA / "zenith" / scene
    res = run.render(cfg, out, fmt="npy", backend=F.ZENITH_BACKEND, bin=binary)     # backend=metal 回落 CPU 时 render 直接抛 LumiceError
    arrays, sidecars = F.load_npy_render(res)
    prov = res.provenance
    extra = {"scene": scene, "tier": list(TIERS.get(scene, S.TIER)), "ray_num": ray_num, "max_hits": 4, "sun_alt": F.ZENITH_SUN_ALT,
             "filter_paths": sorted("-".join(map(str, p)) for p in S.filter_paths(filters)) if filters else [],
             "filter_action": filters[0].get("action", "filter_in") if filters else None,
             "backend": F.ZENITH_BACKEND, "gpu_route": prov["gpu_route"], "wall_clock_s": prov["wall_clock_s"]}
    meta = F.pack_dual(F.DATA / "zenith" / f"{scene}.zip", arrays, sidecars, extra)
    return {k: meta[k] for k in ("total_energy_float32", "gpu_route", "wall_clock_s")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="*", default=list(SCENES))
    ap.add_argument("--ray-num", type=int, default=F.ZENITH_RAY_NUM)
    args = ap.parse_args()
    for sc in args.scenes:
        print(sc, render(sc, RAY_NUM_OVERRIDE.get(sc, args.ray_num)), flush=True)


if __name__ == "__main__":
    main()
