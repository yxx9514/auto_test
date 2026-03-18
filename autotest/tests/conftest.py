from __future__ import annotations

"""
pytest 全局夹具与 Allure 附件增强。

你可以把这里理解为“所有用例共享的启动逻辑”：
- 统一加载配置、初始化日志
- 提供 API / 关键字 /（可选）UI 的 fixture
- 用例失败时自动附加一些排障信息到 Allure（HTTP calls / screenshot）

初学者小贴士：fixture 就像“自动准备好的变量”

例如用例函数这样写：

    def test_xxx(http_client):
        ...

pytest 会自动把 `http_client` 这个 fixture 的返回值传进来，你不用自己创建。
"""

import os
from pathlib import Path
from typing import Any

import allure
import pytest
import responses

from framework.api.client import HttpClient
from framework.core.config import load_settings
from framework.core.logging import setup_logger
from framework.keywords.builtin import default_registry
from framework.keywords.context import KeywordContext
from framework.ui.playwright_support import playwright_available, safe_page_screenshot


@pytest.fixture(scope="session", autouse=True)
def _init() -> None:
    # 统一日志入口：本地控制台 + logs/run.log
    setup_logger()


@pytest.fixture(scope="session")
def settings():
    # 允许通过环境变量覆盖配置路径（不同环境/不同人都能复用同一套用例）
    cfg = os.getenv("AUTOTEST_CONFIG")
    # 如果你有多个环境配置文件，可以这样跑：
    #   $env:AUTOTEST_CONFIG="D:\...\configs\test.yaml"  (PowerShell)
    #   pytest
    return load_settings(cfg)


@pytest.fixture(scope="session")
def http_client(settings):
    # API 用例/关键字用例都会用到同一个 HttpClient
    # 你以后如果需要“默认 headers / token / 重试”等，通常也是改这里或改 HttpClient 类
    return HttpClient(base_url=settings.api.base_url, timeout=settings.api.timeout)


@pytest.fixture
def responses_mock():
    # 用 `responses` mock 掉 requests 发出的 HTTP 请求，保证示例用例离线可运行、稳定可复现
    # 初学者理解成：把“真的 HTTP 请求”换成“我们预先写好的假响应”
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def keyword_ctx(settings, http_client, responses_mock):
    # 关键字上下文：把“环境配置 + http + mock + 关键字表”组合在一起
    # 关键字用例只需要拿到 keyword_ctx，就能跑完整个 YAML case
    ctx = KeywordContext(settings=settings, http=http_client, responses_mock=responses_mock)
    ctx.registry.update(default_registry())
    return ctx


def pytest_sessionstart(session: Any) -> None:
    # 给 Allure 写入一些环境信息（报告里能看到）
    results_dir = Path("allure-results")
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "environment.properties").write_text(
        "project=autotest-framework\n" f"python={os.sys.version.split()[0]}\n",
        encoding="utf-8",
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: Any, call: Any):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

    if rep.when == "call" and rep.failed:
        # API：附加 responses 捕获到的调用信息（请求/响应简化版）
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

        # UI：如果跑的是 Playwright，用例失败时自动截屏
        if playwright_available():
            page = item.funcargs.get("page")
            if page is not None:
                png = safe_page_screenshot(page)
                if png:
                    allure.attach(png, name="screenshot", attachment_type=allure.attachment_type.PNG)

