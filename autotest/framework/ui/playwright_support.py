from __future__ import annotations

from typing import Any


def playwright_available() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except Exception:
        return False


def safe_page_screenshot(page: Any) -> bytes | None:
    try:
        return page.screenshot(full_page=True)
    except Exception:
        return None

