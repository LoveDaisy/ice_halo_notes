"""halo_notes.draw — 冰晶示意图绘图库（六方柱几何 / 投影可见性 / 光路 / 面编号 / 风格四层）。"""

from .geometry import Face, HexPrism, Polyhedron, rotation, rotation_between, rotation_from_frames
from .projection import Camera, face_visible, visible_faces
from .raypath import (Cone, RayPath, SegmentKind, aim, face_sequence, face_toward, parallel_origins,
                      solve_raypath, trace, verify_path)
from .scene import (annotate, draw_axes, draw_raypath, finish, frame, new_figure, render_corridor,
                    render_crystal)
from .style import PRESETS, Preset
from .unfold import Corridor, corridor_faces, straighten, unfold, unfolded_tail

__all__ = [
    "Camera", "Cone", "Corridor", "Face", "HexPrism", "PRESETS", "Polyhedron", "Preset", "RayPath",
    "SegmentKind", "aim", "annotate", "corridor_faces", "draw_axes", "draw_raypath", "face_sequence",
    "face_toward", "face_visible",
    "finish", "frame", "new_figure", "parallel_origins", "render_corridor", "render_crystal", "rotation", "rotation_between", "rotation_from_frames",
    "solve_raypath", "straighten", "trace", "unfold", "unfolded_tail", "verify_path", "visible_faces",
]
