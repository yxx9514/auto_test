"""
角色领域对象。

``kind`` 取值 ``system`` / ``business``：用于后续权限扩展（如仅系统角色可删库级配置）。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Role:
    """
    :ivar id: 字符串主键（稳定 id，如 ``role_admin``）。
    :ivar name: 展示名（唯一）。
    :ivar kind: ``system`` 或 ``business``。
    """

    id: str
    name: str
    kind: str

    def to_dict(self) -> dict[str, Any]:
        """用于 JSON 响应。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Role:
        """反序列化。"""
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            kind=str(data["kind"]),
        )
