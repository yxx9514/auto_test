"""
依赖注入的简易工厂（Service Locator 轻量版）。

作用
----
路由层（``routes/*.py``）不直接 ``new UserService()``，而是通过 **无参工厂** 获取服务实例，
便于以后替换为带 ``db``、带缓存的实现，或做单元测试时 patch。

说明
----
当前 ``UserService`` / ``RoleService`` / ``CaseService`` 内部直接使用全局 ``db.session``（Flask-SQLAlchemy
在应用上下文中绑定），因此工厂 **不需要** 传入 ``app``；必须在 **请求上下文或 app_context** 内调用。

若未来服务需要 ``current_app`` 读配置，可改为从 ``flask import current_app`` 读取。
"""

from __future__ import annotations

from .services.case_service import CaseService
from .services.role_service import RoleService
from .services.user_service import UserService


def user_service() -> UserService:
    """返回用户领域服务实例（无状态，可重复调用）。"""
    return UserService()


def role_service() -> RoleService:
    """返回角色领域服务实例。"""
    return RoleService()


def case_service() -> CaseService:
    """返回用例领域服务实例。"""
    return CaseService()
