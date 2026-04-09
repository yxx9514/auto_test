"""
URL 与 JSON 中的 **数字主键** 校验（用户 id、用例 id）。

设计背景
--------
- 用户与用例主键在库中为 **自增整数**，业务上约定 **最多 6 位**（1～999999）。
- URL 路径里的片段永远是 **字符串**（如 ``"/api/v1/users/12"``），需解析为 ``int`` 并校验范围。
- Flask-Login 的 ``user_id`` 在会话里常以 **字符串** 保存，``user_loader`` 也会收到字符串。

特别注意：Python 中 ``bool`` 是 ``int`` 的子类，必须先排除 ``bool``，否则 ``True`` 会被当成 ``1``。
"""

from __future__ import annotations

MAX_NUMERIC_ID = 999_999
MAX_USER_ID = MAX_NUMERIC_ID
MAX_CASE_ID = MAX_NUMERIC_ID


def parse_numeric_id(raw: str | int | None) -> int | None:
    """
    将输入解析为范围内的正整数；非法则返回 ``None``（由上层决定返回 400 还是 404）。

    :param raw: 路径参数、查询串、JSON 数字或字符串。
    :return: ``1 <= n <= MAX_NUMERIC_ID`` 的整数，否则 ``None``。
    """
    if raw is None:
        return None
    try:
        if isinstance(raw, bool):
            return None
        if isinstance(raw, int):
            n = raw
        else:
            s = str(raw).strip()
            if not s.isdigit():
                return None
            n = int(s)
    except (TypeError, ValueError):
        return None
    if n < 1 or n > MAX_NUMERIC_ID:
        return None
    return n


def parse_user_id(raw: str | int | None) -> int | None:
    """用户 id 解析，语义与 ``parse_numeric_id`` 相同（别名便于路由层阅读）。"""
    return parse_numeric_id(raw)


def parse_case_id(raw: str | int | None) -> int | None:
    """用例 id 解析，语义与 ``parse_numeric_id`` 相同。"""
    return parse_numeric_id(raw)
