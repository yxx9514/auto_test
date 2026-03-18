from __future__ import annotations

"""
PO（Page Object）模式基类。

核心思想：
- 测试用例只描述“业务行为”（打开页面、点击、输入、断言）
- 页面细节（选择器、页面跳转、组件操作）放在 Page 类中集中管理
"""

from typing import Any


class BasePage:
    """所有 Page 的基类，封装常用导航能力。"""

    def __init__(self, page: Any, base_url: str = "") -> None:
        # page 是 Playwright 提供的对象，你可以理解成“浏览器里的当前标签页”
        self.page = page
        # base_url 是你系统的访问入口，比如：
        # - 测试环境：https://test.example.com
        # - 生产环境：https://www.example.com
        self.base_url = base_url.rstrip("/")

    def goto(self, path: str) -> None:
        """
        统一的跳转方法：
        - 传绝对 URL：直接打开
        - 传相对路径：自动拼接 base_url（更利于多环境切换）
        """

        # 初学者提示：如果你的项目有多个系统模块，推荐传相对路径：
        #   self.goto("/login")
        # 然后通过切换 base_url 达到切换环境的目的。
        if path.startswith("http://") or path.startswith("https://"):
            self.page.goto(path)
            return
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
        self.page.goto(url)

