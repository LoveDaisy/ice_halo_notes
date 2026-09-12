"""把 Lumice 渲染图与 matplotlib 标注 / ``halo_notes.draw`` 晶体 inset 合成到一张像素画布上。

画布坐标 = 目标图片的像素坐标（原点左上、y 向下），所有标注位置直接用像素给，和 psd 标注层一一对应。
中文字体只读引用 ``halo_notes.draw.style.mapping.CJK_SANS``。不改 ``halo_notes.draw`` 内部，只 import 现成能力。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from halo_notes.draw import Camera, HexPrism, RayPath, frame, render_crystal, solve_raypath  # noqa: E402
from halo_notes.draw.style import PRESETS, Preset  # noqa: E402
from halo_notes.draw.style.mapping import CJK_SANS, LineStyle  # noqa: E402

DPI = 100  # 像素画布固定 100 dpi：1 pt = 100/72 px，字号换算见 px_to_pt

Box = tuple[float, float, float, float]  # (x, y, w, h) 像素

# 2.1 右下 inset 用的深色预设：黑底白线框 + 入射 / 出射都用珊瑚红（旧图观感）；从 DEFAULT 派生，不动 draw
DARK_INSET: Preset = PRESETS["default"].replace(
    name="dark_inset",
    palette=PRESETS["default"].palette.with_colors("dark_inset", background="#000000", ink="#FFFFFF", ink_faint="#8A8A8A"),
    style_map=PRESETS["default"].style_map.replace(
        edge_visible=LineStyle("ink", linewidth=2.0),
        edge_hidden=LineStyle("ink_faint", linewidth=1.0),
        ray_incident=LineStyle("accent_warm", linewidth=2.4),
        ray_internal=LineStyle("accent_warm", linewidth=2.4, alpha=0.45),
        ray_exit=LineStyle("accent_warm", linewidth=2.4),
    ),
)


def px_to_pt(px: float) -> float:
    return px * 72.0 / DPI


# ---------- 画布 ----------


def pixel_canvas(width: int, height: int, background: str = "black"):
    """建一张 ``width×height`` 像素的画布：单个铺满的 axes，坐标即像素（y 向下）。"""
    fig = plt.figure(figsize=((width + 0.5) / DPI, (height + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(background)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_aspect("equal")
    ax.set_axis_off()
    return fig, ax


def paste_image(ax, image: Path | str | Image.Image, box: Box, *, zorder: int = 0) -> None:
    """把图片贴进像素框 ``box``（拉伸到框大小；调用方保证宽高比）。"""
    img = image if isinstance(image, Image.Image) else Image.open(image)
    x, y, w, h = box
    ax.imshow(np.asarray(img.convert("RGB")), extent=(x, x + w, y + h, y), interpolation="lanczos", zorder=zorder)


def render_canvas(fig) -> Image.Image:
    """把画布栅格化成 PIL 图（尺寸 = 建画布时的像素尺寸）。"""
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    return Image.fromarray(buf[:, :, :3].copy())


def save_canvas(fig, out_path: Path | str, *, quality: int = 95) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = render_canvas(fig)
    if out_path.suffix.lower() in (".jpg", ".jpeg"):
        img.save(out_path, quality=quality)
    else:
        img.save(out_path)
    plt.close(fig)
    return out_path


# ---------- 标注图元（像素坐标） ----------


def add_text(ax, xy: Sequence[float], text: str, *, size_px: float = 40, color: str = "white",
             ha: str = "center", va: str = "center", weight: str = "normal", family=CJK_SANS, **kw: Any):
    return ax.text(xy[0], xy[1], text, fontsize=px_to_pt(size_px), color=color, ha=ha, va=va,
                   fontweight=weight, fontfamily=list(family), zorder=20, **kw)


def add_dot(ax, xy: Sequence[float], *, radius_px: float = 8, color: str = "white", zorder: int = 15):
    ax.add_patch(Circle(xy, radius_px, facecolor=color, edgecolor="none", zorder=zorder))


def add_arrow(ax, tail: Sequence[float], head: Sequence[float], *, color: str = "#FC5D53",
              width_px: float = 4, head_px: float = 22, zorder: int = 16):
    """从 ``tail`` 指向 ``head`` 的实心箭头（像素）。"""
    ax.add_patch(FancyArrowPatch(tail, head, arrowstyle=f"-|>,head_length={px_to_pt(head_px):.1f},head_width={px_to_pt(head_px * 0.55):.1f}",
                                 color=color, linewidth=px_to_pt(width_px), mutation_scale=1, shrinkA=0, shrinkB=0, zorder=zorder))


def add_polyline(ax, points: Sequence[Sequence[float]], *, color: str = "black", width_px: float = 3, zorder: int = 14, **kw: Any):
    pts = np.asarray(points, float)
    ax.plot(pts[:, 0], pts[:, 1], color=color, linewidth=px_to_pt(width_px), solid_capstyle="round", zorder=zorder, **kw)


def add_leader(ax, target: Sequence[float], elbow: Sequence[float], text: str, *, text_end: Sequence[float] | None = None,
               color: str = "black", width_px: float = 3, size_px: float = 48, ha: str = "left"):
    """6.5 式引线：``target``（弧上一点）→ ``elbow`` 折点 →（可选）水平段末端，文字贴在末端。"""
    pts = [target, elbow] + ([text_end] if text_end is not None else [])
    add_polyline(ax, pts, color=color, width_px=width_px)
    end = pts[-1]
    add_text(ax, (end[0] + (12 if ha == "left" else -12), end[1]), text, size_px=size_px, color=color, ha=ha, va="center")


def add_box(ax, box: Box, *, color: str = "#E02020", width_px: float = 4, zorder: int = 16):
    x, y, w, h = box
    ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor=color, linewidth=px_to_pt(width_px), zorder=zorder))


def add_circle(ax, center: Sequence[float], radius_px: float, *, color: str = "white", width_px: float = 2, zorder: int = 12):
    ax.add_patch(Circle(center, radius_px, fill=False, edgecolor=color, linewidth=px_to_pt(width_px), zorder=zorder))


# ---------- 晶体 inset（复用 halo_notes.draw） ----------


def add_crystal_inset(fig, box: Box, canvas_size: tuple[int, int], *, raypath: Sequence[int], height_ratio: float = 0.5,
                      camera: Camera | None = None, preset: Preset = DARK_INSET, tail: float = 1.4, head: float = 1.4,
                      face_numbers: bool = False) -> RayPath:
    """在画布像素框 ``box`` 里画一个六方片晶 + 指定面序列的光路（Snell 真实反解，锥体箭头）。

    只 import ``halo_notes.draw`` 的 ``HexPrism`` / ``solve_raypath`` / ``render_crystal``，返回反解出的光路供单测核验面序列。
    """
    W, H = canvas_size
    x, y, w, h = box
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.set_axis_off()
    ax.patch.set_alpha(0)
    crystal = HexPrism(1.0, height_ratio)
    camera = camera or Camera(azimuth=35, elevation=22, distance=9)
    path = solve_raypath(crystal, list(raypath), tail=tail, head=head)
    render_crystal(ax, crystal, [path], camera=camera, preset=preset, face_numbers=face_numbers)
    xlim, ylim = frame(camera, [crystal.vertices, path.points], int(w), int(h), margin=0.06)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    return path


# ---------- 图像工具 ----------


def crop(image: Path | str | Image.Image, box: Box) -> Image.Image:
    img = image if isinstance(image, Image.Image) else Image.open(image)
    x, y, w, h = box
    return img.crop((int(x), int(y), int(x + w), int(y + h)))


def invert(image: Path | str | Image.Image) -> Image.Image:
    """负片（6.5 左图：白底、晕呈深色）。"""
    img = image if isinstance(image, Image.Image) else Image.open(image)
    return ImageOps.invert(img.convert("RGB"))


def compose_bands(band_images: Sequence[Path | str | Image.Image], titles: Sequence[str], *, gap: int = 60,
                  title_height: int = 90, title_size_px: float = 44, title_color: str = "white",
                  background: str = "black") -> Image.Image:
    """把多张竖条带横向拼接并在下方加标题；输出宽 = Σ带宽 + gap×(n−1)，高 = max 带高 + title_height。"""
    if len(band_images) != len(titles):
        raise ValueError("band_images 与 titles 数量不一致")
    imgs = [im if isinstance(im, Image.Image) else Image.open(im) for im in band_images]
    widths = [im.width for im in imgs]
    W = sum(widths) + gap * (len(imgs) - 1)
    H = max(im.height for im in imgs) + title_height
    fig, ax = pixel_canvas(W, H, background)
    x = 0
    for im, title in zip(imgs, titles):
        paste_image(ax, im, (x, 0, im.width, im.height))
        add_text(ax, (x + im.width / 2, im.height + title_height / 2), title, size_px=title_size_px, color=title_color)
        x += im.width + gap
    out = render_canvas(fig)
    plt.close(fig)
    return out
