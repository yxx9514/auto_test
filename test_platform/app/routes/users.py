"""
用户 CRUD 路由。

权限说明（当前阶段）
--------------------
尚未按角色做细粒度鉴权；**凡已登录用户** 均可调用（后续可在装饰器里校验 ``admin`` 等）。

路径参数 ``user_id`` 必须为 **1～999999** 的整数；否则返回 400，避免无效输入命中数据库异常。

``PATCH`` 语义：仅更新传入字段；``password`` 与 ``role_ids`` 至少其一。
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from ..deps import role_service, user_service
from ..ids import parse_user_id
from ..serializers import user_public_dict

bp = Blueprint("users", __name__)


def _bad_user_id():
    """路径参数 user_id 非法时的统一 400 响应。"""
    return (
        jsonify(
            {
                "error": "invalid_request",
                "message": "用户 id 须为 1～999999 之间的整数（最多 6 位）",
            }
        ),
        400,
    )


def _parse_role_ids(data: dict) -> list[str]:
    """
    从 JSON 中取 ``role_ids`` 列表；类型错误抛 ``ValueError``（由视图转 400）。
    """
    raw = data.get("role_ids")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("role_ids 必须是字符串数组")
    return [str(x) for x in raw]


@bp.route("", methods=["GET"])
@login_required
def list_users():
    """用户列表（含角色解析）。"""
    us = user_service()
    rs = role_service()
    items = [user_public_dict(u, rs) for u in us.list_users()]
    return jsonify({"users": items})


@bp.route("", methods=["POST"])
@login_required
def create_user():
    """创建用户；用户名冲突返回 409。"""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "invalid_request", "message": "username 与 password 必填"}), 400
    try:
        role_ids = _parse_role_ids(data)
    except ValueError as e:
        return jsonify({"error": "invalid_request", "message": str(e)}), 400

    rs = role_service()
    for rid in role_ids:
        if not rs.get_by_id(rid):
            return jsonify({"error": "invalid_role", "message": f"角色不存在: {rid}"}), 400

    us = user_service()
    try:
        rec = us.create(username, password, role_ids)
    except ValueError as e:
        return jsonify({"error": "conflict", "message": str(e)}), 409
    return jsonify({"user": user_public_dict(rec, rs)}), 201


@bp.route("/<user_id>", methods=["GET"])
@login_required
def get_user(user_id: str):
    """单用户详情。"""
    if parse_user_id(user_id) is None:
        return _bad_user_id()
    us = user_service()
    rs = role_service()
    rec = us.get_by_id(user_id)
    if not rec:
        return jsonify({"error": "not_found", "message": "用户不存在"}), 404
    return jsonify({"user": user_public_dict(rec, rs)})


@bp.route("/<user_id>", methods=["PATCH"])
@login_required
def patch_user(user_id: str):
    """更新密码和/或角色列表。"""
    if parse_user_id(user_id) is None:
        return _bad_user_id()
    data = request.get_json(silent=True) or {}
    password = data.get("password")
    role_ids_raw = data.get("role_ids")

    us = user_service()
    rs = role_service()

    if role_ids_raw is not None:
        try:
            role_ids = _parse_role_ids(data)
        except ValueError as e:
            return jsonify({"error": "invalid_request", "message": str(e)}), 400
        for rid in role_ids:
            if not rs.get_by_id(rid):
                return jsonify({"error": "invalid_role", "message": f"角色不存在: {rid}"}), 400
    else:
        role_ids = None

    if password is None and role_ids is None:
        return jsonify({"error": "invalid_request", "message": "无有效更新字段"}), 400

    rec = us.update(user_id, password=password, role_ids=role_ids)
    if not rec:
        return jsonify({"error": "not_found", "message": "用户不存在"}), 404
    return jsonify({"user": user_public_dict(rec, rs)})


@bp.route("/<user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id: str):
    """删除用户；禁止删除当前登录用户（避免锁死会话）。"""
    if parse_user_id(user_id) is None:
        return _bad_user_id()
    cur = parse_user_id(current_user.get_id())
    tgt = parse_user_id(user_id)
    if cur is not None and tgt is not None and cur == tgt:
        return jsonify({"error": "invalid_request", "message": "不能删除当前登录用户"}), 400
    us = user_service()
    if not us.delete(user_id):
        return jsonify({"error": "not_found", "message": "用户不存在"}), 404
    return jsonify({"ok": True})
