"""history-rewrite 工具共用：把仓库根加进 sys.path 以 import 划界规则（halo_notes.repo.layout，stdlib-only）。"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from halo_notes.repo import layout  # noqa: E402,F401
