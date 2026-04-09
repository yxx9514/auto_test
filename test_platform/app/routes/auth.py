"""
认证相关路由：登录、登出、当前用户。

Flask-Login 与 Session
----------------------
- ``login_user(user)``：把用户 id 写入 **签名会话**；默认 Cookie 名为 ``session``（可配置）。
- ``logout_user()``：清除会话中的登录信息。
- ``@login_required``：未登录时触发 ``LoginManager.unauthorized_handler``（本项目中返回 JSON 401）。
- ``request.get_json(silent=True)``：解析 ``Content-Type: application/json`` 的请求体；解析失败返回 ``None`` 而不抛异常。

安全说明
--------
密码校验使用 ``werkzeug`` 哈希比对；**从不**在成功响应里返回密码或哈希。
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from ..auth_user import PlatformUser
from ..deps import role_service, user_service
from ..serializers import user_public_dict

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["POST"])
def login_api():
    """
    用户名密码登录；成功则设置会话 Cookie。

    请求体 JSON: ``{"username": "...", "password": "..."}``
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "invalid_request", "message": "请提供用户名和密码"}), 400

    us = user_service()
    rec = us.get_by_username(username)
    if not rec or not us.verify_password(rec, password):
        return jsonify({"error": "invalid_credentials", "message": "用户名或密码错误"}), 401

    login_user(PlatformUser(rec.id, rec.username, rec.role_ids), remember=False)
    rs = role_service()
    return jsonify({"ok": True, "user": user_public_dict(rec, rs)})


@bp.route("/logout", methods=["POST"])
@login_required
def logout_api():
    """登出当前会话。"""
    logout_user()
    return jsonify({"ok": True})


@bp.route("/me", methods=["GET"])
@login_required
def me_api():
    """返回当前登录用户信息（若库中用户已删则 404 并登出）。"""
    us = user_service()
    rs = role_service()
    rec = us.get_by_id(current_user.get_id())
    if not rec:
        logout_user()
        return jsonify({"error": "not_found", "message": "用户不存在"}), 404
    return jsonify({"user": user_public_dict(rec, rs)})
