from __future__ import annotations

"""
配置加载模块。

目标：把 YAML 配置文件（`configs/config.yaml`）转成强类型对象，后续在测试/框架里使用时更直观。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ApiConfig:
    """API 相关配置。"""

    base_url: str
    timeout: int = 10


@dataclass(frozen=True)
class UiConfig:
    """UI 相关配置（Playwright）。"""

    base_url: str
    browser: str = "chromium"
    headless: bool = True
    timeout_ms: int = 15000


@dataclass(frozen=True)
class Settings:
    """项目全局配置入口。"""

    env: str
    api: ApiConfig
    ui: UiConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    """读取 YAML 并确保顶层是 dict。"""

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping, got: {type(data)}")
    return data


def load_settings(config_path: str | Path | None = None) -> Settings:
    """
    加载配置。

    - **默认**：读取 `autotest/configs/config.yaml`
    - **覆盖**：通过环境变量 `AUTOTEST_CONFIG` 或传入 `config_path` 指定另一个 YAML

    初学者常见用法：

    1) 你只想改 base_url：
       - 直接编辑 `configs/config.yaml` 的 `api.base_url`

    2) 你有多套环境（dev/test/prod）：
       - 复制出 `configs/test.yaml`
       - 运行时设置 `AUTOTEST_CONFIG` 指向它（见 `tests/conftest.py` 的注释）
    """

    root = Path(__file__).resolve().parents[2]  # autotest/
    cfg = Path(config_path) if config_path else (root / "configs" / "config.yaml")
    data = _read_yaml(cfg)

    api = data.get("api") or {}
    ui = data.get("ui") or {}

    return Settings(
        env=str(data.get("env") or "local"),
        api=ApiConfig(
            base_url=str(api.get("base_url") or ""),
            timeout=int(api.get("timeout") or 10),
        ),
        ui=UiConfig(
            base_url=str(ui.get("base_url") or ""),
            browser=str(ui.get("browser") or "chromium"),
            headless=bool(ui.get("headless", True)),
            timeout_ms=int(ui.get("timeout_ms") or 15000),
        ),
    )

