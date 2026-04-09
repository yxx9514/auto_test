"""
================================================================================
联调用例：关键字驱动 + 真实请求本地 test_platform 服务
================================================================================

为什么单独一个文件？
--------------------
- 示例关键字用例依赖 **responses** mock，不能发真实登录 Cookie。
- 本文件使用 ``keyword_ctx_live``（见 ``tests/keyword/conftest.py``）：**不启用** ``RequestsMock``，
  请求会真正发到 ``configs/test_platform.yaml`` 里的 ``api.base_url``（默认 ``http://127.0.0.1:5000``）。

前置条件
--------
1. MySQL 可用，Flask 测试平台已初始化库表与种子数据。
2. 已启动::

       cd test_platform && python run.py

3. 种子账号 ``admin`` / ``admin123`` 可登录。

执行::

    pytest tests/keyword/test_test_platform_keyword_cases.py -v

或使用标记::

    pytest -m test_platform -v

用例数据文件：``data/test_platform_keyword_cases.yaml``（关键字覆盖「新增用户」：成功、未登录 401、
重名 409、非法角色 400、缺密码 400）。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from framework.keywords.engine import run_steps


def _load_cases():
    """加载联调专用 YAML 中的 case 列表。"""
    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((root / "data" / "test_platform_keyword_cases.yaml").read_text(encoding="utf-8"))
    return data["cases"]


@pytest.mark.test_platform
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["name"])
def test_test_platform_keyword_case(keyword_ctx_live, case):
    """
    与 ``test_keyword_case`` 结构相同，仅 fixture 换为 ``keyword_ctx_live``。

    注意：服务未启动时会连接失败，属 **环境类失败**，需先起 test_platform。
    """
    run_steps(keyword_ctx_live, case["steps"])
