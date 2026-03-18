from __future__ import annotations

"""
内置关键字（Built-in Keywords）。

你可以把这里当成“关键字库”，每个函数对应一种动作。
后续扩展方式：
- 新增函数 `kw_xxx`
- 在 `default_registry()` 注册 `"xxx": kw_xxx`

一个关键字函数长什么样？

- 输入：`ctx`（上下文） + `args`（从 YAML 传来的参数 dict）
- 处理：做一件事（发请求、点按钮、断言……）
- 输出：返回结果（可选）。如果 YAML 写了 `save_as`，返回值会被保存成变量
"""

import json as _json
from typing import Any

import responses

from ..core.jsonpath import get_path
from .context import KeywordContext, KeywordFunc


def kw_api_mock_get(ctx: KeywordContext, args: dict[str, Any]) -> None:
    """
    关键字：为 GET 请求注册一个 mock 响应（离线跑 API）。

    这里用 `responses` 是为了：
    - 让示例用例完全不依赖网络/外部服务
    - 真实项目里也能用它做稳定的契约测试/错误码覆盖
    """

    if ctx.responses_mock is None:
        raise RuntimeError("responses_mock is not set; use the pytest fixture to enable mocking")

    # args 来自 YAML，例如：
    #   keyword: api_mock_get
    #   args:
    #     url: "https://api.local/users/1"
    #     status: 200
    #     json: {id: 1, name: "alice"}
    url = str(args["url"])
    status = int(args.get("status") or 200)
    payload = args.get("json")
    body = _json.dumps(payload, ensure_ascii=False)
    ctx.responses_mock.add(responses.GET, url, body=body, status=status, content_type="application/json")


def kw_api_get(ctx: KeywordContext, args: dict[str, Any]) -> Any:
    """关键字：发起 GET 请求，返回 `ApiResponse`，便于 `save_as` 保存。"""

    # YAML 里通常这样写：
    #   - keyword: api_get
    #     args: { url: "https://api.local/users/1" }
    #     save_as: resp
    url = str(args["url"])
    return ctx.http.get(url)


def kw_assert_json_path(ctx: KeywordContext, args: dict[str, Any]) -> None:
    """
    关键字：断言 JSON 中某个 path 的值（极简版 jsonpath）。

    - `data_ref`：一般来自 `${resp.json}`（已被引擎解析为 dict）
    - `path`：例如 "name" 或 "items.0.id"
    """

    # YAML 例子：
    #   - keyword: assert_json_path
    #     args:
    #       data_ref: "${resp.json}"
    #       path: "name"
    #       expected: "alice"
    data = args["data_ref"]
    path = str(args.get("path") or "")
    expected = args.get("expected")
    actual = get_path(data, path) if path else data
    assert actual == expected, f"assert_json_path failed: path={path} actual={actual!r} expected={expected!r}"


def default_registry() -> dict[str, KeywordFunc]:
    return {
        "api_mock_get": kw_api_mock_get,
        "api_get": kw_api_get,
        "assert_json_path": kw_assert_json_path,
    }

