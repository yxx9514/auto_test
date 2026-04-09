"""
历史实现：基于 JSON 文件的简易存储。

当前主流程已改为 **MySQL + SQLAlchemy**，本包保留作学习参考或离线演示；``create_app`` 不再调用 ``ensure_seed``。
"""

from __future__ import annotations

from .json_store import JsonListStore

__all__ = ["JsonListStore"]
