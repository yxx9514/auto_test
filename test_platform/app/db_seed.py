"""
首次部署时的 **种子数据**（仅当对应表无任何行时插入）。

SQLAlchemy 使用方式
-------------------
- ``select(RoleModel).limit(1)`` + ``session.scalars(...).first()``：判断表是否为空。
- ``db.session.add_all`` / ``add``：加入会话（未提交前不会真正写库）。
- ``commit()``：提交事务；失败需 ``rollback()``（本脚本在启动路径上由框架处理）。
- ``session.get(RoleModel, "role_admin")``：按主键取一行（SQLAlchemy 2.0 风格）。

密码哈希
--------
使用 **Werkzeug** ``generate_password_hash``（默认 pbkdf2:sha256），与 ``UserService.verify_password`` 校验方式一致。

多对多关联
----------
``UserModel.roles.append(admin_role)`` 依赖 ``orm_models`` 里定义的 ``relationship`` 与 ``secondary`` 表；
提交后 ``user_roles`` 关联表会自动插入对应行（外键 ``ON DELETE CASCADE`` 由模型定义）。
"""

from __future__ import annotations

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from .extensions import db
from .orm_models import RoleModel, TestCaseModel, UserModel


def seed_if_empty() -> None:
    """若 ``roles`` / ``users`` / ``test_cases`` 为空则写入演示数据。"""
    if db.session.scalars(select(RoleModel).limit(1)).first() is None:
        roles = [
            RoleModel(id="role_admin", name="admin", kind="system"),
            RoleModel(id="role_pm", name="PM", kind="business"),
            RoleModel(id="role_tse", name="TSE", kind="business"),
            RoleModel(id="role_qa", name="测试", kind="business"),
            RoleModel(id="role_dev", name="开发", kind="business"),
        ]
        db.session.add_all(roles)
        db.session.commit()

    if db.session.scalars(select(UserModel).limit(1)).first() is None:
        admin = UserModel(
            username="admin",
            password_hash=generate_password_hash("admin123"),
        )
        admin_role = db.session.get(RoleModel, "role_admin")
        if admin_role:
            admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.commit()

    if db.session.scalars(select(TestCaseModel).limit(1)).first() is None:
        sample = TestCaseModel(
            name="示例-登录接口校验",
            module="认证",
            level="P1",
            pre_steps="服务已启动；已存在测试账号。",
            steps="1. POST /api/v1/auth/login 携带正确用户名密码\n2. 检查返回 200 且含 user",
            expected_result="登录成功并返回用户信息。",
            actual_result=None,
            executor=None,
            executed_at=None,
        )
        db.session.add(sample)
        db.session.commit()
