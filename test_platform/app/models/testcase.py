"""
测试用例领域对象。

``executed_at`` 在 API 中为 **字符串**（ISO8601）；在 ORM 中为 ``datetime``；由 ``converters.testcase_model_to_case`` 统一转换。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class TestCase:
    """
    平台管理的用例字段（与产品需求文档字段对齐）。

    :ivar id: 自增整型主键。
    :ivar module: 功能模块名称。
    :ivar level: 用例等级（如 P0/P1）。
    :ivar pre_steps / steps: 前置与执行步骤（文本）。
    :ivar expected_result / actual_result: 预期与实际结果。
    :ivar executor: 执行人标识（可为用户名或工号，由业务约定）。
    :ivar executed_at: 最近一次执行时间字符串；未执行为 ``None``。
    """

    id: int
    name: str
    module: str
    level: str
    pre_steps: str
    steps: str
    expected_result: str
    actual_result: str | None
    executor: str | None
    executed_at: str | None

    def to_dict(self) -> dict[str, Any]:
        """供 ``jsonify`` 使用。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestCase:
        """从 dict 构造（导入或缓存场景）。"""
        return cls(
            id=int(data["id"]),
            name=str(data.get("name") or ""),
            module=str(data.get("module") or ""),
            level=str(data.get("level") or ""),
            pre_steps=str(data.get("pre_steps") or ""),
            steps=str(data.get("steps") or ""),
            expected_result=str(data.get("expected_result") or ""),
            actual_result=data.get("actual_result") if data.get("actual_result") is not None else None,
            executor=data.get("executor") if data.get("executor") is not None else None,
            executed_at=data.get("executed_at") if data.get("executed_at") is not None else None,
        )
