"""
SQLAlchemy ORM 模型（与 MySQL 表一一对应）。

Flask-SQLAlchemy
----------------
所有模型继承 ``db.Model``；``db`` 定义在 ``extensions.py``。表名由 ``__tablename__`` 指定。

关系
----
- **用户 ↔ 角色**：多对多，中间表 ``user_roles``（两个外键联合主键）。
- ``relationship(..., secondary=user_roles)``：ORM 层跨表导航；``lazy="selectin"`` 可减少 N+1 查询（用户列表带角色时）。

外键与级联
----------
``ondelete="CASCADE"``：删除用户或角色时，中间表关联行自动删除（需 InnoDB）。

主键策略
--------
- ``users.id`` / ``test_cases.id``：整型自增；**业务上**限制在 1～999999（应用层 ``ids.py``），因 MySQL 对 AUTO_INCREMENT 列的 CHECK 有限制。
- ``roles.id``：字符串（如 ``role_admin``），便于种子数据稳定引用。

``datetime`` 列
---------------
``TestCaseModel.executed_at`` 映射为 Python ``datetime``；API 层用 ``converters`` 做字符串互转。
"""

from __future__ import annotations

from .extensions import db

user_roles = db.Table(
    "user_roles",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "role_id",
        db.String(36),
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class UserModel(db.Model):
    """用户表：自增整型主键 + 唯一用户名 + 密码哈希。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    roles = db.relationship(
        "RoleModel",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )


class RoleModel(db.Model):
    """角色表：字符串主键，区分 system / business。"""

    __tablename__ = "roles"

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    kind = db.Column(db.String(16), nullable=False)
    users = db.relationship(
        "UserModel",
        secondary=user_roles,
        back_populates="roles",
    )


class TestCaseModel(db.Model):
    """测试用例表：自增整型主键 + 文本步骤与结果字段。"""

    __tablename__ = "test_cases"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    module = db.Column(db.String(255), nullable=False, default="")
    level = db.Column(db.String(32), nullable=False, default="")
    pre_steps = db.Column(db.Text, nullable=False, default="")
    steps = db.Column(db.Text, nullable=False, default="")
    expected_result = db.Column(db.Text, nullable=False, default="")
    actual_result = db.Column(db.Text, nullable=True)
    executor = db.Column(db.String(128), nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
