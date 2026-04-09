from __future__ import annotations

import copy
from typing import Any


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """
    深度合并两个字典：patch 覆盖 base；子 dict 递归合并；list 等非 dict 值整段替换。
    """

    out = copy.deepcopy(base)
    for key, val in patch.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out
