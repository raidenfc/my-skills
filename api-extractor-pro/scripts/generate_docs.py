#!/usr/bin/env python3
"""
generate_docs.py — 从 contract.json 生成中文 Markdown 文档和 OpenAPI 3.1 YAML
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从契约生成接口文档")
    parser.add_argument("--contract", required=True, help="contract.json 路径")
    parser.add_argument("--output-root", required=True, help="输出根目录")
    parser.add_argument("--project-name", default="项目", help="项目名称")
    parser.add_argument("--version", default="1.0.0", help="API 版本")
    return parser.parse_args()


# =====================================================
# Markdown 文档生成
# =====================================================

def build_markdown(contract: Dict, project_name: str) -> str:
    """生成中文 Markdown 接口文档"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    endpoints = contract.get("endpoints", [])
    meta = contract.get("meta", {})

    lines: List[str] = []

    # 头部信息
    lines.append(f"# {project_name} 接口文档")
    lines.append("")
    lines.append(f"> 📅 生成时间：{ts}")
    lines.append(f"> 📊 接口总数：{len(endpoints)} 个")
    lines.append(f"> 🔧 技术栈：{meta.get('framework', '未知')} + MSW Mock")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 按模块分组
    modules: Dict[str, List[Dict]] = {}
    for ep in endpoints:
        module = ep.get("module", "default")
        modules.setdefault(module, []).append(ep)

    # 目录
    lines.append("## 目录")
    lines.append("")
    lines.append("- [1. 通用规范](#1-通用规范)")
    lines.append("- [2. 快速接入 MSW Mock](#2-快速接入-msw-mock)")
    for i, module in enumerate(sorted(modules.keys()), start=3):
        lines.append(f"- [{i}. {module} 模块](#{i}-{module}-模块)")
    lines.append(f"- [{len(modules) + 3}. 错误码总览](#{len(modules) + 3}-错误码总览)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. 通用规范
    lines.append("## 1. 通用规范")
    lines.append("")
    lines.append("### 请求地址")
    lines.append("")
    lines.append("| 环境 | Base URL |")
    lines.append("|------|----------|")
    lines.append("| 开发（Mock） | `http://localhost:3000`（由 MSW 拦截） |")
    lines.append("| 测试环境 | `https://staging.api.example.com` |")
    lines.append("| 生产环境 | `https://api.example.com` |")
    lines.append("")

    if meta.get("baseURL"):
        lines.append(f"> 📌 项目 BaseURL 配置：`{meta['baseURL']}`")
        lines.append("")

    lines.append("### 认证方式")
    lines.append("")
    auth_mode = meta.get("authMode", "bearer")
    if auth_mode == "bearer":
        lines.append("```http")
        lines.append("Authorization: Bearer <token>")
        lines.append("```")
    lines.append("")

    lines.append("### 统一响应格式")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps({"code": 200, "data": {}, "message": "success"}, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("### 分页接口响应格式")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps({
        "code": 200,
        "data": {"list": [], "total": 100, "page": 1, "pageSize": 10},
        "message": "success",
    }, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. MSW 接入
    lines.append("## 2. 快速接入 MSW Mock")
    lines.append("")
    lines.append("### 安装")
    lines.append("")
    lines.append("```bash")
    lines.append("npm install msw --save-dev")
    lines.append("npx msw init public/ --save")
    lines.append("```")
    lines.append("")
    lines.append("### 启用（入口文件）")
    lines.append("")
    lines.append("```javascript")
    lines.append("if (import.meta.env.DEV) {")
    lines.append("  const { worker } = await import('./mock/browser')")
    lines.append("  await worker.start({ onUnhandledRequest: 'bypass' })")
    lines.append("}")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 各模块接口
    for i, (module, eps) in enumerate(sorted(modules.items()), start=3):
        lines.append(f"## {i}. {module} 模块")
        lines.append("")

        for ep in eps:
            method = ep.get("method", "GET")
            path = ep.get("path", "/")
            endpoint_name = ep.get("endpoint", "")
            desc = endpoint_name.split(".")[-1] if "." in endpoint_name else endpoint_name

            lines.append(f"### {method} {path} — {desc}")
            lines.append("")

            # 认证标记
            if any(h.get("name") == "Authorization" for h in ep.get("headers", [])):
                lines.append("**认证**：✅ 需要 Bearer Token")
            else:
                lines.append("**认证**：❌ 无需")
            lines.append("")

            # 路径参数
            path_params = ep.get("pathParams", [])
            if path_params:
                lines.append("**路径参数**")
                lines.append("")
                lines.append("| 参数 | 类型 | 说明 |")
                lines.append("|------|------|------|")
                for p in path_params:
                    lines.append(f"| {p.get('name')} | {p.get('type', 'string')} | {p.get('description', '')} |")
                lines.append("")

            # 查询参数
            query_params = ep.get("query", [])
            if query_params:
                lines.append("**查询参数**")
                lines.append("")
                lines.append("| 参数 | 类型 | 必填 | 默认值 | 说明 |")
                lines.append("|------|------|:----:|--------|------|")
                for q in query_params:
                    required = "✅" if q.get("required") else "❌"
                    default = q.get("default", "—")
                    lines.append(f"| {q.get('name')} | {q.get('type', 'string')} | {required} | {default} | {q.get('description', '')} |")
                lines.append("")

            # 请求体
            body = ep.get("requestBody")
            if body:
                content_type = body.get("contentType", "application/json")
                lines.append(f"**请求体**（{content_type}）")
                lines.append("")
                schema = body.get("schema", {})
                props = schema.get("properties", {})
                if props:
                    lines.append("| 参数 | 类型 | 说明 |")
                    lines.append("|------|------|------|")
                    for name, info in props.items():
                        lines.append(f"| {name} | {info.get('type', 'any')} | {info.get('description', '')} |")
                    lines.append("")

            # 成功响应
            for r in ep.get("responses", []):
                if str(r.get("status", "")).startswith("2"):
                    lines.append(f"**响应示例**（成功 {r.get('status', 200)}）")
                    lines.append("")
                    lines.append("```json")
                    lines.append(json.dumps(r.get("example", {}), ensure_ascii=False, indent=2))
                    lines.append("```")
                    lines.append("")

            # 错误响应
            errors = ep.get("errors", [])
            if errors:
                lines.append("**错误码**")
                lines.append("")
                lines.append("| 错误码 | 说明 |")
                lines.append("|--------|------|")
                for e in errors:
                    lines.append(f"| {e.get('status', 400)} | {e.get('message', '错误')} |")
                lines.append("")

            # 待确认项
            todos = ep.get("x-todo-confirm", [])
            if todos:
                lines.append("> ⚠️ **待确认项**")
                for t in todos:
                    lines.append(f"> - {t}")
                lines.append("")

            lines.append("---")
            lines.append("")

    # 错误码总览
    lines.append(f"## {len(modules) + 3}. 错误码总览")
    lines.append("")
    lines.append("| 错误码 | 含义 | 前端处理建议 |")
    lines.append("|--------|------|-------------|")
    lines.append("| 200 | 成功 | — |")
    lines.append("| 400 | 请求参数错误 | 表单校验提示 |")
    lines.append("| 401 | 未授权 / Token 失效 | 跳转登录页 |")
    lines.append("| 403 | 无权限 | 提示\"暂无权限\" |")
    lines.append("| 404 | 资源不存在 | 提示\"数据不存在\" |")
    lines.append("| 409 | 数据冲突 | 提示具体冲突原因 |")
    lines.append("| 429 | 请求频率过高 | 提示\"操作过于频繁\" |")
    lines.append("| 500 | 服务器内部错误 | 提示\"服务异常，请稍后重试\" |")
    lines.append("")

    return "\n".join(lines)


# =====================================================
# OpenAPI YAML 生成
# =====================================================

def yaml_value(v: Any) -> str:
    """转换为 YAML 标量值"""
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if any(c in s for c in [':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'"]):
        return f'"{s}"'
    return s


def dict_to_yaml(obj: Any, indent: int = 0) -> List[str]:
    """递归将字典转为 YAML 文本"""
    space = "  " * indent
    lines: List[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{space}{k}:")
                lines.extend(dict_to_yaml(v, indent + 1))
            else:
                lines.append(f"{space}{k}: {yaml_value(v)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{space}-")
                lines.extend(dict_to_yaml(item, indent + 1))
            else:
                lines.append(f"{space}- {yaml_value(item)}")
    else:
        lines.append(f"{space}{yaml_value(obj)}")
    return lines


def build_openapi(contract: Dict, project_name: str, version: str) -> Dict:
    """构建 OpenAPI 3.1 结构"""
    endpoints = contract.get("endpoints", [])
    meta = contract.get("meta", {})

    paths: Dict = {}
    for ep in endpoints:
        path = ep.get("path", "/")
        method = ep.get("method", "GET").lower()

        op: Dict[str, Any] = {
            "operationId": ep.get("endpoint", "unknown"),
            "tags": [ep.get("module", "default")],
            "summary": ep.get("endpoint", ""),
            "parameters": [],
            "responses": {},
        }

        # 路径参数
        for p in ep.get("pathParams", []):
            op["parameters"].append({
                "name": p.get("name"),
                "in": "path",
                "required": True,
                "schema": {"type": p.get("type", "string")},
                "description": p.get("description", ""),
            })

        # 查询参数
        for q in ep.get("query", []):
            param: Dict[str, Any] = {
                "name": q.get("name"),
                "in": "query",
                "required": bool(q.get("required", False)),
                "schema": {"type": q.get("type", "string")},
                "description": q.get("description", ""),
            }
            if "default" in q:
                param["schema"]["default"] = q["default"]
            op["parameters"].append(param)

        # 请求头
        for h in ep.get("headers", []):
            op["parameters"].append({
                "name": h.get("name"),
                "in": "header",
                "required": bool(h.get("required", False)),
                "schema": {"type": h.get("type", "string")},
            })

        # 请求体
        body = ep.get("requestBody")
        if body:
            content_type = body.get("contentType", "application/json")
            op["requestBody"] = {
                "required": method in {"post", "put", "patch"},
                "content": {
                    content_type: {
                        "schema": body.get("schema", {"type": "object"}),
                    }
                },
            }

        # 成功响应
        for r in ep.get("responses", []):
            code = str(r.get("status", 200))
            op["responses"][code] = {
                "description": r.get("description", "成功"),
                "content": {
                    "application/json": {
                        "schema": r.get("schema", {"type": "object"}),
                        "example": r.get("example", {}),
                    }
                },
            }

        # 错误响应
        for e in ep.get("errors", []):
            code = str(e.get("status", 400))
            op["responses"][code] = {
                "description": e.get("message", "错误"),
                "content": {
                    "application/json": {
                        "example": e.get("example", {}),
                    }
                },
            }

        paths.setdefault(path, {})
        paths[path][method] = op

    auth_mode = meta.get("authMode", "bearer")
    security_schemes = {}
    if auth_mode == "bearer":
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "登录后获取的 JWT Token",
        }

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": f"{project_name} API",
            "version": version,
            "description": f"{project_name} 接口文档，由 api-extractor-pro 自动生成",
        },
        "servers": [
            {"url": "http://localhost:3000", "description": "开发环境（MSW Mock）"},
            {"url": "https://api.example.com", "description": "生产环境"},
        ],
        "paths": paths,
    }

    if security_schemes:
        spec["components"] = {"securitySchemes": security_schemes}

    return spec


def main() -> int:
    args = parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    output_root = Path(args.output_root).resolve()
    docs_dir = output_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 生成 Markdown
    md = build_markdown(contract, args.project_name)
    md_path = docs_dir / "api-docs.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"[generate-docs] 写入：{md_path}")

    # 生成 OpenAPI YAML
    spec = build_openapi(contract, args.project_name, args.version)
    yaml_lines = dict_to_yaml(spec)
    yaml_path = docs_dir / "openapi.yaml"
    yaml_path.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    print(f"[generate-docs] 写入：{yaml_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
