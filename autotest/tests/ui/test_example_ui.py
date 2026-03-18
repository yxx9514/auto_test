from __future__ import annotations

"""
UI + PO 示例（Playwright）。

注意：UI 依赖是可选的；如果没安装 `.[ui]`，该文件会在收集阶段被 skip。
"""

import importlib.util

import pytest

from pages.example_home_page import ExampleHomePage

if importlib.util.find_spec("playwright") is None or importlib.util.find_spec("pytest_playwright") is None:
    pytest.skip("UI deps not installed. Run: pip install -e \".[ui]\" && playwright install", allow_module_level=True)


@pytest.mark.ui
def test_open_home_and_check_title(page, settings):
    home = ExampleHomePage(page, base_url=settings.ui.base_url)
    home.open()
    assert "Example" in home.title()

