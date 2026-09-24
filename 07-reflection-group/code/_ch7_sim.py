# 图 6（fig_halos_columns.py）与 7.5 底图（sim_pose_to_sky_backdrop.py）共用的 Lumice 过滤器构造（R2-1，一份实现）：
# 正文里的 #k 是**矩阵（共轭类）**，不是一条光路——所以过滤器要放进「镜面积落在该共轭类内的全部光路」，不只是一条代表的
# PBD 轨道。做法：`reflection_group.raypaths_of_class(k)` 纯代数枚举长度 ≤ 6、相邻面不重复、折射抵消（n_out = −M n_in）的
# 全部面序列（几何可达性交给 Lumice），`representatives_under_pbd` 按 PBD 轨道去重取代表（#3 类 36 条、#2 类 88 条、
# #11 类 22 条，< 4096 的 OR 子句上限），每条代表一个 `raypath` 子过滤器，再用一个 `complex` 复合过滤器 OR 起来。
# v4.5.1 语义（源码 filter_spec.cpp::ComplexSpec）：复合过滤器自己的 symmetry 施加到全部子过滤器上，所以 PBD 写在复合
# 过滤器上（子过滤器也各带 PBD，供单独渲染 / 探针对照）。探针（2026-09-13，2×10⁶ 光线、rectangular 全天、absolute 曝光）：
# 复合过滤器渲染 = Σ 各子过滤器单独渲染（线性化后总能量比 / 逐像素），且 PBD ≠ PB（D 对称在柱晶 roll 均匀下生效），
# 记录见 scratchpad progress.md。
from __future__ import annotations

from lumice_integral.symmetry import reflection_group as rg
from halo_notes.sim import config as C

FILTER_ID = 1          # 复合过滤器的 id；scattering entry 引用它
MAX_LEN = 6            # 与 ch2 / ch3 的枚举长度一致
SYMMETRY = "PBD"


def class_representatives(number: int, max_len: int = MAX_LEN) -> tuple[tuple[int, ...], ...]:
    """#number 所在共轭类的全部光路，按 PBD 轨道去重后的代表序列。"""
    return rg.representatives_under_pbd(rg.raypaths_of_class(number, max_len))


def class_filters(number: int, *, max_len: int = MAX_LEN, symmetry: str = SYMMETRY) -> list[dict]:
    """过滤器段：``[complex(id=FILTER_ID, OR 全部代表), raypath(id=2, 代表 1), raypath(id=3, 代表 2), …]``。"""
    reps = class_representatives(number, max_len)
    subs = [C.raypath_filter(FILTER_ID + 1 + i, list(seq), symmetry) for i, seq in enumerate(reps)]
    return [C.complex_filter(FILTER_ID, [f["id"] for f in subs], symmetry)] + subs


def class_filter_paths(filters: list[dict]) -> set[tuple[int, ...]]:
    """反向：一个 filter 段里复合过滤器引用的全部子光路（单测 (c) 用）。"""
    by_id = {f["id"]: f for f in filters}
    top = by_id[FILTER_ID]
    return {tuple(by_id[i]["raypath"]) for i in C.composition_ids(top)}
