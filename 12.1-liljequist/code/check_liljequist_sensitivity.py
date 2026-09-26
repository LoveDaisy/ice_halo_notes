# 核验 12.1 番外提纲的数字（确定性，无网络，不跑仿真、不调 LI，约 1 s，末行 OK）：只读 ch8 图 7 已有数据
# （../../08-wedge-times-fold/data/cross_section_sensitivity{,_summary}.csv：片晶 h/a=0.2、太阳 0°、zenith σ=0.5°，
# face_distance [1,d,1,d,1,d]，d ∈ {1,1.2,1.4,1.8}，A60-10 / A0-02 两格各一次 Lumice 过滤渲染，条带 ±1.5°、0.5° 桶），
# 把提纲要用的几项整理成数字：142° 锐边不动；A0-02 那一格内侧的陡升仍在 153° 附近、变的是外侧（从下降的尾巴变成一路到反日点的平台）。
# 再用本仓闭式（halo_notes.math.wedge）核 LI 转录常量 141.83929991° = 120° + D_min(60°) 的算术；其余 LI 数字只转录、不核（见 [5]）。
# 口径提醒：ch8 的 A0-02 列是整个格子（Lumice 过滤器 OR 全部代表光路），不是单条 3-5-6-7-3；与 LI 单光路测量不可逐数比对。
import csv
from pathlib import Path

import numpy as np

from halo_notes.math.wedge import min_deviation_deg

CH8_DATA = Path(__file__).resolve().parents[2] / "08-wedge-times-fold" / "data"
DS = (1.0, 1.2, 1.4, 1.8)
N = 1.31                                   # LI canonical 折射率，与下面 LI 转录值同一口径

# 出处：LI docs/phase2.md 附录「Chapter-10 verdicts rerun」（2026-09-25，task ch10-liljequist-unblock-and-docs），逐字转录
LI_A60_10_SADDLE_DEG = 141.83929991        # A60-10 两成员 DPField 临界值，h/a = 0.2/1/2 极差 2.8e-14°
LI_LILJEQUIST_PEAK_DEG = 153.069685        # 3-5-6-7-3：面 5/6/7 内部 TIR 起始线上 D_P 的最大值（不是 D_P 临界值）
LI_LILJEQUIST_HALF_MAX = {0.2: (152.55, 158.80), 1.0: (149.80, 157.30), 2.0: (147.65, 157.05)}   # h/a → 半高区间（°）
# 出处：LI scratchpad/explore-ch12-anchor-probes/SUMMARY.md 能力矩阵「有限走廊/权重」行（探针量级，不是 LI 正式测量）
LI_ENTRY_MEASURE = {1.0: 0.0149, 1.2: 0.0060}   # geometry.entry_measure，d → 值


def read_summary():
    with (CH8_DATA / "cross_section_sensitivity_summary.csv").open() as f:
        return {(float(r["d"]), r["class"]): {k: float(v) for k, v in r.items() if k not in ("d", "class")} for r in csv.DictReader(f)}


def read_profiles():
    with (CH8_DATA / "cross_section_sensitivity.csv").open() as f:
        rows = list(csv.DictReader(f))
    az = np.array([float(r["az_deg"]) for r in rows])
    return az, {(d, cid): np.array([float(r[f"{cid}_d{d:g}"]) for r in rows]) for d in DS for cid in ("A60-10", "A0-02")}


def check_edge(s):
    """[1] A60-10：142° 锐边（内侧半高点）跨四档 d 的极差、条带能量单调下降。"""
    print("[1] A60-10（60° 楔 + 120° 折叠）：锐边位置与能量")
    edge = [s[(d, "A60-10")]["edge_az"] for d in DS]
    energy = [s[(d, "A60-10")]["energy"] for d in DS]
    for d, e, en in zip(DS, edge, energy):
        print(f"  d = {d:g}: 锐边 {e:.2f}°，条带能量 {en:.2f}")
    spread = max(edge) - min(edge)
    print(f"  ⇒ 锐边极差 {spread:.2f}°（0.5° 桶），能量 d=1→1.8 降到 {energy[-1] / energy[0]:.3f} 倍")
    assert spread < 1.5
    assert all(a > b for a, b in zip(energy, energy[1:]))
    return spread


def check_peak_summary(s):
    """[2] A0-02：半高全宽、条带能量随 d 的走势（ch8 表里的数，整理成倍数）。"""
    print("[2] A0-02（幻日环那一格，含 3-5-6-7-3）：半高全宽与能量")
    fwhm = [s[(d, "A0-02")]["fwhm_deg"] for d in DS]
    energy = [s[(d, "A0-02")]["energy"] for d in DS]
    peak = [s[(d, "A0-02")]["peak_az"] for d in DS]
    for d, w, en, p in zip(DS, fwhm, energy, peak):
        print(f"  d = {d:g}: 半高全宽 {w:.2f}°，条带能量 {en:.2f}，剖面最大值所在桶 {p:.2f}°")
    ratio = fwhm[1] / fwhm[0]
    print(f"  ⇒ 半高全宽 d=1→1.2 展宽 {ratio:.2f} 倍，之后在 {min(fwhm[1:]):.1f}–{max(fwhm[1:]):.1f}° 之间波动（不是单调走宽）；"
          f"能量先升后降（最大在 d = {DS[int(np.argmax(energy))]:g}，是 d=1 的 {max(energy) / energy[0]:.2f} 倍）")
    print("  注：d = 1.2 / 1.4 的「最大值所在桶」跳到 178° 附近，是平台上的涨落，不是峰移走了——见 [3]")
    assert ratio > 3.5 and min(fwhm[1:]) > 20
    k = int(np.argmax(energy))
    assert 0 < k < len(DS) - 1                      # 先升后降，不是单调衰减
    return ratio


def check_profile_shape(az, prof):
    """[3] A0-02 剖面形状：内侧陡升的位置（145–160° 内相邻桶差最大处）与外侧平台比（170–180° 均值 / 陡升顶 153–154.5° 均值）。"""
    print("[3] A0-02 剖面形状：内侧陡升在哪、外侧是尾巴还是平台")
    rise, plateau = [], []
    for d in DS:
        y = prof[(d, "A0-02")]
        m = (az >= 145) & (az <= 160)
        x, v = az[m], y[m]
        i = int(np.argmax(np.diff(v)))
        rise.append(0.5 * (x[i] + x[i + 1]))
        top = y[(az >= 153) & (az <= 154.5)].mean()
        plateau.append(y[(az >= 170) & (az <= 180)].mean() / top)
        print(f"  d = {d:g}: 最陡上升在 {rise[-1]:.2f}°（{x[i]:.2f}→{x[i + 1]:.2f}°），外侧平台比 {plateau[-1]:.3f}")
    where = f"{rise[0]:.2f}°" if max(rise) == min(rise) else f"{min(rise):.2f}–{max(rise):.2f}°"
    print(f"  ⇒ 陡升位置四档 d 都在 {where}（LI 3-5-6-7-3 拐点 {LI_LILJEQUIST_PEAK_DEG}°，口径不同，只并列）；"
          f"d = 1 外侧是下降的尾巴（平台比 {plateau[0]:.2f}），d ≥ 1.2 变成平台（≥ {min(plateau[1:]):.2f}）")
    assert all(152 <= r <= 154 for r in rise)
    assert plateau[0] < 0.1 and min(plateau[1:]) > 0.9
    return rise, plateau


def check_transcribed(s):
    """[4] LI 转录常量的算术：A60-10 鞍点 = 120° + D_min(60°, n=1.31)（本仓闭式）；entry_measure 比值与 ch8 整格能量比的方向；
    Liljequist 半高区间宽度。"""
    print("[4] LI 转录常量的算术自洽（不是本仓测量）")
    closed = 120.0 + min_deviation_deg(60.0, N)
    print(f"  120° + D_min(60°, n={N}) = {closed:.8f}°，LI 鞍点 {LI_A60_10_SADDLE_DEG}°，差 {closed - LI_A60_10_SADDLE_DEG:+.1e}°")
    assert abs(closed - LI_A60_10_SADDLE_DEG) < 1e-7
    r = LI_ENTRY_MEASURE[1.0] / LI_ENTRY_MEASURE[1.2]
    print(f"  entry_measure d=1 / d=1.2 = {LI_ENTRY_MEASURE[1.0]} / {LI_ENTRY_MEASURE[1.2]} = {r:.2f}（窗口收窄约 {r:.1f} 倍；探针量级）")
    e = s[(1.2, "A0-02")]["energy"] / s[(1.0, "A0-02")]["energy"]
    print(f"  方向对照：d=1→1.2，3-5-6-7-3 入射测度 ×{1 / r:.2f}，ch8 A0-02 整格条带能量 ×{e:.2f}——方向相反，"
          "提示 d ≥ 1.2 的平台多半不是 3-5-6-7-3 这一条撑起来的（同格别的成员：同一 Φ、同一 D_P 场、不同窗口）；"
          "但 entry_measure 是 LI 探针对全体可行 u 的量、ch8 是片晶太阳 0°，口径不同，只作方向提示，分解见 [5]")
    assert r > 1 and e > 1
    for ha, (lo, hi) in LI_LILJEQUIST_HALF_MAX.items():
        print(f"  LI 3-5-6-7-3 半高区间 h/a = {ha:g}: {lo}–{hi}°，宽 {hi - lo:.2f}°，峰 {LI_LILJEQUIST_PEAK_DEG}° 在区间内")
        assert lo < LI_LILJEQUIST_PEAK_DEG < hi
    widths = [hi - lo for lo, hi in LI_LILJEQUIST_HALF_MAX.values()]
    assert all(a < b for a, b in zip(widths, widths[1:]))     # h/a 越大越宽：峰位不动、宽度随窗口变
    print("  ⇒ 正六边形截面下，h/a 0.2→2 峰位不动、半高宽 6.25°→9.40°：宽度由窗口定，这是 LI 已测的「h/a 方向」；"
          "「截面方向」（d）的同类测量尚无，见 [5]")


def report_unverified():
    """[5] 提纲引用、本脚本不核的数字与尚缺的对照。"""
    print("\n[5] 仅转录、未在本仓核验；或尚缺的对照（提纲「动笔前置」）")
    for s in ("LI：153.069685° 是面 5/6/7 TIR 起始线上 D_P 的最大值（三面一致到 5e-11°），剖面在此连续带折角；"
              "折角两侧斜率 +0.0052/+0.0217/+0.0405 与 −0.00017/−0.0050/−0.0129 per rad（h/a 0.2/1/2）",
              "LI：3-5-6-7-3 与 1-3-2 同一个 D_P 场 2·arcsin|u·n3|，|∇D_P| ≡ 2（到 8.9e-16 rad），与 h/a 无关",
              "LI 探针：entry_measure d=1→1.2 从 0.0149 到 0.0060（scratchpad 探针，未进 LI 正式记录）",
              "缺：LI 单光路 3-5-6-7-3 在 d ∈ {1,1.2,1.4,1.8} 下的剖面（峰位 / 峰高 / 半高宽 / 153° 以外是否出现平台）——"
              "LI 建议的 explore ch08-liljequist-numeric-reproduction，尚未执行",
              "缺：ch8 A0-02 格子里 3-5-6-7-3 单条光路的份额（本仓只有整格剖面）；d ≠ 1 时平台由哪些成员贡献未分解"):
        print(f"  - {s}")


def main():
    s = read_summary()
    az, prof = read_profiles()
    check_edge(s)
    check_peak_summary(s)
    check_profile_shape(az, prof)
    check_transcribed(s)
    report_unverified()
    print("OK")


if __name__ == "__main__":
    main()
