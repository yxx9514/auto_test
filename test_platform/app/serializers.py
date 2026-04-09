"""
将领域对象格式化为 **对外 API 安全** 的字典（例如去掉 ``password_hash``）。

``user_public_dict``
--------------------
- ``UserRecord`` 含 ``role_ids``（字符串 id 列表）；前端往往需要 **角色名称**。
- 通过 ``RoleService.list_roles()`` 拉全表角色，在内存里做 id → 对象映射（数据量小可接受；量大可改为联表或缓存）。
- 若某 id 在库里不存在，返回占位 ``(未知角色)``，避免整条接口失败。
"""

from __future__ import annotations

from .models.user import UserRecord
from .services.role_service import RoleService


def user_public_dict(rec: UserRecord, roles: RoleService) -> dict:
    """
    构造可 JSON 化的用户字典（无密码）。

    :param rec: 用户记录（含 ``password_hash``，但本函数不输出该字段）。
    :param roles: 用于解析 ``role_ids`` 的服务实例。
    :return: 含 ``id``、``username``、``role_ids``、``roles``（已解析对象列表）的字典。
    """
    role_map = {r.id: r for r in roles.list_roles()}
    resolved = []
    for rid in rec.role_ids:
        if rid in role_map:
            resolved.append(role_map[rid].to_dict())
        else:
            resolved.append({"id": rid, "name": "(未知角色)", "kind": "unknown"})
    return {
        "id": rec.id,
        "username": rec.username,
        "role_ids": rec.role_ids,
        "roles": resolved,
    }
