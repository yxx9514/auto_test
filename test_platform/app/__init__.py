"""
Flask 应用工厂（Application Factory）。

为什么用工厂函数 ``create_app()`` 而不是全局 ``app = Flask(__name__)``？
--------------------------------------------------------------------
- 便于 **单元测试** 里创建多个应用实例、换配置。
- 便于 **多环境**（开发/测试/生产）切换 ``config_name``。
- 延迟绑定扩展（``db.init_app``、``login_manager.init_app``），避免循环导入。

启动顺序摘要
------------
1. ``ensure_database_exists``：用 **PyMySQL** 直连 MySQL（不指定库名），执行 ``CREATE DATABASE IF NOT EXISTS``。
2. ``db.init_app`` + ``db.create_all()``：**Flask-SQLAlchemy** 根据 ``orm_models`` 里已导入的模型建表。
3. ``seed_if_empty``：表为空时写入角色、管理员、示例用例。
4. **Flask-Login**：注册 ``user_loader``（从会话里的 user_id 查库）、``unauthorized_handler``（API 返回 JSON 401）。
5. ``register_blueprints``：挂载 ``/api/v1/...`` 路由。

下面 ``import orm_models`` 仅为了 **副作用**：让 SQLAlchemy 注册 ``UserModel`` 等表元数据，否则 ``create_all`` 不知道要建哪些表。
"""

from __future__ import annotations

from flask import Flask, jsonify

from .auth_user import PlatformUser
from .config import config_by_name
from .db_bootstrap import ensure_database_exists
from .db_seed import seed_if_empty
from .deps import user_service
from .extensions import db, login_manager
from . import orm_models as _orm_models  # noqa: F401  # 确保 create_all 能看到 ORM 模型
from .routes import register_blueprints


def create_app(config_name: str | None = None) -> Flask:
    """
    创建并配置 Flask 应用实例。

    :param config_name: ``config_by_name`` 的键，默认 ``development``；可扩展 ``production`` 等。
    :return: 已注册路由与扩展的 ``Flask`` 实例。
    """
    app = Flask(__name__)
    cfg = config_by_name.get(config_name or "default", config_by_name["default"])
    app.config.from_object(cfg)

    ensure_database_exists(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_if_empty()

    login_manager.init_app(app)
    login_manager.login_view = None

    @login_manager.unauthorized_handler
    def _unauthorized() -> tuple[dict, int]:
        """未登录访问受保护视图时，返回 JSON（不做 HTML 登录页重定向，适合纯 API）。"""
        return jsonify({"error": "unauthorized", "message": "请先登录"}), 401

    @login_manager.user_loader
    def _load_user(user_id: str):
        """
        从会话中恢复的 user_id（字符串）加载用户对象。

        Flask-Login 在每次请求时若发现会话有效，会调用此函数；返回 ``None`` 表示会话失效。
        """
        rec = user_service().get_by_id(user_id)
        if not rec:
            return None
        return PlatformUser(rec.id, rec.username, rec.role_ids)

    @app.get("/api/v1/ping")
    def ping():
        """健康检查，供监控或联调确认服务存活；无需登录。"""
        return jsonify({"ok": True, "service": "test-platform"})

    register_blueprints(app)
    return app
