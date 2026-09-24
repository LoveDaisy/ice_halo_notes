"""ch3 光路 ground truth 清单两份副本逐字节一致：本仓 ``03-parallel-raypaths/data/raypath_ground_truth.txt`` 是原始出处，
Lumice Integral 包内 ``lumice_integral/symmetry/data/raypath_ground_truth.txt`` 是 2026-09-24 拷入的派生副本
（``ground_truth_groups()`` 的默认路径指向它）。任一方漂移即失败——须人工核对哪边是权威版本后同步，不得单边改。"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

LOCAL = Path(__file__).resolve().parents[3] / "03-parallel-raypaths" / "data" / "raypath_ground_truth.txt"


def test_ground_truth_file_matches_lumice_integral_copy():
    li = files("lumice_integral.symmetry") / "data" / "raypath_ground_truth.txt"
    assert li.is_file(), f"LI 包内副本不存在：{li}"
    local, packaged = LOCAL.read_bytes(), li.read_bytes()
    assert local == packaged, (f"LI 副本已漂移（本仓 {len(local)} 字节 / LI {len(packaged)} 字节）："
                               "需人工核对哪边是权威版本后同步")
