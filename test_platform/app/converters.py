"""
ORM 模型与 **领域对象（dataclass）** 之间的转换，以及时间字段解析。

分层目的
--------
- **ORM（``orm_models``）**：贴近表结构，给 SQLAlchemy 用。
- **领域对象（``models/*.py``）**：给 Service / 序列化用，避免把 ORM 泄漏到路由的每个角落。
- **API JSON**：由 ``serializers`` 与 ``dataclass.to_dict()`` 再裁剪敏感字段。

``parse_executed_at``
---------------------
HTTP JSON 里是字符串；MySQL 里用 ``DateTime``。使用标准库 ``datetime.fromisoformat``（Python 3.7+），
并兼容末尾 ``Z``（UTC 常见写法）。**非法字符串** 抛 ``ValueError``，由路由捕获返回 400，避免 500。
"""

from __future__ import annotations

from datetime import datetime

from .models.role import Role
from .models.testcase import TestCase
from .models.user import UserRecord
from .orm_models import RoleModel, TestCaseModel, UserModel


def user_model_to_record(u: UserModel) -> UserRecord:
    """将 ``UserModel`` 转为 ``UserRecord``（含 ``role_ids`` 从关联表收集）。"""
    return UserRecord(
        id=u.id,
        username=u.username,
        password_hash=u.password_hash,
        role_ids=[r.id for r in u.roles],
    )


def role_model_to_role(r: RoleModel) -> Role:
    """将 ``RoleModel`` 转为领域 ``Role``。"""
    return Role(id=r.id, name=r.name, kind=r.kind)


def testcase_model_to_case(m: TestCaseModel) -> TestCase:
    """
    将 ``TestCaseModel`` 转为领域 ``TestCase``。

    ``executed_at`` 在库中为 ``datetime``，API 中输出 ISO8601 字符串（与 JSON 一致）。
    """
    ex: datetime | None = m.executed_at
    ex_s = ex.isoformat(timespec="seconds") if ex else None
    return TestCase(
        id=m.id,
        name=m.name,
        module=m.module or "",
        level=m.level or "",
        pre_steps=m.pre_steps or "",
        steps=m.steps or "",
        expected_result=m.expected_result or "",
        actual_result=m.actual_result,
        executor=m.executor,
        executed_at=ex_s,
    )


def parse_executed_at(value: object) -> datetime | None:
    """
    把请求体里的 ``executed_at`` 转为 ``datetime`` 或 ``None``。

    :param value: ``None``、空串、``datetime``、或 ISO8601 字符串。
    :return: 无时区信息则按 naive datetime 存库（由业务约定解释）。
    :raises ValueError: 非空但无法解析的字符串（应映射为 HTTP 400）。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError as e:
        raise ValueError(
            "executed_at 须为 ISO8601 日期时间字符串（可含时区），未执行请省略该字段或传 null；"
            f"示例 2026-04-05T12:30:00。无法解析: {s!r}"
        ) from e
