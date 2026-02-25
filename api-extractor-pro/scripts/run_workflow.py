#!/usr/bin/env python3
"""
run_workflow.py — 流水线主控
一键执行：扫描 → 契约 → Mock → 文档 → 校验 → 变更报告

建议顺序：
1) 静态页面项目先用 static-to-api-layer 完成页面 API 化改造
2) 再使用本工作流统一生成接口治理产物
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行前端 API 工作流")
    parser.add_argument("--config", required=True, help="JSON 配置文件路径")
    return parser.parse_args()


def load_config(path: Path) -> Dict[str, Any]:
    """加载并校验配置"""
    config = json.loads(path.read_text(encoding="utf-8"))
    if "project_root" not in config:
        raise ValueError("配置文件必须包含 project_root 字段")

    config.setdefault("scope", [])
    config.setdefault("entry_hints", [])
    config.setdefault("auth_mode", "bearer")
    config.setdefault("output_dir", config["project_root"])
    config.setdefault("project_name", "项目")
    config.setdefault("strict_mode", False)
    config.setdefault("interactive", False)
    return config


def list_to_csv(v: Any) -> str:
    """将列表转为逗号分隔字符串"""
    if isinstance(v, list):
        return ",".join(str(x) for x in v)
    if isinstance(v, str):
        return v
    return ""


def run_cmd(cmd: List[str], label: str) -> int:
    """运行子命令"""
    print(f"\n{'='*60}")
    print(f"[workflow] {label}")
    print(f"[workflow] cmd: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[workflow] ❌ {label} 失败（退出码 {result.returncode}）")
        return result.returncode
    print(f"[workflow] ✅ {label} 完成")
    return 0


def endpoint_map(contract: Dict) -> Dict[Tuple[str, str], Dict]:
    """构建接口索引"""
    out = {}
    for ep in contract.get("endpoints", []):
        key = (str(ep.get("method", "GET")).upper(), ep.get("path", "/"))
        out[key] = ep
    return out


def classify_change(old: Dict, new: Dict) -> str:
    """分类变更类型"""
    if not old and new:
        return "non-breaking（新增接口）"
    if old and not new:
        return "⚠️ breaking（删除接口）"

    old_params = {p.get("name") for p in old.get("pathParams", []) + old.get("query", [])}
    new_params = {p.get("name") for p in new.get("pathParams", []) + new.get("query", [])}
    if not old_params.issubset(new_params):
        return "⚠️ breaking（参数移除）"

    return "non-breaking（兼容更新）"


def generate_diff_report(prev_path: Path, curr_path: Path, report_path: Path) -> None:
    """生成变更报告"""
    curr = json.loads(curr_path.read_text(encoding="utf-8"))
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.exists() else {"endpoints": []}

    prev_map = endpoint_map(prev)
    curr_map = endpoint_map(curr)
    keys = sorted(set(prev_map.keys()) | set(curr_map.keys()))

    lines: List[str] = []
    lines.append("# 接口变更报告")
    lines.append("")
    lines.append(f"- 生成时间：`{datetime.now(timezone.utc).isoformat()}`")
    lines.append(f"- 上次接口数：`{len(prev_map)}`")
    lines.append(f"- 当前接口数：`{len(curr_map)}`")
    lines.append("")

    added = removed = modified = 0

    if not keys:
        lines.append("暂无接口数据。")
    else:
        lines.append("| 状态 | Method | Path | 变更类型 |")
        lines.append("|------|--------|------|----------|")

        for method, path in keys:
            old = prev_map.get((method, path))
            new = curr_map.get((method, path))
            cls = classify_change(old, new)

            if old and not new:
                status = "🔴 删除"
                removed += 1
            elif not old and new:
                status = "🟢 新增"
                added += 1
            elif old != new:
                status = "🟡 修改"
                modified += 1
            else:
                status = "⚪ 未变"

            lines.append(f"| {status} | `{method}` | `{path}` | {cls} |")

        lines.append("")
        lines.append(f"**汇总**：新增 {added}、修改 {modified}、删除 {removed}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[workflow] 变更报告：{report_path}")


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    config = load_config(Path(args.config).resolve())

    project_root = Path(config["project_root"]).resolve()
    output_dir = Path(config.get("output_dir", project_root)).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    scan_result = output_dir / "scan_result.json"
    contract_path = output_dir / "contract.json"
    prev_contract = output_dir / ".contract.prev.json"

    # 保存上次契约
    if contract_path.exists():
        prev_contract.write_text(contract_path.read_text(encoding="utf-8"), encoding="utf-8")
        print("[workflow] 已备份上次契约")

    print(f"\n{'#'*60}")
    print(f"# API Extractor Pro — 全流程工作流")
    print(f"# 项目：{project_root}")
    print(f"# 输出：{output_dir}")
    print(f"{'#'*60}")

    # ---- 阶段 1：扫描 ----
    scan_cmd = [
        sys.executable,
        str(script_dir / "scan.py"),
        "--project-root", str(project_root),
        "--output", str(scan_result),
    ]
    scope = list_to_csv(config.get("scope", []))
    if scope:
        scan_cmd.extend(["--scope", scope])
    entry_hints = list_to_csv(config.get("entry_hints", []))
    if entry_hints:
        scan_cmd.extend(["--entry-hints", entry_hints])

    ret = run_cmd(scan_cmd, "阶段 1：扫描分析")
    if ret != 0:
        return ret

    # ---- 阶段 2：生成契约 ----
    contract_cmd = [
        sys.executable,
        str(script_dir / "build_contract.py"),
        "--scan-result", str(scan_result),
        "--auth-mode", config.get("auth_mode", "bearer"),
        "--output", str(contract_path),
    ]
    if config.get("strict_mode"):
        contract_cmd.append("--strict-mode")

    ret = run_cmd(contract_cmd, "阶段 2：生成契约")
    if ret != 0:
        return ret

    # ---- 阶段 3：用户确认（交互模式）----
    if config.get("interactive"):
        print("\n[workflow] ⏳ 阶段 3：等待用户确认")
        print("[workflow] 请查看 contract.json，确认后按 Enter 继续...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print("\n[workflow] 用户取消")
            return 1

    # ---- 阶段 4：生成 MSW Mock ----
    msw_cmd = [
        sys.executable,
        str(script_dir / "generate_msw.py"),
        "--contract", str(contract_path),
        "--output-root", str(output_dir),
    ]
    ret = run_cmd(msw_cmd, "阶段 4：生成 MSW Mock")
    if ret != 0:
        return ret

    # ---- 阶段 5：生成文档 ----
    docs_cmd = [
        sys.executable,
        str(script_dir / "generate_docs.py"),
        "--contract", str(contract_path),
        "--output-root", str(output_dir),
        "--project-name", config.get("project_name", "项目"),
    ]
    ret = run_cmd(docs_cmd, "阶段 5：生成接口文档")
    if ret != 0:
        return ret

    # ---- 阶段 6：一致性校验 ----
    consistency_cmd = [
        sys.executable,
        str(script_dir / "check_consistency.py"),
        "--contract", str(contract_path),
        "--openapi", str(output_dir / "docs" / "openapi.yaml"),
        "--handlers", str(output_dir / "mock" / "handlers"),
        "--report", str(output_dir / "reports" / "consistency-report.md"),
    ]
    if config.get("strict_mode"):
        consistency_cmd.append("--strict-mode")

    ret = run_cmd(consistency_cmd, "阶段 6：一致性校验")
    if ret != 0 and config.get("strict_mode"):
        return ret

    # ---- 阶段 7：变更报告 ----
    print(f"\n{'='*60}")
    print("[workflow] 阶段 7：生成变更报告")
    print(f"{'='*60}")
    generate_diff_report(prev_contract, contract_path, output_dir / "reports" / "api-diff.md")

    # ---- 完成 ----
    print(f"\n{'#'*60}")
    print("# ✅ 全流程完成！")
    print(f"#")
    print(f"# 产物清单：")
    print(f"#   扫描结果：   {scan_result}")
    print(f"#   接口契约：   {contract_path}")
    print(f"#   MSW Mock：   {output_dir / 'mock/'}")
    print(f"#   接口文档：   {output_dir / 'docs/api-docs.md'}")
    print(f"#   OpenAPI：    {output_dir / 'docs/openapi.yaml'}")
    print(f"#   一致性报告： {output_dir / 'reports/consistency-report.md'}")
    print(f"#   变更报告：   {output_dir / 'reports/api-diff.md'}")
    print(f"{'#'*60}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
