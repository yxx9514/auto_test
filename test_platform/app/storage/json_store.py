"""
线程安全的 JSON 文件读写（列表根结构）。

标准库用法
----------
- ``json.load`` / ``json.dump``：序列化；``ensure_ascii=False`` 保留中文。
- ``pathlib.Path``：跨平台路径；临时文件 ``.tmp`` 再 ``replace`` 实现 **原子替换**（崩溃时尽量不留下半写入文件）。
- ``threading.RLock``：可重入锁，同一进程多线程下避免读写交错（本服务多为单进程单请求线程，仍属良好习惯）。

泛型 ``TypeVar("T")``
---------------------
``JsonListStore[T]`` 与具体 dataclass 解耦：由调用方传入 ``from_dict`` / ``to_dict`` 两个可调用对象完成类型转换。
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class JsonListStore(Generic[T]):
    """
    将对象列表持久化为 ``{"<key>": [ {...}, ... ]}`` 形式的 JSON 文件。

    :param path: 文件路径。
    :param key: JSON 根对象里数组对应的键名，如 ``"users"``。
    :param from_dict: 把 dict 转回领域对象。
    :param to_dict: 把领域对象转为可 JSON 序列化的 dict。
    """

    def __init__(
        self,
        path: Path,
        key: str,
        from_dict: Callable[[dict[str, Any]], T],
        to_dict: Callable[[T], dict[str, Any]],
    ) -> None:
        self._path = path
        self._key = key
        self._from_dict = from_dict
        self._to_dict = to_dict
        self._lock = threading.RLock()

    def _read_raw(self) -> dict[str, Any]:
        """读整个 JSON 对象；文件不存在视为空列表。"""
        if not self._path.exists():
            return {self._key: []}
        with self._path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_raw(self, data: dict[str, Any]) -> None:
        """写入磁盘（先写临时文件再替换）。"""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self._path)

    def all_items(self) -> list[T]:
        """加载全部项并转为 ``T``。"""
        with self._lock:
            raw = self._read_raw()
            items = raw.get(self._key) or []
            return [self._from_dict(x) for x in items if isinstance(x, dict)]

    def by_id(self, item_id: str) -> T | None:
        """线性查找指定 ``id`` 的项（数据量小可接受）。"""
        for it in self.all_items():
            d = self._to_dict(it)
            if str(d.get("id")) == str(item_id):
                return it
        return None

    def upsert(self, item: T) -> None:
        """存在同 id 则替换，否则追加。"""
        d = self._to_dict(item)
        iid = str(d["id"])
        with self._lock:
            raw = self._read_raw()
            lst = list(raw.get(self._key) or [])
            replaced = False
            out: list[dict[str, Any]] = []
            for x in lst:
                if isinstance(x, dict) and str(x.get("id")) == iid:
                    out.append(d)
                    replaced = True
                else:
                    out.append(x)
            if not replaced:
                out.append(d)
            raw[self._key] = out
            self._write_raw(raw)

    def delete(self, item_id: str) -> bool:
        """按 id 删除；未找到返回 ``False``。"""
        with self._lock:
            raw = self._read_raw()
            lst = list(raw.get(self._key) or [])
            new_lst = [x for x in lst if not (isinstance(x, dict) and str(x.get("id")) == str(item_id))]
            if len(new_lst) == len(lst):
                return False
            raw[self._key] = new_lst
            self._write_raw(raw)
            return True
