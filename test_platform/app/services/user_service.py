"""
用户领域服务：封装对 ``UserModel`` / ``user_roles`` 的数据库操作。

SQLAlchemy 2.0 风格
--------------------
- ``select(Model)`` 构造查询；``session.scalars(stmt).all()`` 取多行；``session.scalar(stmt)`` 取单行或标量。
- ``session.get(Model, pk)`` 按主键加载（未找到为 ``None``）。
- 修改关联 ``user.roles`` 后 ``commit()`` 会同步中间表。

Werkzeug 密码
------------
``generate_password_hash`` / ``check_password_hash``：与具体哈希算法版本无关地校验（字符串里自带算法前缀）。
"""

from __future__ import annotations

from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from ..converters import user_model_to_record
from ..extensions import db
from ..ids import parse_user_id
from ..models.user import UserRecord
from ..orm_models import RoleModel, UserModel


class UserService:
    """用户相关业务逻辑。"""

    def list_users(self) -> list[UserRecord]:
        """查询所有用户并转为 ``UserRecord`` 列表。"""
        rows = db.session.scalars(select(UserModel)).all()
        return [user_model_to_record(u) for u in rows]

    def get_by_id(self, user_id: str | int | None) -> UserRecord | None:
        """按主键查询；``user_id`` 非法或不存在返回 ``None``。"""
        uid = parse_user_id(user_id)
        if uid is None:
            return None
        u = db.session.get(UserModel, uid)
        return user_model_to_record(u) if u else None

    def get_by_username(self, username: str) -> UserRecord | None:
        """登录时用用户名定位用户。"""
        u = db.session.scalar(select(UserModel).where(UserModel.username == username))
        return user_model_to_record(u) if u else None

    def create(self, username: str, password: str, role_ids: list[str]) -> UserRecord:
        """
        新建用户并绑定角色。

        :raises ValueError: 用户名已存在。
        """
        if self.get_by_username(username):
            raise ValueError("用户名已存在")
        user = UserModel(
            username=username,
            password_hash=generate_password_hash(password),
        )
        for rid in role_ids:
            r = db.session.get(RoleModel, rid)
            if r:
                user.roles.append(r)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user_model_to_record(user)

    def update(
        self,
        user_id: str | int | None,
        *,
        password: str | None = None,
        role_ids: list[str] | None = None,
    ) -> UserRecord | None:
        """更新密码和/或角色；主键无效或用户不存在返回 ``None``。"""
        uid = parse_user_id(user_id)
        if uid is None:
            return None
        user = db.session.get(UserModel, uid)
        if not user:
            return None
        if password is not None:
            user.password_hash = generate_password_hash(password)
        if role_ids is not None:
            user.roles.clear()
            for rid in role_ids:
                r = db.session.get(RoleModel, rid)
                if r:
                    user.roles.append(r)
        db.session.commit()
        db.session.refresh(user)
        return user_model_to_record(user)

    def delete(self, user_id: str | int | None) -> bool:
        """删除用户（级联删除 ``user_roles`` 中的关联行）。"""
        uid = parse_user_id(user_id)
        if uid is None:
            return False
        user = db.session.get(UserModel, uid)
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True

    def verify_password(self, rec: UserRecord, password: str) -> bool:
        """校验明文密码是否与 ``password_hash`` 匹配。"""
        return check_password_hash(rec.password_hash, password)
