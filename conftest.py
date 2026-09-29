"""仓库级 pytest 钩子：``@pytest.mark.local_data`` 测试缺只留本地的产物时 skip（见 ``halo_notes/repo/testing.py``）。"""

import pytest

from halo_notes.repo.testing import MARK, local_only_path, skip_reason


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    try:
        return (yield)
    except FileNotFoundError as exc:
        rel = local_only_path(exc) if item.get_closest_marker(MARK) else None
        if rel is None:
            raise
        pytest.skip(skip_reason(rel))
