"""
应用配置（Flask ``app.config`` 的数据源）。

Flask 用法
----------
``app.config.from_object(Config)`` 会把 **类属性中大写** 的项拷贝进 ``app.config`` 字典，
例如 ``SQLALCHEMY_DATABASE_URI``、``SECRET_KEY``。

SQLAlchemy / Flask-SQLAlchemy
-----------------------------
- ``SQLALCHEMY_DATABASE_URI``：数据库连接 URI；使用 **PyMySQL** 驱动时前缀为 ``mysql+pymysql://``。
- ``SQLALCHEMY_TRACK_MODIFICATIONS``：设为 ``False`` 可省内存与开销（Flask-SQLAlchemy 旧版跟踪）。
- ``SQLALCHEMY_ENGINE_OPTIONS``：传给底层 ``create_engine`` 的参数；``pool_pre_ping`` 可在连接失效时自动检测重连。

安全相关
--------
- ``SECRET_KEY``：用于 **签名会话 Cookie**；泄露会导致会话可被伪造，生产必须用强随机值并通过环境变量注入。
- ``SESSION_COOKIE_HTTPONLY``：禁止 JavaScript 读 Cookie，降低 XSS 窃取会话风险。
- ``SESSION_COOKIE_SAMESITE=Lax``：减轻 CSRF；纯 API + 跨站前端时可能需调整为 ``None`` 并配合其他防护。

其它
----
- ``JSON_AS_ASCII=False``：``jsonify`` 对中文等使用 UTF-8 直出，而不是 ``\\uXXXX`` 转义。
- ``STORE_DIR``：历史 JSON 存储目录（当前主流程用 MySQL，该配置可保留兼容）。
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus


def _base_dir() -> Path:
    """``test_platform/`` 根目录（``app`` 的上一级）。"""
    return Path(__file__).resolve().parent.parent


class Config:
    """默认配置；可通过子类覆盖（如关闭 DEBUG）。"""

    SECRET_KEY = os.environ.get("TEST_PLATFORM_SECRET_KEY") or "dev-change-me-in-production"
    JSON_AS_ASCII = False
    STORE_DIR = Path(os.environ.get("TEST_PLATFORM_STORE_DIR") or (_base_dir() / "instance" / "store"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "123456")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "PythonProject2")

    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_PLATFORM_DATABASE_URI") or (
        f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{quote_plus(MYSQL_DATABASE)}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}


class DevelopmentConfig(Config):
    """开发配置：开启 Flask DEBUG（详细错误页、自动重载）。"""

    DEBUG = True


config_by_name = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
}
