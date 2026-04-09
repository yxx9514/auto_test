"""
角色领域服务。

角色主键策略
------------
使用 ``uuid`` 生成短十六进制后缀拼成 ``role_xxx``，避免与种子里的固定 id 冲突；种子角色 id 仍为可读字符串（如 ``role_admin``）。

并发与唯一性
------------
``name`` 列有 **唯一约束**；重复插入会触发数据库错误——当前在业务层先 ``select`` 判断名称是否存在，再 ``commit``，属于乐观式防冲突（高并发下仍可能竞态，生产可依赖唯一约束捕获异常）。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from ..converters import role_model_to_role
from ..extensions import db
from ..models.role import Role
from ..orm_models import RoleModel


class RoleService:
    """角色相关业务逻辑。"""

    def list_roles(self) -> list[Role]:
        """全部角色。"""
        rows = db.session.scalars(select(RoleModel)).all()
        return [role_model_to_role(r) for r in rows]

    def get_by_id(self, role_id: str) -> Role | None:
        """按字符串主键查询。"""
        r = db.session.get(RoleModel, role_id)
        return role_model_to_role(r) if r else None

    def create(self, name: str, kind: str) -> Role:
        """
        新建角色。

        :raises ValueError: ``kind`` 非法或 ``name`` 已存在。
        """
        if kind not in ("system", "business"):
            raise ValueError("kind 必须是 system 或 business")
        exists = db.session.scalar(select(RoleModel).where(RoleModel.name == name))
        if exists:
            raise ValueError("角色名称已存在")
        role = RoleModel(id=f"role_{uuid.uuid4().hex[:12]}", name=name, kind=kind)
        db.session.add(role)
        db.session.commit()
        db.session.refresh(role)
        return role_model_to_role(role)

    def delete(self, role_id: str) -> bool:
        """删除角色；不存在返回 ``False``。"""
        r = db.session.get(RoleModel, role_id)
        if not r:
            return False
        db.session.delete(r)
        db.session.commit()
        return True
