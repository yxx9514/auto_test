"""
================================================================================
pytest 根目录 conftest.py —— 全局夹具（Fixture）与报告增强
================================================================================

pytest 如何发现本文件？
----------------------
``pytest`` 会从 **测试目录向上** 查找名为 ``conftest.py`` 的文件；本文件位于 ``tests/`` 根下，
因此 ``tests/api``、``tests/keyword``、``tests/ui`` 里的用例 **自动继承** 这里定义的 fixture。

核心概念：Fixture（夹具）
------------------------
- 用 ``@pytest.fixture`` 装饰的函数，返回值可 **注入** 到测试函数参数中。
- ``scope="session"``：整个 pytest 进程只执行一次，适合读配置、建昂贵资源。
- ``autouse=True``：不写在参数里也会 **自动执行**（如本文件的 ``_init`` 日志初始化）。

涉及第三方库
------------
- **pytest**：测试框架；``hookwrapper`` 钩子可拦截测试各阶段报告。
- **responses**：拦截 ``requests`` 发出的真实 HTTP，返回预设响应（离线、稳定）。
- **allure-pytest**：失败时 ``allure.attach`` 附加文本/图片到 HTML 报告。
- **pathlib**：用 ``Path(__file__)`` 定位资源，避免依赖「当前工作目录 cwd」。

子目录 ``tests/keyword/conftest.py`` 中的定义会与 **本文件合并**；离测试越近的 conftest 优先级越高（可覆盖同名 fixture）。

导入说明
--------
源码使用 ``from framework.xxx import ...``（与 ``pyproject.toml`` 里 setuptools 的 ``packages`` 一致：
顶层包名为 ``framework``、``pages``，**没有** ``autotest`` 这一层 Python 包）。
请在 ``autotest`` 目录执行 ``pip install -e .``，或把该目录加入 ``PYTHONPATH``，否则会出现 ``ModuleNotFoundError: No module named 'framework'``。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import allure
import pytest
import responses

from framework.api.client import HttpClient
from framework.core.config import load_settings
from framework.core.payload_templates import load_payload_templates
from framework.core.logging import setup_logger
from framework.keywords.builtin import default_registry
from framework.keywords.context import KeywordContext
from framework.ui.playwright_support import playwright_available, safe_page_screenshot


@pytest.fixture(scope="session", autouse=True)
def _init() -> None:
    """
    会话级自动执行：初始化 loguru 等全局日志。

    不设返回值；仅副作用。``scope="session"`` 保证整次 pytest 只跑一次。
    """
    setup_logger()


@pytest.fixture(scope="session")
def settings():
    """
    加载 ``configs/config.yaml``（或环境变量 ``AUTOTEST_CONFIG`` 指向的其它 YAML）。

    返回 ``Settings`` 数据类，内含 ``api.base_url``、``ui.*`` 等。
    多环境示例（PowerShell）::

        $env:AUTOTEST_CONFIG="D:\\...\\autotest\\configs\\test_platform.yaml"
        pytest
    """
    cfg = os.getenv("AUTOTEST_CONFIG")
    return load_settings(cfg)


@pytest.fixture(scope="session")
def http_client(settings):
    """
    基于 ``requests.Session`` 的 HTTP 客户端，**同一 session 内自动保持 Cookie**。

    与关键字 ``api_post`` 联调登录接口时，同一 fixture 实例会带上登录后的 ``session`` Cookie。
    ``scope="session"`` 表示所有用例共用一个 Session；若需用例级隔离可改为默认 ``function`` scope。
    """
    return HttpClient(base_url=settings.api.base_url, timeout=settings.api.timeout)


@pytest.fixture
def responses_mock():
    """
    激活 ``responses`` 对 ``requests`` 的补丁；在 ``with`` 块内注册的 URL 返回模拟响应。

    ``assert_all_requests_are_fired=False``：未命中的请求不一定报错（便于混合 mock 与真实请求时调试）。
    ``yield`` 之后 pytest 会退出上下文管理器，自动卸载 mock。
    """
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def keyword_ctx(settings, http_client, responses_mock):
    """
    关键字驱动用例的 **执行上下文**：配置 + HTTP 客户端 + mock + 关键字注册表。

    ``KeywordContext.registry`` 默认合并 ``builtin.default_registry()``（含 ``api_get``、``api_post`` 等）。
    测试函数里调用 ``run_steps(keyword_ctx, steps)`` 即可按 YAML 顺序执行关键字。
    """
    root = Path(__file__).resolve().parents[1]
    ctx = KeywordContext(settings=settings, http=http_client, responses_mock=responses_mock)
    ctx.templates.update(load_payload_templates(root / "data" / "payload_templates"))
    ctx.registry.update(default_registry())
    return ctx


def pytest_sessionstart(session: Any) -> None:
    """
    pytest 钩子：整个测试会话 **开始时** 调用一次（早于用例执行）。

    这里写入 Allure 的 ``environment.properties``，报告里可展示 Python 版本等项目信息。
    ``session`` 参数为 pytest 的 Session 对象，本处未使用但需保留签名以符合钩子约定。
    """
    results_dir = Path("allure-results")
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "environment.properties").write_text(
        "project=autotest-framework\n" f"python={os.sys.version.split()[0]}\n",
        encoding="utf-8",
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: Any, call: Any):
    """
    钩子包装器：在每个测试阶段（setup/call/teardown）生成报告对象后介入。

    - ``hookwrapper=True``：必须先 ``yield``，再在之后读取 ``outcome.get_result()``。
    - ``tryfirst=True``：尽量早执行，便于给 ``item`` 挂上 ``rep_call`` 等属性供其它插件使用。

    当 **call 阶段失败** 时：尝试从 ``responses_mock`` 抠出 HTTP 调用链附加到 Allure；
    若存在 Playwright ``page``，则截屏附加，便于 UI 失败排查。
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

    if rep.when == "call" and rep.failed:
        rsps = item.funcargs.get("responses_mock")
        if rsps is not None:
            try:
                calls = []
                for c in getattr(rsps, "calls", []):
                    req = getattr(c, "request", None)
                    resp = getattr(c, "response", None)
                    calls.append(
                        {
                            "method": getattr(req, "method", None),
                            "url": getattr(req, "url", None),
                            "request_body": getattr(req, "body", None),
                            "status": getattr(resp, "status_code", None),
                            "response_body": getattr(resp, "text", None),
                        }
                    )
                allure.attach(str(calls), name="http_calls", attachment_type=allure.attachment_type.TEXT)
            except Exception:
                pass

        if playwright_available():
            page = item.funcargs.get("page")
            if page is not None:
                png = safe_page_screenshot(page)
                if png:
                    allure.attach(png, name="screenshot", attachment_type=allure.attachment_type.PNG)
