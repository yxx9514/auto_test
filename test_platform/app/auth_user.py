"""
Flask-Login 所需的「当前用户」对象类型。

Flask-Login 机制简述
--------------------
1. 登录成功后调用 ``login_user(user)``，把 **用户主键**（及可选「记住我」）写入 **签名的会话 Cookie**。
2. 后续请求带上 Cookie，Flask-Login 用 ``user_loader`` 回调把 id 换回用户对象。
3. ``UserMixin`` 提供默认的 ``is_authenticated``、``get_id()`` 等；``get_id()`` 会把 ``id`` 转成 **字符串** 存会话。

为什么不用 ORM ``UserModel`` 直接当登录用户？
---------------------------------------------
- 会话里只应放 **最小信息**；ORM 对象可能惰性加载关联，且不宜长期挂会话。
- 这里用轻量类只带 ``id``、``username``、``role_ids``，与 ``UserRecord`` 对齐。
"""

from __future__ import annotations

from flask_login import UserMixin


class PlatformUser(UserMixin):
    """
    已登录用户在内存中的表示（由 ``user_loader`` 构造）。

    :ivar id: 数据库主键（整数）；``UserMixin.get_id()`` 会转为 str 写入会话。
    :ivar username: 登录名，便于日志或 API 展示。
    :ivar role_ids: 角色主键列表（字符串 id，与 ``roles`` 表一致）。
    """

    def __init__(self, user_id: int, username: str, role_ids: list[str]) -> None:
        self.id = user_id
        self.username = username
        self.role_ids = role_ids
