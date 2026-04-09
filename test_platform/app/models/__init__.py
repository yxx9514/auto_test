"""
与 HTTP/业务传输相关的 **轻量数据类**（``dataclasses``）。

与 ``orm_models`` 的区别
------------------------
- ORM 对象绑定 ``db.session``、惰性加载；不宜随意序列化或跨层传递。
- 这里的数据类无会话依赖，适合 Service 返回、再经 ``serializers`` 转成 JSON 安全结构。
"""

from __future__ import annotations

from .role import Role
from .testcase import TestCase
from .user import UserRecord

__all__ = ["Role", "TestCase", "UserRecord"]
