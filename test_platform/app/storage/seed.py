"""
JSON 存储模式的种子数据（与早期无数据库版本配套）。

流程
----
若 ``roles.json`` / ``users.json`` 不存在，则写入默认角色与 ``admin`` 用户。

**注意**：当前应用默认使用 MySQL，种子逻辑在 ``app/db_seed.py``；本模块仅保留供参考或自行脚本调用。
"""

from __future__ import annotations

from pathlib import Path

from werkzeug.security import generate_password_hash

from ..models.role import Role
from ..models.user import UserRecord
from .json_store import JsonListStore


def ensure_seed(store_dir: Path) -> None:
    """
    在 ``store_dir`` 下初始化 ``roles.json``、``users.json``（若不存在）。

    :param store_dir: 例如 ``instance/store``。
    """
    roles_path = store_dir / "roles.json"
    users_path = store_dir / "users.json"

    store_dir.mkdir(parents=True, exist_ok=True)

    if not roles_path.exists():
        default_roles = [
            Role(id="role_admin", name="admin", kind="system"),
            Role(id="role_pm", name="PM", kind="business"),
            Role(id="role_tse", name="TSE", kind="business"),
            Role(id="role_qa", name="测试", kind="business"),
            Role(id="role_dev", name="开发", kind="business"),
        ]
        rstore = JsonListStore(
            roles_path,
            "roles",
            Role.from_dict,
            lambda r: r.to_dict(),
        )
        for r in default_roles:
            rstore.upsert(r)

    if not users_path.exists():
        # 与 MySQL 版一致：管理员使用数字 id（JSON 演示用固定为 1）
        admin = UserRecord(
            id=1,
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role_ids=["role_admin"],
        )
        ustore = JsonListStore(
            users_path,
            "users",
            UserRecord.from_dict,
            lambda u: u.to_dict(),
        )
        ustore.upsert(admin)
