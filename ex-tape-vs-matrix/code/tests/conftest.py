"""让 tests/ 能 import 上一级的章内脚本（`tape_halo_function` / `crosscheck_bridge` / `crosscheck_a`），与
`halo_notes/*/tests/test_figures.py` 把章 `code/` 目录塞进 sys.path 的做法一致。"""

import sys
from pathlib import Path

CODE_DIR = str(Path(__file__).resolve().parents[1])
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)
