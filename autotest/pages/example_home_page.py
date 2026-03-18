from __future__ import annotations

from .base_page import BasePage


class ExampleHomePage(BasePage):
    """示例 Page：用于展示 PO 的写法（打开首页、读取标题）。"""

    def open(self) -> None:
        self.goto("/")

    def title(self) -> str:
        return self.page.title()

