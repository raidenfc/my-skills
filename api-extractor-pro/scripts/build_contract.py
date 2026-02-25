#!/usr/bin/env python3
"""
build_contract.py — 从 scan_result.json 生成结构化 contract.json
contract.json 是整个工作流的唯一事实源（Single Source of Truth）
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# 无需认证的接口关键词
NO_AUTH_KEYWORDS = {"login", "register", "signup", "signin", "auth", "captcha", "verify", "reset-password"}


def needs_auth_by_path(path: str) -> bool:
    """判断路径是否需要认证（登录/注册等公开接口不需要）"""
    path_lower = path.lower()
    return not any(kw in path_lower for kw in NO_AUTH_KEYWORDS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从扫描结果生成接口契约")
    parser.add_argument("--scan-result", required=True, help="scan_result.json 路径")
    parser.add_argument("--auth-mode", default="bearer", help="认证方式：bearer / cookie / custom")
    parser.add_argument("--output", default="contract.json", help="输出文件路径")
    parser.add_argument("--strict-mode", action="store_true", help="严格模式")
    return parser.parse_args()


def endpoint_name(method: str, path: str) -> Tuple[str, str]:
    """从路径推断模块名和接口名

    返回 (module, endpoint) 如 ("user", "user.login")
    """
    # 移除 /api 前缀
    clean = re.sub(r"^/api/", "/", path)
    segments = [s for s in clean.strip("/").split("/") if s and not s.startswith(":") and not s.startswith("{")]
    has_path_param = bool(re.search(r"[:{]", path))

    if not segments:
        module = "default"
    else:
        module = re.sub(r"[^a-zA-Z0-9_]", "_", segments[0]).lower()

    if len(segments) >= 2:
        action = re.sub(r"[^a-zA-Z0-9_]", "_", segments[-1]).lower()
    elif has_path_param:
        # GET /api/user/:id → user.getById, PUT → user.update, DELETE → user.delete
        method_action_map = {"GET": "getById", "PUT": "update", "PATCH": "update", "DELETE": "delete"}
        action = method_action_map.get(method.upper(), method.lower())
    else:
        # GET /api/resources → resources.list, POST → resources.create
        method_action_map = {"GET": "list", "POST": "create", "PUT": "update", "DELETE": "delete"}
        action = method_action_map.get(method.upper(), method.lower())

    return module, f"{module}.{action}"


def extract_path_params(path: str) -> List[Dict]:
    """提取路径参数"""
    # 支持 :id 和 {id} 两种格式
    params = re.findall(r"[:{](\w+)}?", path)
    return [{"name": p, "type": "string", "required": True} for p in params]


def normalize_path_format(path: str) -> str:
    """统一路径参数为 {id} 格式（OpenAPI 标准）"""
    return re.sub(r":(\w+)", r"{\1}", path)


def infer_query_params(path: str) -> List[Dict]:
    """推断查询参数"""
    queries = []
    # 分页接口
    has_path_param = bool(re.search(r"[:{]", path))
    is_list_pattern = any(kw in path.lower() for kw in ["list", "search", "query", "page"])
    is_plural_collection = path.rstrip("/").endswith("s") and not has_path_param
    if is_list_pattern or is_plural_collection:
        queries.extend([
            {"name": "page", "type": "integer", "required": False, "description": "页码", "default": 1},
            {"name": "pageSize", "type": "integer", "required": False, "description": "每页条数", "default": 10},
        ])
    return queries


def infer_headers(auth_mode: str) -> List[Dict]:
    """推断请求头"""
    if auth_mode.lower() == "bearer":
        return [{"name": "Authorization", "type": "string", "required": False, "example": "Bearer <token>"}]
    if auth_mode.lower() == "cookie":
        return [{"name": "Cookie", "type": "string", "required": False}]
    return []


def infer_request_body(method: str, path: str) -> Optional[Dict]:
    """推断请求体"""
    if method not in {"POST", "PUT", "PATCH"}:
        return None
    if "upload" in path.lower() or "file" in path.lower():
        return {
            "contentType": "multipart/form-data",
            "schema": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}},
        }
    return {
        "contentType": "application/json",
        "schema": {"type": "object", "properties": {}},
    }


def build_success_response(path: str) -> Dict:
    """构建成功响应模板"""
    has_path_param = bool(re.search(r"[:{]", path))
    is_list = (any(kw in path.lower() for kw in ["list", "search"]) or path.rstrip("/").endswith("s")) and not has_path_param
    if is_list:
        data = {"list": [], "total": 0, "page": 1, "pageSize": 10}
    else:
        data = {}
    return {
        "status": 200,
        "description": "成功",
        "schema": {
            "type": "object",
            "properties": {
                "code": {"type": "integer", "example": 200},
                "data": {"type": "object"},
                "message": {"type": "string", "example": "success"},
            },
        },
        "example": {"code": 200, "data": data, "message": "success"},
    }


def build_error_response(status: int = 400, message: str = "请求参数错误") -> Dict:
    """构建错误响应模板"""
    return {
        "status": status,
        "code": "BAD_REQUEST",
        "message": message,
        "example": {"code": status, "data": None, "message": message},
    }


def build_todo_confirms(match: Dict) -> List[str]:
    """生成待确认项"""
    todos = []
    pattern = match.get("pattern", "")
    path = match.get("path", "")

    if "react-query" in pattern or "swr" in pattern:
        todos.append("API 路径从 Hook 调用推断，需人工确认")

    if path == "[需要 AI 分析]":
        todos.append("无法自动提取 URL，需 AI 分析代码上下文")

    todos.append("请求/响应 schema 为静态分析推断，需人工确认")

    return todos


def build_contract_endpoint(match: Dict, auth_mode: str) -> Dict:
    """从单个扫描匹配构建契约端点"""
    method = match.get("method", "GET").upper()
    raw_path = match.get("path", "/")
    path = normalize_path_format(raw_path)

    if method not in HTTP_METHODS:
        method = "GET"

    module, endpoint = endpoint_name(method, path)

    return {
        "module": module,
        "endpoint": endpoint,
        "method": method,
        "path": path,
        "pathParams": extract_path_params(path),
        "query": infer_query_params(path),
        "headers": infer_headers(auth_mode) if needs_auth_by_path(path) else [],
        "requestBody": infer_request_body(method, path),
        "responses": [build_success_response(path)],
        "errors": [build_error_response()],
        "mockStrategy": "success",
        "x-todo-confirm": build_todo_confirms(match),
        "source": {
            "file": match.get("file", ""),
            "line": match.get("line", 0),
            "pattern": match.get("pattern", ""),
            "context": match.get("context", ""),
        },
    }


def main() -> int:
    args = parse_args()
    scan_result = json.loads(Path(args.scan_result).read_text(encoding="utf-8"))

    matches = scan_result.get("matches", [])
    # 过滤无法识别的匹配
    valid_matches = [m for m in matches if m.get("method") != "UNKNOWN" or m.get("path") != "[需要 AI 分析]"]

    endpoints = []
    seen = set()
    for m in valid_matches:
        key = (m.get("method", "GET").upper(), normalize_path_format(m.get("path", "/")))
        if key in seen:
            continue
        seen.add(key)
        endpoints.append(build_contract_endpoint(m, args.auth_mode))

    contract = {
        "meta": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "projectRoot": scan_result.get("projectRoot", str(Path(args.scan_result).parent.resolve())),
            "framework": scan_result.get("framework", "未知"),
            "baseURL": scan_result.get("baseURL", ""),
            "authMode": args.auth_mode,
            "strictMode": args.strict_mode,
            "totalEndpoints": len(endpoints),
        },
        "endpoints": endpoints,
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build-contract] 输出：{output_path}")
    print(f"[build-contract] 接口数量：{len(endpoints)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
