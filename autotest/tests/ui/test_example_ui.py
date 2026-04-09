"""
================================================================================
UI 自动化示例：Playwright + Page Object（PO）
================================================================================

可选依赖
--------
UI 栈（``playwright``、``pytest-playwright``）在 ``pyproject.toml`` 的 ``[project.optional-dependencies] ui`` 中，
默认 **未安装**。未安装时本模块在 **导入阶段** 即 ``pytest.skip``，避免收集错误。

安装与浏览器驱动::

    pip install -e ".[ui]"
    playwright install

Page Object 模式
----------------
把「页面元素定位 + 基本操作」封到 ``pages/`` 下的类（如 ``ExampleHomePage``），
用例只描述 **业务步骤**（打开首页、断言标题），降低用例对 DOM 细节的耦合。

Fixture ``page``
----------------
由 ``pytest-playwright`` 插件提供：每个用例一个独立浏览器上下文/页面（默认可配置 scope），
失败时根 ``conftest`` 里可尝试自动截屏附加到 Allure（若 ``playwright_available()``）。

执行（需已装 UI 依赖）::

    pytest tests/ui/test_example_ui.py -v
"""

from __future__ import annotations

import importlib.util

import pytest

from pages.example_home_page import ExampleHomePage

# 模块级 skip：收集测试前若发现未安装 playwright，则跳过整个文件（避免 ImportError）
if importlib.util.find_spec("playwright") is None or importlib.util.find_spec("pytest_playwright") is None:
    pytest.skip(
        "UI deps not installed. Run: pip install -e \".[ui]\" && playwright install",
        allow_module_level=True,
    )


@pytest.mark.ui
def test_open_home_and_check_title(page, settings):
    """
    打开配置中的 ``ui.base_url`` 首页，断言标题包含 ``Example``。

    :param page: Playwright ``Page`` 实例（pytest-playwright 注入）。
    :param settings: 根 conftest 的 session 级配置，含 ``settings.ui.base_url`` 等。
    """
    home = ExampleHomePage(page, base_url=settings.ui.base_url)
    home.open()
    assert "Example" in home.title()
