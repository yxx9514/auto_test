"""
用户领域对象（非 ORM）。

``UserRecord`` 含 ``password_hash``：仅服务层与登录校验使用，**绝不**通过 ``serializers.user_public_dict`` 输出给客户端。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class UserRecord:
    """
    表示持久化用户的一行核心字段。

    :ivar id: 自增整型主键（1～999999 业务约定）。
    :ivar username: 登录名，唯一。
    :ivar password_hash: Werkzeug 生成的哈希串。
    :ivar role_ids: 角色表主键（字符串）列表，顺序可与中间表插入顺序一致。
    """

    id: int
    username: str
    password_hash: str
    role_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        """转字典（调试或日志慎用，含敏感哈希）。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserRecord:
        """从 dict 构造（如导入导出场景）。"""
        role_ids = data.get("role_ids") or []
        if not isinstance(role_ids, list):
            role_ids = []
        return cls(
            id=int(data["id"]),
            username=str(data["username"]),
            password_hash=str(data["password_hash"]),
            role_ids=[str(x) for x in role_ids],
        )
