#!/usr/bin/env python3
"""
check_consistency.py — 交叉校验 contract ↔ OpenAPI ↔ MSW handlers 一致性
输出 reports/consistency-report.md
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验契约、OpenAPI 和 MSW handlers 一致性")
    parser.add_argument("--contract", required=True, help="contract.json 路径")
    parser.add_argument("--openapi", required=True, help="openapi.yaml 路径")
    parser.add_argument("--handlers", required=True, help="mock/handlers/ 目录路径")
    parser.add_argument("--report", required=True, help="报告输出路径")
    parser.add_argument("--strict-mode", action="store_true", help="严格模式，失败返回非零退出码")
    return parser.parse_args()


def extract_contract_pairs(contract: Dict) -> Set[Tuple[str, str]]:
    """从 contract.json 提取 method+path 集合"""
    pairs = set()
    for ep in contract.get("endpoints", []):
        method = str(ep.get("method", "GET")).upper()
        path = ep.get("path", "/")
        pairs.add((method, path))
    return pairs


def extract_openapi_pairs(yaml_text: str) -> Set[Tuple[str, str]]:
    """从 OpenAPI YAML 解析 method+path"""
    pairs: Set[Tuple[str, str]] = set()
    current_path = None
    in_paths = False
    path_indent = None

    for line in yaml_text.splitlines():
        stripped = line.strip()

        if stripped == "paths:":
            in_paths = True
            path_indent = len(line) - len(line.lstrip(" "))
            continue

        if not in_paths or not stripped:
            continue

        indent = len(line) - len(line.lstrip(" "))

        # 退出 paths 块
        if indent <= path_indent and stripped.endswith(":") and not stripped.startswith("/"):
            break

        # 路径行
        if stripped.startswith("/") and stripped.endswith(":"):
            current_path = stripped[:-1].strip().strip('"').strip("'")
            continue

        # HTTP 方法行
        m = re.match(r"^(get|post|put|patch|delete):$", stripped)
        if m and current_path:
            pairs.add((m.group(1).upper(), current_path))

    return pairs


def extract_handler_pairs(handlers_dir: Path) -> Set[Tuple[str, str]]:
    """从 MSW handler 文件提取 method+path"""
    pairs: Set[Tuple[str, str]] = set()

    if handlers_dir.is_file():
        files = [handlers_dir]
    elif handlers_dir.is_dir():
        files = list(handlers_dir.glob("*.js")) + list(handlers_dir.glob("*.ts"))
    else:
        return pairs

    for fp in files:
        if fp.name in ("index.js", "index.ts"):
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in re.finditer(r"http\.(get|post|put|patch|delete)\s*\(\s*'([^']+)'", content):
            method = m.group(1).upper()
            # 将 :id 转为 {id} 以便与契约对比
            path = re.sub(r":(\w+)", r"{\1}", m.group(2))
            pairs.add((method, path))

    return pairs


def check_duplicates(endpoints: List[Dict]) -> List[str]:
    """检查重复接口"""
    seen = {}
    dups = []
    for ep in endpoints:
        key = f"{ep.get('method', 'GET')} {ep.get('path', '/')}"
        if key in seen:
            dups.append(key)
        seen[key] = True
    return dups


def check_quality(endpoints: List[Dict]) -> List[str]:
    """检查契约质量"""
    issues: List[str] = []
    for ep in endpoints:
        name = ep.get("endpoint", "unknown")

        # 命名规范
        if "." not in name:
            issues.append(f"`{name}`: 接口命名应为 `domain.action` 格式")

        # 成功响应
        has_success = any(
            str(r.get("status", "")).startswith("2")
            for r in ep.get("responses", [])
        )
        if not has_success:
            issues.append(f"`{name}`: 缺少 2xx 成功响应")

        # 错误响应
        has_error = any(
            str(e.get("status", "")).startswith(("4", "5"))
            for e in ep.get("errors", [])
        )
        if not has_error:
            issues.append(f"`{name}`: 缺少 4xx/5xx 错误响应")

    return issues


def format_pairs(pairs: List[Tuple[str, str]]) -> List[str]:
    """格式化 method+path 对"""
    return [f"`{m} {p}`" for m, p in sorted(pairs)]


def main() -> int:
    args = parse_args()

    # 读取 contract
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    endpoints = contract.get("endpoints", [])
    contract_pairs = extract_contract_pairs(contract)

    # 读取 OpenAPI
    openapi_path = Path(args.openapi)
    if openapi_path.exists():
        openapi_pairs = extract_openapi_pairs(openapi_path.read_text(encoding="utf-8"))
    else:
        openapi_pairs = set()
        print(f"[consistency] 警告：OpenAPI 文件不存在 {args.openapi}")

    # 读取 MSW handlers
    handlers_path = Path(args.handlers)
    handler_pairs = extract_handler_pairs(handlers_path)

    # 执行检查
    duplicates = check_duplicates(endpoints)
    quality_issues = check_quality(endpoints)

    missing_in_openapi = contract_pairs - openapi_pairs
    missing_in_handlers = contract_pairs - handler_pairs
    extra_in_openapi = openapi_pairs - contract_pairs
    extra_in_handlers = handler_pairs - contract_pairs

    # 生成报告
    ts = datetime.now(timezone.utc).isoformat()
    lines: List[str] = []
    lines.append("# 一致性校验报告")
    lines.append("")
    lines.append(f"- 生成时间：`{ts}`")
    lines.append(f"- 契约接口数：`{len(contract_pairs)}`")
    lines.append(f"- OpenAPI 接口数：`{len(openapi_pairs)}`")
    lines.append(f"- MSW Handler 数：`{len(handler_pairs)}`")
    lines.append("")

    total_issues = 0

    def section(title: str, items: List[str], emoji: str = "❌") -> None:
        nonlocal total_issues
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("✅ 无问题")
        else:
            total_issues += len(items)
            for item in items:
                lines.append(f"- {emoji} {item}")
        lines.append("")

    section("重复接口", duplicates)
    section("契约质量问题", quality_issues, "⚠️")
    section("契约中有但 OpenAPI 中缺失", format_pairs(list(missing_in_openapi)))
    section("契约中有但 MSW Handler 中缺失", format_pairs(list(missing_in_handlers)))
    section("OpenAPI 中多余（契约中不存在）", format_pairs(list(extra_in_openapi)), "⚠️")
    section("MSW Handler 中多余（契约中不存在）", format_pairs(list(extra_in_handlers)), "⚠️")

    # 汇总
    lines.append("## 汇总")
    lines.append("")
    if total_issues == 0:
        lines.append("✅ **全部通过**，契约、OpenAPI 和 MSW handlers 三者一致。")
    else:
        lines.append(f"⚠️ 发现 **{total_issues}** 个问题，请检查并修复。")
    lines.append("")

    # 写入报告
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[consistency] 报告：{report_path}")

    if total_issues > 0 and args.strict_mode:
        print(f"[consistency] 严格模式：发现 {total_issues} 个问题，返回失败")
        return 2

    print("[consistency] ✅ 校验完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
