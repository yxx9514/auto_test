# 测试平台（test_platform）说明

面向 **测试工程师自学自动化 / 测试平台开发** 的说明文档：项目做什么、用到哪些库、如何运行、如何调试与扩展。

---

## 1. 项目是做什么的？

这是一个用 **Python + Flask** 搭建的 **测试管理后台 API**（当前阶段以 REST 为主，无独立前端页面），提供：

- **用户**：登录、用户 CRUD（数字 id，1～999999）
- **角色**：角色列表、新增、删除；用户与角色多对多
- **用例**：测试用例 CRUD（数字 id，1～999999）

数据保存在 **MySQL**；鉴权使用 **Flask-Login 会话 Cookie**（登录后浏览器/Postman 携带 `session`）。

---

## 2. 技术栈与各库职责（建议对照源码学习）

| 库 | 作用（在本项目里） |
|----|-------------------|
| **Flask** | Web 框架：路由、请求/响应、`jsonify`、`request`、`Blueprint` 拆分模块。 |
| **Flask-Login** | 登录态：`login_user` / `logout_user`、`@login_required`、`current_user`、`user_loader` 从会话恢复用户。 |
| **Flask-SQLAlchemy** | 把 **SQLAlchemy** 接入 Flask：`db = SQLAlchemy()`、`db.init_app(app)`、`db.Model`、`db.session`。 |
| **SQLAlchemy 2.x** | ORM + 数据库会话：`select()`、`session.get()`、`session.scalars()`、`session.commit()`。 |
| **PyMySQL** | 纯 Python 的 MySQL 驱动；连接串里写作 `mysql+pymysql://...`（由 SQLAlchemy 使用）。 |
| **cryptography** | MySQL 8 默认 `caching_sha2_password` 时，PyMySQL 需要它做加密握手；缺了会报需要 cryptography。 |
| **Werkzeug** | Flask 自带依赖：`generate_password_hash` / `check_password_hash` 做密码哈希，**禁止明文存库**。 |
| **urllib.parse.quote_plus** | 拼数据库 URL 时对用户名、密码里的特殊字符做 URL 编码。 |

**标准库**：`os`（环境变量）、`pathlib`（路径）、`datetime`（用例执行时间）、`typing`（类型注解）、`dataclasses`（领域小对象，与 ORM 分离）。

---

## 3. 目录结构（读代码从这里开始）

```
test_platform/
├── README.md                 # 本说明
├── requirements.txt          # pip 依赖
├── run.py                    # 开发启动入口
├── openapi/
│   └── test-platform.openapi.yaml   # 可导入 Postman 的 OpenAPI 描述
└── app/
    ├── __init__.py           # create_app：建库、建表、种子、注册蓝图、Flask-Login
    ├── config.py             # 配置类与环境变量
    ├── extensions.py         # db、LoginManager 单例
    ├── auth_user.py          # Flask-Login 用的 UserMixin 实现
    ├── ids.py                # 用户/用例 id 解析（1～999999）
    ├── converters.py         # ORM ↔ 领域对象、executed_at 解析
    ├── serializers.py        # 对外 JSON 形状（如隐藏密码）
    ├── deps.py               # 简易服务工厂（给路由用）
    ├── db_bootstrap.py       # 用 PyMySQL 建库（若不存在）
    ├── db_seed.py            # 首次空表时写入角色/admin/示例用例
    ├── orm_models.py         # SQLAlchemy 表模型
    ├── models/               # 与 API/业务相关的 dataclass（非 ORM）
    ├── routes/               # 蓝图：auth / users / roles / cases
    ├── services/             # 业务逻辑 + db.session 操作
    └── storage/              # 历史 JSON 存储实现（当前主流程已用 MySQL，可忽略或作参考）
```

---

## 4. 环境准备

1. **Python 3.10+**（与团队约定一致即可）。
2. **MySQL 5.7+ / 8.x**，服务已启动，能使用你配置的账号创建库。
3. 在项目下安装依赖：

```bash
cd test_platform
pip install -r requirements.txt
```

---

## 5. 配置与环境变量

默认配置在 `app/config.py` 的 `Config` 类中，可通过 **环境变量** 覆盖（适合不同机器、不把密码写进仓库）：

| 变量 | 含义 |
|------|------|
| `MYSQL_HOST` | 默认 `127.0.0.1` |
| `MYSQL_PORT` | 默认 `3306` |
| `MYSQL_USER` | 默认 `root` |
| `MYSQL_PASSWORD` | 默认以 `config.py` 为准，**生产务必改** |
| `MYSQL_DATABASE` | 默认 `PythonProject2`（与项目名一致） |
| `TEST_PLATFORM_DATABASE_URI` | 若设置，则**整段**覆盖 SQLAlchemy 连接串 |
| `TEST_PLATFORM_SECRET_KEY` | Flask 会话签名密钥，**生产必须改** |

连接串格式示例：

`mysql+pymysql://用户:密码@主机:端口/库名?charset=utf8mb4`

---

## 6. 启动与首次运行

```bash
cd test_platform
python run.py
```

默认监听 `0.0.0.0:5000`。启动时会：

1. `ensure_database_exists`：若库不存在则 `CREATE DATABASE`（utf8mb4）。
2. `db.create_all()`：按 `orm_models.py` 建表。
3. `seed_if_empty`：若表为空，写入角色、管理员、示例用例。

**默认管理员**（种子数据）：用户名 `admin`，密码 `admin123`（仅用于学习/开发，上线前请改）。

---

## 7. API 与 Postman

- OpenAPI 文件：`openapi/test-platform.openapi.yaml`  
- Post：**Import → 选择该文件**。  
- 除 `GET /api/v1/ping` 与 `POST /api/v1/auth/login` 外，需先登录，并携带 **Cookie `session`**。

**用例接口注意**：`executed_at` 必须是 **ISO8601** 合法字符串，或 **不传 / null**。Postman 里不要用占位符 `"string"`，否则会返回 400。

---

## 8. 与仓库内 autotest 联调（关键字用例）

测试平台启动后，可在仓库的 `autotest` 中运行：

```bash
pytest tests/keyword/test_test_platform_keyword_cases.py -v
```

详见 `autotest/configs/test_platform.yaml` 与对应用例 YAML。需 autotest 虚拟环境安装齐全依赖（`responses`、`allure-pytest` 等）。

---

## 9. 常见问题

| 现象 | 可能原因 |
|------|----------|
| 需要 `cryptography` | MySQL 8 认证插件；`pip install cryptography`。 |
| 无法连接数据库 | 服务未起、端口/密码错误、防火墙。 |
| 改表结构后报错 | `create_all` 不会自动改已有表；开发期可 `DROP TABLE` 后重启，生产用迁移工具（如 Alembic）。 |
| 401 | 未登录或 Cookie 未带上。 |
| 用户/用例 id 400 | id 必须是 **1～999999** 的整数。 |

---

## 10. 扩展学习建议

- Flask 官方文档：应用工厂、`Blueprint`、配置。  
- Flask-Login：会话与 `user_loader`。  
- SQLAlchemy 2.0 教程：`Session`、`select`、关系 `relationship` / `secondary`。  
- 下一步可接：**Alembic 迁移**、**JWT**、**按角色鉴权**、**任务队列执行自动化用例**。

---

## 11. 源码中的注释约定

各 `.py` 文件内补充了 **模块说明**、**类/函数 docstring**，说明职责、参数、返回值及用到的关键 API。建议按「`README` → `app/__init__.py` → `routes` → `services` → `orm_models`」顺序阅读。
