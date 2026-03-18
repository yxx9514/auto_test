from __future__ import annotations

"""
关键字驱动示例。

这个用例演示：
- 用例步骤写在 `data/keyword_cases.yaml`
- pytest 负责参数化 case
- `run_steps()` 负责按步骤执行关键字
"""

from pathlib import Path

import pytest
import yaml

from framework.keywords.engine import run_steps


def _load_cases():
    # 同样用“以文件定位根目录”的方式，避免用户从不同目录运行时读不到数据文件
    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((root / "data" / "keyword_cases.yaml").read_text(encoding="utf-8"))
    return data["cases"]


@pytest.mark.keyword
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["name"])
def test_keyword_case(keyword_ctx, case):
    run_steps(keyword_ctx, case["steps"])

