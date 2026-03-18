 ## 自动化测试项目（API + UI）
 
 目标：一套项目同时支持 **API 自动化** 与 **UI 自动化**，并集成 **pytest + allure**，具备 **数据驱动**、**关键字封装**、**PO(Page Object) 模式** 等能力。
 
 ### 目录结构
 
 - `configs/`: 环境与运行配置（YAML）
 - `data/`: 数据驱动与关键字用例数据（YAML/CSV/JSON 都可扩展）
 - `framework/`
   - `core/`: 配置、日志、通用工具
   - `api/`: HTTP Client 与 API 关键字
   - `ui/`: UI 运行与截图/附件（Playwright 可选）
   - `keywords/`: 关键字引擎（读 YAML 步骤 -> 执行动作）
 - `pages/`: PO 模式页面对象
 - `tests/`
   - `api/`: API 示例用例（使用 `responses` 离线 mock）
   - `ui/`: UI 示例用例（默认跳过；安装 UI 依赖后可跑）
   - `keyword/`: 关键字驱动示例（从 `data/keyword_cases.yaml` 读步骤）
 
 ### 安装
 
 在项目根目录的 `autotest/` 下执行：
 
 ```bash
 python -m venv .venv
 .\.venv\Scripts\activate
 pip install -U pip
 pip install -e .
 ```
 
 如需 UI 自动化（Playwright）：
 
 ```bash
 pip install -e ".[ui]"
 playwright install
 ```
 
 ### 运行
 
 ```bash
 pytest
 ```
 
 生成 Allure 报告：
 
 ```bash
 allure serve allure-results
 ```
 
 ### 常用命令
 
 - 仅跑 API：`pytest -m api`
 - 仅跑 UI：`pytest -m ui`
 - 仅跑关键字：`pytest -m keyword`
 
