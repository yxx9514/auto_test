"""
领域服务层包。

``Service`` 类集中处理事务边界（``commit``/``rollback`` 策略可在中间件统一加强），
路由层只做 HTTP 解析、状态码与错误消息映射。
"""

from __future__ import annotations

from .case_service import CaseService
from .role_service import RoleService
from .user_service import UserService

__all__ = ["CaseService", "RoleService", "UserService"]
