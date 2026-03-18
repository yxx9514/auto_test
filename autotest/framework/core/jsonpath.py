from __future__ import annotations

from typing import Any


def get_path(data: Any, path: str) -> Any:
    """
    Minimal "json-path like" getter.

    Supported:
    - "a.b.c"
    - "items.0.name"
    """
    if path == "" or path is None:
        return data
    cur: Any = data
    for part in str(path).split("."):
        if isinstance(cur, list):
            idx = int(part)
            cur = cur[idx]
        elif isinstance(cur, dict):
            cur = cur[part]
        else:
            raise KeyError(f"Cannot access '{part}' on {type(cur)}")
    return cur

