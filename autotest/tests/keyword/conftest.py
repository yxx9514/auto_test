"""
================================================================================
tests/keyword 目录局部 conftest —— 仅对 keyword 子目录及子包生效
================================================================================

pytest conftest 作用域
----------------------
- 本文件与 ``tests/conftest.py`` **合并**：keyword 下的测试可同时使用两边的 fixture。
- 此处定义的 ``keyword_ctx_live`` **不会**覆盖根目录的 ``keyword_ctx``（名称不同）。

keyword_ctx_live 的设计意图
----------------------------
- **不使用 responses**：``KeywordContext.responses_mock=None``，关键字如 ``api_post`` 走真实 TCP。
- **独立配置**：显式 ``load_settings(.../configs/test_platform.yaml)``，不依赖 ``AUTOTEST_CONFIG``，
  避免与默认 ``config.yaml``（mock 示例用的假 base_url）混淆。
- **函数级 scope**：每个测试函数新的 ``HttpClient`` Session；若需整文件共用一个登录态可改为 ``module`` scope（注意测试间数据污染）。

与根目录 ``http_client`` 的关系
------------------------------
本 fixture **自建** ``HttpClient``，不注入根 conftest 的 ``http_client``，从而使用 **test_platform 专用 base_url**，
且不受 session 级共享 Session 与 mock 混用问题影响。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from framework.api.client import HttpClient
from framework.core.config import load_settings
from framework.core.payload_templates import load_payload_templates
from framework.keywords.builtin import default_registry
from framework.keywords.context import KeywordContext


@pytest.fixture
def keyword_ctx_live():
    """
    构造面向真实 test_platform 的关键字上下文。

    :return: 已注册内置关键字的 ``KeywordContext``；``responses_mock`` 为 ``None``。
    """
    root = Path(__file__).resolve().parents[2]
    settings = load_settings(root / "configs" / "test_platform.yaml")
    http = HttpClient(base_url=settings.api.base_url, timeout=settings.api.timeout)
    ctx = KeywordContext(settings=settings, http=http, responses_mock=None)
    ctx.templates.update(load_payload_templates(root / "data" / "payload_templates"))
    ctx.registry.update(default_registry())
    return ctx
