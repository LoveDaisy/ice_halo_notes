# 产出 ../img/pose_to_sky_br.gif（#3，$M=br$）与 ../img/pose_to_sky_s.gif（#2，$M=s$）：与 7.5 静态图同一行布局（三栏），
# 中栏只剩一枚会动的柱晶——ψ=ψ0 固定，θ 在所选光路的扫描区间 [θa, θb] 内匀速来回一轮（每帧 `search_raypath` 固定入射方向重新
# 解光路），左栏样本点同步沿竖线 ψ=ψ0 移动并留下轨迹，右栏（Lumice 底图上）天空点：br 版纹丝不动（弧上一个亮点），
# s 版沿一条曲线画出轨迹。读者要看出：晶体在动、光路在变，出射光点不动（br）；对比 s：θ 一动光点就动。
# R1-3：原先的第二段 ψ 已删（可行区间只允许 ψ 差 5°，「换 ψ 才动」演不出来反而冗余）。
# 帧：来回 2×N_HALF = 40 帧、25 fps（40 ms/帧）；θ 区间的可行性由 1° 步长扫描得到，见 _pose_to_sky.py 顶注（ROWS[·].sweep）。
# 调色板（R2-4）：右栏 Lumice 底图的色彩噪声会吃光 gif 的 256 色，出射箭头的蓝被量化成灰——`animate(fixed_colors=FIXED_COLORS)`
# 把入射 / 内部 / 出射光的语义色、样本色原样钉进调色板（`halo_notes.draw.animation.PaletteWriter`）。
# 静态抽帧只作核验（test_figures 经 export_frames_png），不入正文。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from _pose_to_sky import (IMG, PANEL_ENTRY, PRESET, PSI0, ROWS, add_row_axes, build_attitude_axes,  # noqa: F401
                          build_sky_axes, draw_connector, draw_crystal_panel, draw_samples_on_attitude,
                          draw_sky_samples, exit_end_xy, finish, sample_line, sky_limits, sky_point, sky_xy, solve)
from halo_notes.draw import animate, export_frames_png
from halo_notes.draw.geometry import unit

OUTS = {3: IMG / "pose_to_sky_br.gif", 2: IMG / "pose_to_sky_s.gif"}
WIDTH, HEIGHT, DPI = 1500, 575, 100    # 静态图的一行缩半（gif 体积）
N_HALF, FPS = 20, 25                   # θa→θb 20 帧、θb→θa 20 帧

PATHS = {f"#{n} {'-'.join(map(str, s.faces))}": list(s.faces) for n, s in ROWS.items()}
# 必须原样进 gif 调色板的颜色：光路三段语义色 + 样本色（不钉白 / 黑：底图里太阳眩光附近的近白像素会被整块吸成纯白）
FIXED_COLORS = [PRESET.line_kwargs(sem)["color"] for sem in ("ray_incident", "ray_internal", "ray_exit")] + \
               [PRESET.line_kwargs(sample_line(0))["color"]]


def schedule(number: int) -> list[tuple[float, float]]:
    """帧表 [(ψ0, θ), …]：θ 在 [θa, θb] 内匀速来回（首尾各到端点一次）。"""
    a, b = ROWS[number].sweep
    forth = np.linspace(a, b, N_HALF)
    return [(PSI0, float(t)) for t in forth] + [(PSI0, float(t)) for t in forth[::-1][1:-1]] + [(PSI0, float(a))]


def compute_frames(number: int) -> list[dict]:
    """逐帧解光路（帧表里每个姿态都必须可行——区间来自 1° 扫描）。"""
    out = []
    for psi, theta in schedule(number):
        R, crystal, path = solve(psi, theta, ROWS[number].faces)
        p = sky_point(number, R)
        assert np.linalg.norm(-unit(path.points[-1] - path.points[-2]) - p) < 1e-9
        out.append({"psi": psi, "theta": theta, "R": R, "crystal": crystal, "path": path, "sky": p})
    return out


FRAMES = {n: compute_frames(n) for n in ROWS}
N_FRAMES = {n: len(f) for n, f in FRAMES.items()}


def make_build_axes(number: int):
    def build_axes(n_rows: int):
        fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT * n_rows + 0.5) / DPI), dpi=DPI)
        fig.patch.set_facecolor(PRESET.palette["background"])
        rows = []
        h = 1.0 / n_rows
        for r in range(n_rows):
            ax_left, mids, ax_sky = add_row_axes(fig, 1.0 - (r + 1) * h, h, 1)
            build_attitude_axes(ax_left)
            build_sky_axes(ax_sky, number)
            finish(ax_sky, *sky_limits(number))
            ax_sky.set_title(ROWS[number].title, **PRESET.text_kwargs("panel_title"), math_fontfamily="cm", loc="right")
            rows.append((ax_left, mids[0], ax_sky))
        return fig, rows
    return build_axes


def make_render_frame(number: int):
    frames = FRAMES[number]

    def render_frame(fig, row, i: int) -> None:
        ax_left, ax_mid, ax_sky = row
        f = frames[i]
        seg = frames[:i + 1]                                                # 到目前为止的轨迹
        draw_samples_on_attitude(ax_left, [(f["psi"], f["theta"])], trail=np.array([(g["psi"], g["theta"]) for g in seg]))
        draw_crystal_panel(ax_mid, number, 0, f["crystal"], f["path"])
        draw_sky_samples(ax_sky, number, [f["sky"]], stacked=False, trail=np.array([g["sky"] for g in seg]))
        draw_connector(ax_left, (f["psi"], f["theta"]), ax_mid, PANEL_ENTRY, preset=PRESET, semantic=sample_line(0),
                       coords_b="axes fraction")
        draw_connector(ax_mid, exit_end_xy(number, f["path"]), ax_sky, sky_xy(number, f["sky"]), preset=PRESET,
                       semantic=sample_line(0))
    return render_frame


def main() -> None:
    for number, out in OUTS.items():
        animate(make_render_frame(number), N_FRAMES[number], out, fps=FPS, build_axes=make_build_axes(number), dpi=DPI,
                fixed_colors=FIXED_COLORS)
        print(f"saved {out} ({N_FRAMES[number]} frames)")


if __name__ == "__main__":
    main()
