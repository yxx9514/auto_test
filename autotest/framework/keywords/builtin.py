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
import time
from typing import Any

import responses

from ..core.jsonpath import get_path
from ..core.merge_dict import deep_merge
from .context import KeywordContext, KeywordFunc


def _build_json_from_template(ctx: KeywordContext, template_name: str, patch: dict[str, Any]) -> dict[str, Any]:
    if template_name not in ctx.templates:
        known = sorted(ctx.templates)
        hint = f" Known keys: {known}" if known else " No templates loaded (check data/payload_templates/)."
        raise KeyError(f"Unknown json_template {template_name!r}.{hint}")
    base = ctx.templates[template_name]
    if not isinstance(base, dict):
        raise TypeError(f"Template {template_name!r} must be a mapping, got {type(base)}")
    return deep_merge(base, patch)


def _resolve_api_json_body(ctx: KeywordContext, args: dict[str, Any]) -> Any:
    """
    支持三种方式（互斥）：
    - 仅 ``json``：与原来一致
    - ``json_template`` + 可选 ``json_patch``：从 ctx.templates 取底稿再合并补丁（补丁里可用 ``${}``）
    """

    has_json_key = "json" in args
    has_template = args.get("json_template") is not None
    if has_json_key and has_template:
        raise ValueError("api_post args: use either json or json_template, not both")
    if has_template:
        name = str(args["json_template"])
        patch = args.get("json_patch") or {}
        if not isinstance(patch, dict):
            raise TypeError("json_patch must be a dict")
        return _build_json_from_template(ctx, name, patch)
    if has_json_key:
        return args["json"]
    return None


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


def kw_api_post(ctx: KeywordContext, args: dict[str, Any]) -> Any:
    """
    关键字：发起 POST（JSON body），返回 `ApiResponse`。

    大 body 可放到 ``data/payload_templates/`` 中，此处用 ``json_template`` + ``json_patch`` 只写差异字段。
    """

    url = str(args["url"])
    body = _resolve_api_json_body(ctx, args)
    return ctx.http.post(url, json=body)


def kw_json_from_template(ctx: KeywordContext, args: dict[str, Any]) -> dict[str, Any]:
    """
    关键字：从模板合并出 dict，供后续步骤 ``save_as`` 后传给 ``api_post`` 的 ``json: "${body}"``。

    args: ``template``（名），可选 ``patch``（与 json_patch 语义相同）
    """

    name = str(args["template"])
    patch = args.get("patch") or {}
    if not isinstance(patch, dict):
        raise TypeError("patch must be a dict")
    return _build_json_from_template(ctx, name, patch)

def kw_api_put(ctx: KeywordContext, args: dict[str, Any]) -> Any:
    """关键字：发起 PUT（JSON body），返回 `ApiResponse`。"""

    url = str(args["url"])
    body = args.get("json")
    return ctx.http.post(url, json=body)

def kw_api_delete(ctx: KeywordContext, args: dict[str, Any]) -> Any:
    """关键字：发起 DELETE（JSON body），返回 `ApiResponse`。"""

    url = str(args["url"])
    body = args.get("json")
    return ctx.http.post(url, json=body)


def kw_assert_equals(ctx: KeywordContext, args: dict[str, Any]) -> None:
    """关键字：断言两个值相等（`actual` / `expected` 会先经过变量解析）。"""

    actual = args["actual"]
    expected = args["expected"]
    assert actual == expected, f"assert_equals failed: actual={actual!r} expected={expected!r}"


def kw_unix_timestamp(ctx: KeywordContext, args: dict[str, Any]) -> int:
    """关键字：返回当前 Unix 时间戳（秒，整数），用于拼唯一用户名等。"""

    _ = ctx, args
    return int(time.time())


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
        "api_post": kw_api_post,
        "json_from_template": kw_json_from_template,
        "assert_equals": kw_assert_equals,
        "unix_timestamp": kw_unix_timestamp,
        "assert_json_path": kw_assert_json_path,
    }

