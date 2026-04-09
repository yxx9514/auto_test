from __future__ import annotations

"""
关键字引擎（Keyword Engine）。

它做两件事：
- **变量解析**：把 args 里的 `${var}` 或 `${var.attr}` 解析成真实值
- **执行步骤**：根据 `keyword` 找到对应函数执行，并支持 `save_as` 保存结果

示例步骤（来自 `data/keyword_cases.yaml`）：

    - keyword: api_get
      args:
        url: "https://api.local/users/1"
      save_as: resp
    - keyword: assert_json_path
      args:
        data_ref: "${resp.json}"
        path: "name"
        expected: "alice"

初学者记住 3 句话就够了：

1) YAML 里每一步都有一个 `keyword`（关键字名字）
2) Python 里有一个同名函数去执行这个动作（在 `ctx.registry` 里注册）
3) 上一步的结果可以用 `save_as` 存起来，下一步用 `${变量名}` 取出来

大请求体可放在 ``data/payload_templates/*.yaml``，在 ``api_post`` 的 args 里用 ``json_template`` +
``json_patch``（补丁里同样支持 ``${}``）；与 ``json`` 二选一。也可用关键字 ``json_from_template`` 生成 body 再 ``save_as``。
"""

import re
from typing import Any

from ..core.jsonpath import get_path
from .context import KeywordContext

_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _eval_ref(ctx: KeywordContext, expr: str) -> Any:
    """
    Supported:
    - var: "${resp}"
    - var.attr: "${resp.status_code}"
    - var.json: "${resp.json}" -> call .json() if callable
    - var.json.path: "${resp.json.name}" -> json() then get_path
    """

    # expr 是 `${...}` 里面的内容，比如 "resp.json.name"
    # 我们把它按 "." 切开，一段一段地往下取值。
    parts = expr.split(".")
    base = parts[0]
    if base not in ctx.variables:
        raise KeyError(f"Unknown variable: {base}")
    cur: Any = ctx.variables[base]

    for part in parts[1:]:
        # 约定：如果遇到 json，就调用对象的 json() 方法（requests/我们的 ApiResponse 都有这个习惯）
        if part == "json" and hasattr(cur, "json"):
            j = getattr(cur, "json")
            cur = j() if callable(j) else j
            continue

        # 如果当前是 dict/list，就用我们自己的 get_path 再往下取
        if isinstance(cur, (dict, list)):
            cur = get_path(cur, part)
        else:
            # 否则当作普通对象属性读取，例如 resp.status_code
            cur = getattr(cur, part)
    return cur


def resolve_value(ctx: KeywordContext, value: Any) -> Any:
    """
    递归解析 value 中的变量引用。

    - str：支持 `${...}`；如果整段字符串就是变量表达式，则返回原类型（不是 str）
    - dict/list：递归处理
    """

    if isinstance(value, str):
        # 例子1：value = "hello" -> 没有变量，原样返回
        # 例子2：value = "${resp.status_code}" -> 返回 int（不是字符串）
        # 例子3：value = "id=${user_id}" -> 做字符串替换，返回 str
        matches = list(_VAR_PATTERN.finditer(value))
        if not matches:
            return value
        if len(matches) == 1 and matches[0].span() == (0, len(value)):
            return _eval_ref(ctx, matches[0].group(1))

        def repl(m: re.Match[str]) -> str:
            v = _eval_ref(ctx, m.group(1))
            return str(v)

        return _VAR_PATTERN.sub(repl, value)

    if isinstance(value, list):
        # list 里每个元素都递归处理
        return [resolve_value(ctx, v) for v in value]

    if isinstance(value, dict):
        # dict 的每个 value 都递归处理
        return {k: resolve_value(ctx, v) for k, v in value.items()}

    return value


def run_steps(ctx: KeywordContext, steps: list[dict[str, Any]]) -> None:
    """按顺序执行步骤列表（一个 case 的 steps）。"""

    for i, step in enumerate(steps, start=1):
        keyword = step.get("keyword")
        if not keyword:
            raise ValueError(f"Step {i} missing keyword")
        if keyword not in ctx.registry:
            raise KeyError(f"Unknown keyword: {keyword}")

        raw_args = step.get("args") or {}
        if not isinstance(raw_args, dict):
            raise ValueError(f"Step {i} args must be dict")

        # 先把 args 里的 `${...}` 全部解析掉，得到真正的入参
        args = resolve_value(ctx, raw_args)

        # 执行关键字函数（动作）
        result = ctx.registry[keyword](ctx, args)

        save_as = step.get("save_as")
        if save_as:
            # 把结果存到变量表：下一步就能用 `${变量名}` 引用它
            ctx.variables[str(save_as)] = result

