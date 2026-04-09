"""
注册所有 HTTP 蓝图（Blueprint）。

Flask Blueprint
---------------
把不同模块的路由拆到独立文件，避免单文件过大；``url_prefix`` 统一加在 ``/api/v1/...`` 下。

注册顺序一般不影响匹配；若存在路径冲突，以先注册的规则为准（本项目中无重叠）。
"""

from __future__ import annotations

from flask import Flask

from .auth import bp as auth_bp
from .cases import bp as cases_bp
from .roles import bp as roles_bp
from .users import bp as users_bp


def register_blueprints(app: Flask) -> None:
    """
    将认证、用户、角色、用例蓝图挂到应用上。

    :param app: ``create_app`` 创建的 ``Flask`` 实例。
    """
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(roles_bp, url_prefix="/api/v1/roles")
    app.register_blueprint(cases_bp, url_prefix="/api/v1/cases")
