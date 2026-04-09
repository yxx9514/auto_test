"""
================================================================================
API 自动化示例：数据驱动 + HTTP Mock（responses）
================================================================================

学习目标
--------
1. **数据与代码分离**：用例数据放在 ``data/user_data.yaml``，同一套断言逻辑跑多组输入。
2. **pytest.mark.parametrize**：把列表/可迭代对象展开成多条独立用例，报告中每条有独立结果。
3. **responses 库**：不发起真实网络请求，避免依赖外部服务、提高稳定性（契约/接口形态测试）。

执行方式（在 ``autotest`` 包根目录或已配置 PYTHONPATH 时）::

    pytest tests/api/test_user_api.py -v

标记 ``@pytest.mark.api`` 可与 ``pytest -m api`` 只跑 API 类用例。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


def _load_users():
    """
    从 YAML 读取 ``users`` 列表。

    使用 ``Path(__file__).resolve().parents[2]`` 定位 ``autotest/``：
    - ``parents[0]`` = tests/api
    - ``parents[1]`` = tests
    - ``parents[2]`` = autotest（项目内框架根）

    这样无论从仓库根目录还是 autotest 目录执行 pytest，都能找到 ``data/user_data.yaml``。
    """
    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((root / "data" / "user_data.yaml").read_text(encoding="utf-8"))
    return data["users"]


@pytest.mark.api
@pytest.mark.parametrize("user", _load_users())
def test_get_user_data_driven(http_client, responses_mock, user):
    """
    对每组 ``user`` 数据：注册 GET mock，再断言 HttpClient 解析结果正确。

    参数由 pytest 注入：
    - ``http_client``：根 conftest 提供的会话级客户端（见 ``tests/conftest.py``）。
    - ``responses_mock``：函数级 fixture，本用例内注册的 mock 仅对本用例有效。
    - ``user``：parametrize 注入的一行数据（dict）。

    ``responses_mock.add(...)``：
    - 当 ``requests``（被 HttpClient 内部使用）请求匹配 ``url`` 时，直接返回 ``body``，不访问公网。
    - ``content_type=application/json`` 与 ``json.dumps`` 配合，模拟 REST API。
    """
    url = f"https://api.local/users/{user['id']}"
    responses_mock.add(
        method="GET",
        url=url,
        body=json.dumps(user, ensure_ascii=False),
        status=200,
        content_type="application/json",
    )

    resp = http_client.get(url)
    assert resp.status_code == 200
    assert resp.json()["name"] == user["name"]
