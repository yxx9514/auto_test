from __future__ import annotations

"""
API 数据驱动示例。

这个用例演示：
- 数据来自 `data/user_data.yaml`
- 用 `responses_mock` mock 掉外部 HTTP（离线可运行）
- 用 `pytest.mark.parametrize` 做数据驱动
"""

import json
from pathlib import Path

import pytest
import yaml


def _load_users():
    # 以文件位置为锚点，向上找到 autotest/ 根目录，避免依赖当前工作目录
    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((root / "data" / "user_data.yaml").read_text(encoding="utf-8"))
    return data["users"]


@pytest.mark.api
@pytest.mark.parametrize("user", _load_users())
def test_get_user_data_driven(http_client, responses_mock, user):
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

