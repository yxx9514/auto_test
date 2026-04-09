"""
Flask 扩展「单例」声明模块。

为什么单独放一个文件？
--------------------
避免 ``app/__init__.py``、``orm_models.py``、``routes`` 之间 **循环导入**。
通常做法：这里只 **创建** ``db`` / ``login_manager``，在 ``create_app`` 里再 ``init_app(app)``。

Flask-SQLAlchemy
----------------
``db = SQLAlchemy()`` 尚未绑定具体应用；``db.init_app(app)`` 之后：
- ``db.Model`` 可作为所有 ORM 模型的基类；
- ``db.session`` 是当前请求（或应用上下文）下的数据库会话。

Flask-Login
-----------
``LoginManager`` 负责：
- 解析会话中的用户 id，调用你在 ``create_app`` 里注册的 ``user_loader``；
- ``@login_required`` 装饰器拦截未登录访问。

``login_view`` 本可设为「未登录时重定向的登录页路由名」；本项目 API 用 ``unauthorized_handler`` 返回 JSON，
故将 ``login_view`` 置为 ``None`` 并在工厂里自定义未授权响应。

``session_protection="strong"``：检测客户端变化，降低会话固定攻击风险（可能使部分代理场景下频繁登出，可按需调整）。
"""

from __future__ import annotations

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login_api"
login_manager.session_protection = "strong"
