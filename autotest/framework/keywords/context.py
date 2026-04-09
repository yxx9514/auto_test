from __future__ import annotations

"""
关键字执行上下文（Keyword Context）。

你可以把它理解为“关键字用例运行时的共享环境”：
- settings：读取到的环境配置
- http：HTTP 客户端（API 关键字会用到）
- variables：步骤之间传递变量（`save_as` 保存、`${...}` 引用）
- registry：关键字名 -> 可执行函数 的映射表
- templates：大请求体模板（名 -> dict），来自 ``data/payload_templates/*.yaml``，供 ``json_template`` 使用
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from loguru import logger

from ..api.client import HttpClient
from ..core.config import Settings

KeywordFunc = Callable[["KeywordContext", dict[str, Any]], Any]


@dataclass
class KeywordContext:
    """关键字运行时上下文。"""

    settings: Settings
    http: HttpClient
    variables: dict[str, Any] = field(default_factory=dict)
    registry: dict[str, KeywordFunc] = field(default_factory=dict)
    responses_mock: Any | None = None
    templates: dict[str, Any] = field(default_factory=dict)

    def log(self, message: str) -> None:
        """关键字执行时的统一日志入口（可扩展为写入 Allure step）。"""
        logger.info(message)

