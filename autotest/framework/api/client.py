from __future__ import annotations

"""
最小可用的 HTTP Client 封装。

为什么要封装：
- 业务 API 层/关键字层不直接依赖 `requests` 的细节
- 后续想加：统一 headers、鉴权、重试、日志、请求/响应 Allure 附件 等会更集中
"""

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ApiResponse:
    """对 `requests.Response` 的轻量包装，方便在关键字/断言里使用。"""

    status_code: int
    headers: dict[str, Any]
    text: str

    def json(self) -> Any:
        """把 `text` 解析为 JSON（若为空返回 None）。"""

        import json

        return json.loads(self.text) if self.text else None


class HttpClient:
    """
    HTTP Client（基于 `requests.Session`）。

    - `base_url`：可选，传相对路径时会自动拼接
    - `timeout`：全局超时（秒）

    你以后最常见的扩展（建议照这个模板加）：

    1) 统一 headers：

        self.session.headers.update({"Authorization": "Bearer xxx"})

    2) 统一日志/Allure 附件：在 get/post 里记录 url、status、body

    3) 新增方法：put/delete/patch
    """

    def __init__(self, base_url: str = "", timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, url: str) -> str:
        """支持传绝对 URL 或相对路径。"""

        if url.startswith("http://") or url.startswith("https://"):
            return url
        if not self.base_url:
            return url
        return f"{self.base_url}/{url.lstrip('/')}"

    def get(self, url: str, **kwargs: Any) -> ApiResponse:
        r = self.session.get(self._url(url), timeout=self.timeout, **kwargs)
        return ApiResponse(r.status_code, dict(r.headers), r.text)

    def post(self, url: str, json: Any | None = None, **kwargs: Any) -> ApiResponse:
        r = self.session.post(self._url(url), json=json, timeout=self.timeout, **kwargs)
        return ApiResponse(r.status_code, dict(r.headers), r.text)

