"""
测试用例领域服务。

``update`` 的 ``**fields``
--------------------------
路由层只应传入允许的白名单字段；服务内再次用 ``allowed`` 集合过滤，防止 Mass Assignment 漏洞（恶意 JSON 写未授权列）。

``executed_at``
---------------
入库前经 ``parse_executed_at``；非法格式抛 ``ValueError``，由路由映射为 400。
"""

from __future__ import annotations

from sqlalchemy import select

from ..converters import parse_executed_at, testcase_model_to_case
from ..extensions import db
from ..ids import parse_case_id
from ..models.testcase import TestCase
from ..orm_models import TestCaseModel


class CaseService:
    """用例相关业务逻辑。"""

    def list_cases(self) -> list[TestCase]:
        """全部用例。"""
        rows = db.session.scalars(select(TestCaseModel)).all()
        return [testcase_model_to_case(m) for m in rows]

    def get_by_id(self, case_id: str | int | None) -> TestCase | None:
        """按整型主键查询；非法 id 返回 ``None``。"""
        cid = parse_case_id(case_id)
        if cid is None:
            return None
        m = db.session.get(TestCaseModel, cid)
        return testcase_model_to_case(m) if m else None

    def create(
        self,
        *,
        name: str,
        module: str,
        level: str,
        pre_steps: str,
        steps: str,
        expected_result: str,
        actual_result: str | None = None,
        executor: str | None = None,
        executed_at: str | None = None,
    ) -> TestCase:
        """新建用例；主键由数据库自增分配。"""
        m = TestCaseModel(
            name=name,
            module=module,
            level=level,
            pre_steps=pre_steps,
            steps=steps,
            expected_result=expected_result,
            actual_result=actual_result,
            executor=executor,
            executed_at=parse_executed_at(executed_at),
        )
        db.session.add(m)
        db.session.commit()
        db.session.refresh(m)
        return testcase_model_to_case(m)

    def update(self, case_id: str | int | None, **fields: object) -> TestCase | None:
        """
        部分更新；``fields`` 中不在白名单的键被忽略。

        :raises ValueError: ``executed_at`` 格式非法。
        """
        cid = parse_case_id(case_id)
        if cid is None:
            return None
        m = db.session.get(TestCaseModel, cid)
        if not m:
            return None
        allowed = {
            "name",
            "module",
            "level",
            "pre_steps",
            "steps",
            "expected_result",
            "actual_result",
            "executor",
            "executed_at",
        }
        for k, v in fields.items():
            if k not in allowed:
                continue
            if k == "executed_at":
                setattr(m, k, parse_executed_at(v))
            else:
                setattr(m, k, v)
        db.session.commit()
        db.session.refresh(m)
        return testcase_model_to_case(m)

    def delete(self, case_id: str | int | None) -> bool:
        """删除用例。"""
        cid = parse_case_id(case_id)
        if cid is None:
            return False
        m = db.session.get(TestCaseModel, cid)
        if not m:
            return False
        db.session.delete(m)
        db.session.commit()
        return True
