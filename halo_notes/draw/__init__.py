"""halo_notes.draw — 冰晶示意图绘图库（六方柱几何 / 投影可见性 / 光路 / 面编号 / 风格四层）。"""

from .geometry import Face, HexPrism, Polyhedron, rotation, rotation_between
from .projection import Camera, face_visible, visible_faces
from .raypath import Cone, RayPath, SegmentKind, aim, face_toward, parallel_origins, trace
from .scene import annotate, draw_axes, draw_raypath, finish, new_figure, render_crystal
from .style import PRESETS, Preset
from .unfold import corridor_faces, straighten, unfold, unfolded_tail

__all__ = [
    "Camera", "Cone", "Face", "HexPrism", "PRESETS", "Polyhedron", "Preset", "RayPath",
    "SegmentKind", "aim", "annotate", "corridor_faces", "draw_axes", "draw_raypath", "face_toward", "face_visible",
    "finish", "new_figure", "parallel_origins", "render_crystal", "rotation", "rotation_between",
    "straighten", "trace", "unfold", "unfolded_tail", "visible_faces",
]
