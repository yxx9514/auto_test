"""
测试平台启动入口（开发环境）。

使用方式（在 test_platform 目录下）::

    python run.py

说明：
- **Flask 内置服务器**仅适合本地开发；生产应使用 gunicorn、uwsgi 等 WSGI 容器。
- `app.run(debug=True)` 会开启调试模式（改代码自动重载、浏览器里显示错误栈），**切勿在生产开启**。
- `host="0.0.0.0"` 表示监听所有网卡，便于局域网其它机器访问；仅本机可改为 `127.0.0.1`。
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
