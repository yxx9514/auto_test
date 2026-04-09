"""
角色管理路由：列表、创建、删除。

说明
----
- 角色主键为 **字符串**（与 Postman / 前端传入的 ``role_id`` 一致），与用户/用例的整型主键不同。
- ``kind`` 仅允许 ``system`` 或 ``business``，与种子数据及后续权限扩展约定一致。
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import login_required

from ..deps import role_service

bp = Blueprint("roles", __name__)


@bp.route("", methods=["GET"])
@login_required
def list_roles():
    """返回全部角色。"""
    rs = role_service()
    return jsonify({"roles": [r.to_dict() for r in rs.list_roles()]})


@bp.route("", methods=["POST"])
@login_required
def create_role():
    """创建角色；名称重复返回 409。"""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    kind = (data.get("kind") or "").strip()
    if not name or kind not in ("system", "business"):
        return jsonify(
            {
                "error": "invalid_request",
                "message": "name 必填，kind 为 system 或 business",
            }
        ), 400
    rs = role_service()
    try:
        role = rs.create(name, kind)
    except ValueError as e:
        return jsonify({"error": "conflict", "message": str(e)}), 409
    return jsonify({"role": role.to_dict()}), 201


@bp.route("/<role_id>", methods=["DELETE"])
@login_required
def delete_role(role_id: str):
    """按主键删除角色；关联用户的中间表行由外键级联删除。"""
    rs = role_service()
    if not rs.delete(role_id):
        return jsonify({"error": "not_found", "message": "角色不存在"}), 404
    return jsonify({"ok": True})
