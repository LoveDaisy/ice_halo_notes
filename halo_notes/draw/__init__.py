"""halo_notes.draw — 冰晶示意图绘图库（六方柱几何 / 投影可见性 / 光路 / 面编号 / 风格四层 /
2D 截面与对称操作）。"""

from .geometry import Face, HexPrism, Polyhedron, rotation, rotation_between, rotation_from_frames
from .geometry2d import CrossSection, Polygon2D, reflection2d, rotation2d
from .interp import lerp_euler, lerp_matrix, lon_lat_roll_to_matrix, matrix_to_lon_lat_roll, slerp_matrix
from .projection import Camera, face_visible, solve_camera_distance, visible_faces
from .raypath import (Cone, RayPath, RayPath2D, SegmentKind, aim, face_sequence, face_toward,
                      parallel_origins, solve_raypath, trace, verify_path)
from .raypath2d import solve_raypath_2d, unfold_2d
from .scene import (annotate, draw_axes, draw_axis_arrow, draw_raypath, draw_rotation_arc_3d, finish,
                    frame, new_figure, render_corridor, render_crystal)
from .scene2d import (annotate_2d, draw_flip_axis, draw_raypath_2d, draw_rotation_arc, draw_wedge_angle,
                      multi_panel, render_medium, render_section)
from .schematic import SplitTree, split_tree, two_face_medium, wedge_angle, wedge_apex
from .sphere import (Sphere, graticule, render_cone, render_curve, render_great_circle,
                     render_point_cloud)
from .style import FACE_COLORS, PRESETS, Preset
from .symmetry import FlipAxis, face_permutation, flip, rotate
from .unfold import Corridor, corridor_faces, straighten, unfold, unfolded_tail

__all__ = [
    "Camera", "Cone", "Corridor", "CrossSection", "FACE_COLORS", "Face", "FlipAxis", "HexPrism",
    "PRESETS", "Polygon2D", "Polyhedron", "Preset", "RayPath", "RayPath2D", "SegmentKind", "SplitTree", "Sphere",
    "aim", "annotate", "annotate_2d", "corridor_faces", "draw_axes", "draw_axis_arrow", "draw_flip_axis",
    "draw_raypath", "draw_raypath_2d", "draw_rotation_arc", "draw_rotation_arc_3d", "draw_wedge_angle", "face_permutation", "face_sequence",
    "face_toward", "face_visible", "finish", "flip", "frame", "graticule", "lerp_euler", "lerp_matrix",
    "lon_lat_roll_to_matrix", "matrix_to_lon_lat_roll", "multi_panel", "new_figure", "parallel_origins",
    "reflection2d", "render_cone", "render_corridor", "render_crystal", "render_curve",
    "render_great_circle", "render_medium", "render_point_cloud", "render_section", "rotate", "rotation", "rotation2d", "rotation_between", "rotation_from_frames",
    "slerp_matrix", "solve_camera_distance", "solve_raypath", "solve_raypath_2d", "split_tree", "straighten",
    "trace",
    "two_face_medium", "unfold", "unfold_2d", "unfolded_tail", "verify_path", "visible_faces",
    "wedge_angle", "wedge_apex",
]
