"""
测试用例 CRUD 路由。

字段与校验
----------
- ``executed_at`` 经 ``converters.parse_executed_at`` 解析；非法字符串由服务/转换层抛 ``ValueError``，此处转 **400**。
- ``_opt_str``：键不存在返回 ``None``（表示不更新）；键存在但空串可转为 ``None``，便于清空可选字段（按业务调整）。

辅助函数 ``_str_field`` / ``_opt_str``
--------------------------------------
减少重复的 ``get`` + 类型转换逻辑，保持视图层可读。
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import login_required

from ..deps import case_service
from ..ids import parse_case_id

bp = Blueprint("cases", __name__)


def _bad_case_id():
    """路径参数 case_id 非法时的统一 400 响应。"""
    return (
        jsonify(
            {
                "error": "invalid_request",
                "message": "用例 id 须为 1～999999 之间的整数（最多 6 位）",
            }
        ),
        400,
    )


def _str_field(data: dict, key: str, default: str = "") -> str:
    """取字段并转 str；``None`` 用 ``default``。"""
    v = data.get(key)
    if v is None:
        return default
    return str(v)


def _opt_str(data: dict, key: str) -> str | None:
    """
    可选字符串：键缺失返回 ``None``；键存在且空串也返回 ``None``。

    用于区分「未传字段」与「传了空」——创建用例时与 ``CaseService`` 约定一致即可。
    """
    if key not in data:
        return None
    v = data.get(key)
    if v is None:
        return None
    return str(v) if str(v) != "" else None


@bp.route("", methods=["GET"])
@login_required
def list_cases():
    """用例列表。"""
    cs = case_service()
    return jsonify({"cases": [c.to_dict() for c in cs.list_cases()]})


@bp.route("", methods=["POST"])
@login_required
def create_case():
    """创建用例；``name`` 必填。"""
    data = request.get_json(silent=True) or {}
    name = _str_field(data, "name").strip()
    if not name:
        return jsonify({"error": "invalid_request", "message": "name 必填"}), 400
    cs = case_service()
    try:
        tc = cs.create(
            name=name,
            module=_str_field(data, "module").strip(),
            level=_str_field(data, "level").strip(),
            pre_steps=_str_field(data, "pre_steps"),
            steps=_str_field(data, "steps"),
            expected_result=_str_field(data, "expected_result"),
            actual_result=_opt_str(data, "actual_result"),
            executor=_opt_str(data, "executor"),
            executed_at=_opt_str(data, "executed_at"),
        )
    except ValueError as e:
        return jsonify({"error": "invalid_request", "message": str(e)}), 400
    return jsonify({"case": tc.to_dict()}), 201


@bp.route("/<case_id>", methods=["GET"])
@login_required
def get_case(case_id: str):
    """单条用例详情。"""
    if parse_case_id(case_id) is None:
        return _bad_case_id()
    cs = case_service()
    tc = cs.get_by_id(case_id)
    if not tc:
        return jsonify({"error": "not_found", "message": "用例不存在"}), 404
    return jsonify({"case": tc.to_dict()})


@bp.route("/<case_id>", methods=["PATCH"])
@login_required
def patch_case(case_id: str):
    """部分更新；仅处理 JSON 中出现的键。"""
    if parse_case_id(case_id) is None:
        return _bad_case_id()
    data = request.get_json(silent=True) or {}
    cs = case_service()
    if not cs.get_by_id(case_id):
        return jsonify({"error": "not_found", "message": "用例不存在"}), 404

    upd: dict[str, object] = {}
    if "name" in data:
        n = _str_field(data, "name").strip()
        if not n:
            return jsonify({"error": "invalid_request", "message": "name 不能为空"}), 400
        upd["name"] = n
    if "module" in data:
        upd["module"] = _str_field(data, "module").strip()
    if "level" in data:
        upd["level"] = _str_field(data, "level").strip()
    if "pre_steps" in data:
        upd["pre_steps"] = _str_field(data, "pre_steps")
    if "steps" in data:
        upd["steps"] = _str_field(data, "steps")
    if "expected_result" in data:
        upd["expected_result"] = _str_field(data, "expected_result")
    if "actual_result" in data:
        upd["actual_result"] = data.get("actual_result")
    if "executor" in data:
        upd["executor"] = data.get("executor")
    if "executed_at" in data:
        upd["executed_at"] = data.get("executed_at")

    if not upd:
        return jsonify({"error": "invalid_request", "message": "无有效更新字段"}), 400

    try:
        tc = cs.update(case_id, **upd)
    except ValueError as e:
        return jsonify({"error": "invalid_request", "message": str(e)}), 400
    return jsonify({"case": tc.to_dict() if tc else None})


@bp.route("/<case_id>", methods=["DELETE"])
@login_required
def delete_case(case_id: str):
    """删除用例。"""
    if parse_case_id(case_id) is None:
        return _bad_case_id()
    cs = case_service()
    if not cs.delete(case_id):
        return jsonify({"error": "not_found", "message": "用例不存在"}), 404
    return jsonify({"ok": True})
