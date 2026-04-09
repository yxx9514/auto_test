"""
================================================================================
关键字驱动示例：步骤写在 YAML，由引擎按序执行
================================================================================

与「数据驱动 API 用例」的区别
----------------------------
- 数据驱动：Python 里写 **断言逻辑**，数据来自 YAML/CSV。
- 关键字驱动：步骤（调用哪个关键字、入参、是否 ``save_as``）也在 YAML 里，
  Python 只负责 **加载 case + 调用 run_steps**。

数据文件
--------
默认读取 ``data/keyword_cases.yaml`` 中的 ``cases`` 列表；每个元素含 ``name`` 与 ``steps``。

``@pytest.mark.parametrize(..., ids=lambda c: c["name"])``
----------------------------------------------------------
为每条 case 指定 **用例 ID**（报告显示为可读名称，而不是 ``case0``）。

依赖的 fixture
--------------
``keyword_ctx``：定义在 ``tests/conftest.py``，内含 **responses mock**，
适合示例里 ``api_mock_get`` + ``api_get`` 的离线演示。

执行::

    pytest tests/keyword/test_keyword_cases.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from framework.keywords.engine import run_steps


def _load_cases():
    """加载 ``data/keyword_cases.yaml`` 中所有 case（路径解析方式同 API 用例）。"""
    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((root / "data" / "keyword_cases.yaml").read_text(encoding="utf-8"))
    return data["cases"]


@pytest.mark.keyword
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["name"])
def test_keyword_case(keyword_ctx, case):
    """
    对单个 YAML case：执行其 ``steps`` 列表。

    ``run_steps`` 会逐步解析 ``${变量}``、调用 ``keyword_ctx.registry`` 中注册的关键字函数；
    任一步断言失败则 pytest 记录失败步骤（可结合 Allure 做步骤拆解，属后续扩展）。
    """
    run_steps(keyword_ctx, case["steps"])
