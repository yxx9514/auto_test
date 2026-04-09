"""
数据库 **建库**（不是建表）：保证 ``MYSQL_DATABASE`` 指向的库存在。

为什么不用 SQLAlchemy 建库？
---------------------------
``create_engine("mysql+pymysql://.../dbname")`` 要求 **库已存在**，否则连接失败。
因此先用 **PyMySQL** 以「不指定 database」的方式连上 MySQL 服务器，执行::

    CREATE DATABASE IF NOT EXISTS `...` CHARACTER SET utf8mb4 ...

PyMySQL 要点
------------
- ``pymysql.connect(..., charset="utf8mb4")``：与表、连接串字符集一致，避免中文乱码。
- ``OperationalError``：常见原因包括拒绝连接、账号密码错误、主机不可达。

注意：反引号包裹库名可防止库名与保留字冲突；**不要**把用户输入直接拼进 SQL（防注入）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pymysql
from pymysql.err import OperationalError

if TYPE_CHECKING:
    from flask import Flask


def ensure_database_exists(app: "Flask") -> None:
    """
    若配置中的 MySQL 库不存在则创建（utf8mb4 / utf8mb4_unicode_ci）。

    :param app: 已加载 ``config`` 的 Flask 应用（读取 ``MYSQL_*`` 键）。
    :raises RuntimeError: 连接失败或建库失败时包装为可读错误信息。
    """
    cfg = app.config
    host = cfg["MYSQL_HOST"]
    port = int(cfg["MYSQL_PORT"])
    user = cfg["MYSQL_USER"]
    password = cfg["MYSQL_PASSWORD"]
    db_name = cfg["MYSQL_DATABASE"]

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    except OperationalError as e:
        conn.close()
        raise RuntimeError(
            f"无法连接 MySQL 或创建数据库 `{db_name}`。请确认服务已启动且账号密码正确。原始错误: {e}"
        ) from e
    finally:
        try:
            conn.close()
        except Exception:
            pass
