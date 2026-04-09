from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_payload_templates(directory: Path) -> dict[str, Any]:
    """
    读取目录下所有 ``*.yaml`` / ``*.yml``，根节点必须为 mapping；同名 key **后加载的文件覆盖先加载的**。

    大体积请求体按业务拆成多个文件（如 ``users.yaml``、``orders.yaml``）放在此目录，用例里用
    ``json_template`` + ``json_patch`` 只写差异字段即可。
    """

    if not directory.is_dir():
        return {}
    paths = sorted({*directory.glob("*.yaml"), *directory.glob("*.yml")})
    merged: dict[str, Any] = {}
    for path in paths:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if raw is None:
            continue
        if not isinstance(raw, dict):
            raise ValueError(f"Payload template root must be a mapping, got {type(raw)}: {path}")
        merged.update(raw)
    return merged
