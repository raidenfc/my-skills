#!/usr/bin/env python3
"""
generate_msw.py — 从 contract.json 生成 MSW v2.x Handler 和 Mock 数据
增强版：包含参数校验、延迟模拟、Token 校验、分页逻辑
"""
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从契约生成 MSW Mock 文件")
    parser.add_argument("--contract", required=True, help="contract.json 路径")
    parser.add_argument("--output-root", required=True, help="输出根目录")
    return parser.parse_args()


def to_msw_path(path: str) -> str:
    """将 {id} 转为 :id（MSW 路由格式）"""
    return re.sub(r"\{([^{}]+)\}", r":\1", path)


def safe_var_name(s: str) -> str:
    """生成安全的 JS 变量名"""
    return re.sub(r"[^a-zA-Z0-9_]", "_", s).strip("_")


def module_file_name(module: str) -> str:
    """模块名转文件名"""
    return re.sub(r"[^a-zA-Z0-9]", "-", module).lower()


def group_by_module(endpoints: List[Dict]) -> Dict[str, List[Dict]]:
    """按模块分组"""
    groups: Dict[str, List[Dict]] = {}
    for ep in endpoints:
        module = ep.get("module", "default")
        groups.setdefault(module, []).append(ep)
    return groups


def needs_auth(ep: Dict) -> bool:
    """判断接口是否需要认证"""
    for h in ep.get("headers", []):
        if h.get("name") == "Authorization":
            return True
    return False


def is_paginated(ep: Dict) -> bool:
    """判断是否为分页接口"""
    query_names = {q.get("name") for q in ep.get("query", [])}
    return "page" in query_names or "pageSize" in query_names


def generate_handler_code(ep: Dict) -> str:
    """生成单个接口的 handler 代码"""
    method = ep.get("method", "GET").lower()
    path = to_msw_path(ep.get("path", "/"))
    endpoint_name = ep.get("endpoint", "unknown")
    strategy = ep.get("mockStrategy", "success")

    # 提取响应示例
    success_example = {}
    for r in ep.get("responses", []):
        if str(r.get("status", "")).startswith("2"):
            success_example = r.get("example", {"code": 200, "data": {}, "message": "success"})
            break

    error_example = {"code": 400, "data": None, "message": "请求参数错误"}
    for e in ep.get("errors", []):
        error_example = e.get("example", error_example)
        break

    lines = []
    lines.append(f"  // {ep.get('method', 'GET')} {ep.get('path', '/')} — {endpoint_name}")

    # 构建 handler 参数
    handler_params = []
    if ep.get("pathParams"):
        handler_params.append("params")
    if method in ("post", "put", "patch"):
        handler_params.append("request")
    elif needs_auth(ep):
        handler_params.append("request")
    elif is_paginated(ep):
        # 分页接口需要读取 request.url 中的 query 参数
        handler_params.append("request")

    params_str = ", ".join(handler_params)
    if handler_params:
        is_async = method in ("post", "put", "patch")
        async_prefix = "async " if is_async else ""
        lines.append(f"  http.{method}('{path}', {async_prefix}({{ {params_str} }}) => {{")
    else:
        is_async = method in ("post", "put", "patch")
        async_prefix = "async " if is_async else ""
        lines.append(f"  http.{method}('{path}', {async_prefix}() => {{")

    # 延迟模拟
    if method in ("post", "put", "patch"):
        lines.append("    await delay(300)")
        lines.append("")

    # Token 校验
    if needs_auth(ep) and "request" in params_str:
        lines.append("    // 认证校验")
        lines.append("    const authHeader = request.headers.get('Authorization')")
        lines.append("    if (!authHeader || !authHeader.startsWith('Bearer ')) {")
        lines.append("      return HttpResponse.json({")
        lines.append("        code: 401, data: null, message: 'Token 无效或已过期'")
        lines.append("      }, { status: 401 })")
        lines.append("    }")
        lines.append("")

    # 请求体解析（POST/PUT/PATCH）
    if method in ("post", "put", "patch") and "request" in params_str:
        body = ep.get("requestBody", {})
        content_type = body.get("contentType", "application/json") if body else "application/json"
        if "json" in content_type:
            lines.append("    const body = await request.json()")
            lines.append("")

    # 路径参数处理
    if ep.get("pathParams") and "params" in params_str:
        for p in ep["pathParams"]:
            pname = p.get("name", "id")
            lines.append(f"    const {pname} = params.{pname}")
        lines.append("")

    # 分页逻辑
    if is_paginated(ep):
        lines.append("    // 分页参数")
        lines.append("    const url = new URL(request.url)")
        lines.append("    const page = parseInt(url.searchParams.get('page') || '1')")
        lines.append("    const pageSize = parseInt(url.searchParams.get('pageSize') || '10')")
        lines.append("")

    # 响应策略
    if strategy == "random":
        lines.append("    // 随机返回成功或错误")
        lines.append("    if (Math.random() > 0.5) {")
        lines.append(f"      return HttpResponse.json({json.dumps(success_example, ensure_ascii=False)})")
        lines.append("    }")
        lines.append(f"    return HttpResponse.json({json.dumps(error_example, ensure_ascii=False)}, {{ status: 400 }})")
    elif strategy == "error":
        lines.append(f"    return HttpResponse.json({json.dumps(error_example, ensure_ascii=False)}, {{ status: 400 }})")
    else:
        lines.append(f"    return HttpResponse.json({json.dumps(success_example, ensure_ascii=False)})")

    lines.append("  }),")
    return "\n".join(lines)


def generate_module_file(module: str, endpoints: List[Dict]) -> str:
    """生成单个模块的 handler 文件"""
    var_name = safe_var_name(module) + "Handlers"

    lines = []
    lines.append("import { http, HttpResponse, delay } from 'msw'")
    lines.append(f"// 数据文件可用于构建更真实的 Mock 响应")
    lines.append(f"// import {module}Data from '../data/{module_file_name(module)}.json'")
    lines.append("")
    lines.append(f"export const {var_name} = [")

    for i, ep in enumerate(endpoints):
        if i > 0:
            lines.append("")
        lines.append(generate_handler_code(ep))

    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def generate_data_file(module: str, endpoints: List[Dict]) -> Dict:
    """生成模块的 Mock 数据文件"""
    data: Dict = {}
    for ep in endpoints:
        endpoint_name = ep.get("endpoint", "unknown")
        key = safe_var_name(endpoint_name.split(".")[-1]) if "." in endpoint_name else safe_var_name(endpoint_name)

        success_example = {}
        for r in ep.get("responses", []):
            if str(r.get("status", "")).startswith("2"):
                success_example = r.get("example", {})
                break

        data[key] = {
            "endpoint": endpoint_name,
            "method": ep.get("method", "GET"),
            "path": ep.get("path", "/"),
            "example": success_example,
        }
    return data


def generate_index_file(modules: Dict[str, List[Dict]]) -> str:
    """生成 handlers/index.js 汇总文件"""
    lines = []
    all_handlers = []

    for module in sorted(modules.keys()):
        var_name = safe_var_name(module) + "Handlers"
        file_name = module_file_name(module)
        lines.append(f"import {{ {var_name} }} from './{file_name}'")
        all_handlers.append(f"  ...{var_name},")

    lines.append("")
    lines.append("export const handlers = [")
    lines.extend(all_handlers)
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def generate_browser_file(modules: Dict[str, List[Dict]]) -> str:
    """生成 browser.js MSW 启动入口"""
    lines = []
    lines.append("import { setupWorker } from 'msw/browser'")
    lines.append("import { handlers } from './handlers/index'")
    lines.append("")
    lines.append("export const worker = setupWorker(...handlers)")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    output_root = Path(args.output_root).resolve()

    endpoints = contract.get("endpoints", [])
    modules = group_by_module(endpoints)

    # 创建目录
    handlers_dir = output_root / "mock" / "handlers"
    data_dir = output_root / "mock" / "data"
    handlers_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # 生成各模块文件
    for module, eps in modules.items():
        file_name = module_file_name(module)

        # handler 文件
        handler_code = generate_module_file(module, eps)
        (handlers_dir / f"{file_name}.js").write_text(handler_code, encoding="utf-8")
        print(f"[generate-msw] 写入：{handlers_dir / f'{file_name}.js'}")

        # 数据文件
        data = generate_data_file(module, eps)
        (data_dir / f"{file_name}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[generate-msw] 写入：{data_dir / f'{file_name}.json'}")

    # index.js
    index_code = generate_index_file(modules)
    (handlers_dir / "index.js").write_text(index_code, encoding="utf-8")
    print(f"[generate-msw] 写入：{handlers_dir / 'index.js'}")

    # browser.js
    browser_code = generate_browser_file(modules)
    (output_root / "mock" / "browser.js").write_text(browser_code, encoding="utf-8")
    print(f"[generate-msw] 写入：{output_root / 'mock' / 'browser.js'}")

    print(f"[generate-msw] 完成：{len(modules)} 个模块，{len(endpoints)} 个接口")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
