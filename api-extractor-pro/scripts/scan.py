#!/usr/bin/env python3
"""
scan.py — 前端 API 调用扫描器
合并 6 大类 API 调用模式，输出结构化 scan_result.json
"""
import argparse
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# =====================================================
# 配置常量
# =====================================================
TEXT_EXT = {".js", ".ts", ".jsx", ".tsx", ".vue", ".wxml"}
IGNORE_DIRS = {"node_modules", "dist", "build", ".git", "coverage", "__tests__", ".nuxt", ".output", ".cache", ".next"}

# =====================================================
# 匹配模式：6 大类
# =====================================================

# 1. Axios 快捷方法：axios.get('/url')
AXIOS_METHOD_RE = re.compile(
    r"""axios\.(get|post|put|patch|delete)\s*\(\s*(['"`])([^'"`]+)\2""",
    re.IGNORECASE,
)

# 2. Axios config 对象：axios({ url: '/url', method: 'POST' })
AXIOS_CONFIG_RE = re.compile(
    r"""axios\s*\(\s*\{[\s\S]{0,500}?url\s*:\s*(['"`])([^'"`]+)\1[\s\S]{0,300}?\}""",
    re.IGNORECASE,
)

# 3. Fetch 原生：fetch('/url', { method: 'POST' })
FETCH_RE = re.compile(
    r"""fetch\s*\(\s*(['"`])([^'"`]+)\1\s*(?:,\s*(\{[\s\S]{0,300}?\}))?\s*\)""",
    re.IGNORECASE,
)

# 4. 自定义封装：request({ url, method }) / api.get() / http.post() / service.xxx()
REQUEST_OBJ_RE = re.compile(
    r"""(?:request|api|http|service)\s*(?:\.\s*(get|post|put|patch|delete))?\s*\(\s*(?:\{[\s\S]{0,500}?url\s*:\s*(['"`])([^'"`]+)\2|(['"`])([^'"`]+)\4)""",
    re.IGNORECASE,
)

# 5. React Query / TanStack：useQuery / useMutation
REACT_QUERY_RE = re.compile(
    r"""(?:useQuery|useMutation|useInfiniteQuery)\s*\(""",
    re.IGNORECASE,
)

# 6. SWR / Vue useRequest
SWR_RE = re.compile(
    r"""(?:useSWR|useRequest)\s*\(\s*(['"`])([^'"`]+)\1""",
    re.IGNORECASE,
)

# 7. 微信小程序 wx.request
WX_REQUEST_RE = re.compile(
    r"""wx\.request\s*\(\s*\{[\s\S]{0,500}?url\s*:\s*(['"`])([^'"`]+)\1""",
    re.IGNORECASE,
)

# 通用 method 提取
METHOD_IN_OBJ_RE = re.compile(r"""method\s*:\s*['"]?(GET|POST|PUT|PATCH|DELETE)['"]?""", re.IGNORECASE)


@dataclass
class ScanMatch:
    """单个 API 调用匹配记录"""
    method: str
    path: str
    file: str
    line: int
    pattern: str
    context: str = ""


@dataclass
class ScanResult:
    """完整扫描结果"""
    projectRoot: str = ""
    framework: str = "未知"
    baseURL: str = ""
    authPattern: str = ""
    apiDirs: List[str] = field(default_factory=list)
    matches: List[Dict[str, Any]] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描前端项目中的 API 调用")
    parser.add_argument("--project-root", required=True, help="项目根目录")
    parser.add_argument("--scope", default="", help="扫描范围（逗号分隔目录）")
    parser.add_argument("--entry-hints", default="", help="API 封装层目录提示（逗号分隔）")
    parser.add_argument("--output", default="", help="输出文件路径（默认：项目根目录下 scan_result.json）")
    return parser.parse_args()


def parse_csv(raw: str) -> List[str]:
    """解析逗号分隔字符串"""
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def line_at(content: str, index: int) -> int:
    """根据字符索引计算行号"""
    return content.count("\n", 0, index) + 1


def get_context(content: str, index: int, max_len: int = 120) -> str:
    """提取匹配位置的上下文（当前行内容）"""
    line_start = content.rfind("\n", 0, index) + 1
    line_end = content.find("\n", index)
    if line_end == -1:
        line_end = len(content)
    line = content[line_start:line_end].strip()
    return line[:max_len] + ("..." if len(line) > max_len else "")


# =====================================================
# 项目结构分析
# =====================================================

def detect_framework(project_root: Path) -> str:
    """检测前端框架"""
    checks = [
        (["next.config.js", "next.config.mjs", "next.config.ts"], "Next.js"),
        (["nuxt.config.ts", "nuxt.config.js"], "Nuxt.js"),
        (["vue.config.js"], "Vue CLI"),
        (["vite.config.ts", "vite.config.js"], "Vite"),
    ]
    for files, name in checks:
        for f in files:
            if (project_root / f).exists():
                return name
    if (project_root / "package.json").exists():
        try:
            pkg = json.loads((project_root / "package.json").read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "react" in deps:
                return "React"
            if "vue" in deps:
                return "Vue"
        except (json.JSONDecodeError, OSError):
            pass
    return "未知"


def detect_base_url(project_root: Path, files: List[Path]) -> str:
    """检测 BaseURL 配置"""
    patterns = ["baseURL", "BASE_URL", "VITE_API", "REACT_APP_API", "VUE_APP_API", "API_BASE"]
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for p in patterns:
            if p in content:
                # 提取包含该模式的行
                for line in content.splitlines():
                    if p in line:
                        return line.strip()[:100]
    # 检查 .env 文件
    for env_file in [".env", ".env.local", ".env.development"]:
        env_path = project_root / env_file
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    for p in patterns:
                        if p in line:
                            return line.strip()
            except OSError:
                pass
    return ""


def detect_auth(files: List[Path]) -> str:
    """检测认证方式"""
    auth_keywords = ["Authorization", "Bearer", "Access-Token", "interceptors.request"]
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for kw in auth_keywords:
            if kw in content:
                if "Bearer" in content:
                    return "Bearer Token"
                if "Access-Token" in content:
                    return "Access-Token Header"
                return f"检测到: {kw}"
    return ""


def discover_api_dirs(project_root: Path) -> List[str]:
    """发现 API 封装层目录"""
    candidates = ["src/api", "src/services", "src/request", "src/http", "api", "services"]
    found = []
    for d in candidates:
        if (project_root / d).is_dir():
            found.append(d)
    return found


# =====================================================
# 文件遍历
# =====================================================

def iter_files(project_root: Path, scopes: List[str]) -> List[Path]:
    """遍历目标文件"""
    roots = [project_root / s for s in scopes] if scopes else [project_root]
    files: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            for filename in filenames:
                p = Path(dirpath) / filename
                if p.suffix in TEXT_EXT:
                    files.append(p)
    return files


# =====================================================
# 核心扫描逻辑
# =====================================================

def scan_file(file_path: Path, content: str) -> List[ScanMatch]:
    """扫描单个文件中的 API 调用"""
    matches: List[ScanMatch] = []
    rel_path = str(file_path)

    # 1. Axios 快捷方法
    for m in AXIOS_METHOD_RE.finditer(content):
        matches.append(ScanMatch(
            method=m.group(1).upper(),
            path=normalize_url(m.group(3)),
            file=rel_path,
            line=line_at(content, m.start()),
            pattern="axios." + m.group(1).lower(),
            context=get_context(content, m.start()),
        ))

    # 2. Axios config 对象
    for m in AXIOS_CONFIG_RE.finditer(content):
        url = normalize_url(m.group(2))
        # 提取 method
        snippet = content[m.start():min(len(content), m.start() + 500)]
        method_match = METHOD_IN_OBJ_RE.search(snippet)
        method = method_match.group(1).upper() if method_match else "GET"
        matches.append(ScanMatch(
            method=method,
            path=url,
            file=rel_path,
            line=line_at(content, m.start()),
            pattern="axios.config",
            context=get_context(content, m.start()),
        ))

    # 3. Fetch 原生
    for m in FETCH_RE.finditer(content):
        url = normalize_url(m.group(2))
        method = "GET"
        opts = m.group(3) or ""
        mm = METHOD_IN_OBJ_RE.search(opts)
        if mm:
            method = mm.group(1).upper()
        matches.append(ScanMatch(
            method=method,
            path=url,
            file=rel_path,
            line=line_at(content, m.start()),
            pattern="fetch",
            context=get_context(content, m.start()),
        ))

    # 4. 自定义封装
    for m in REQUEST_OBJ_RE.finditer(content):
        quick_method = m.group(1)  # api.get() 中的 get
        url_from_obj = m.group(3) or m.group(5)  # url 字段或直接参数
        if not url_from_obj:
            continue
        url = normalize_url(url_from_obj)

        if quick_method:
            method = quick_method.upper()
        else:
            snippet = content[m.start():min(len(content), m.start() + 500)]
            mm = METHOD_IN_OBJ_RE.search(snippet)
            method = mm.group(1).upper() if mm else "GET"

        matches.append(ScanMatch(
            method=method,
            path=url,
            file=rel_path,
            line=line_at(content, m.start()),
            pattern="request.custom",
            context=get_context(content, m.start()),
        ))

    # 5. React Query / TanStack（仅标记位置，需 AI 进一步分析）
    for m in REACT_QUERY_RE.finditer(content):
        matches.append(ScanMatch(
            method="UNKNOWN",
            path="[需要 AI 分析]",
            file=rel_path,
            line=line_at(content, m.start()),
            pattern="react-query",
            context=get_context(content, m.start()),
        ))

    # 6. SWR / useRequest
    for m in SWR_RE.finditer(content):
        url = normalize_url(m.group(2))
        matches.append(ScanMatch(
            method="GET",
            path=url,
            file=rel_path,
            line=line_at(content, m.start()),
            pattern="swr/useRequest",
            context=get_context(content, m.start()),
        ))

    # 7. 微信小程序 wx.request
    for m in WX_REQUEST_RE.finditer(content):
        url = normalize_url(m.group(2))
        snippet = content[m.start():min(len(content), m.start() + 500)]
        method_match = METHOD_IN_OBJ_RE.search(snippet)
        method = method_match.group(1).upper() if method_match else "GET"
        matches.append(ScanMatch(
            method=method,
            path=url,
            file=rel_path,
            line=line_at(content, m.start()),
            pattern="wx.request",
            context=get_context(content, m.start()),
        ))

    return matches


def normalize_url(raw: str) -> str:
    """规范化 URL 路径"""
    # 分离 query string，只处理路径部分
    parts = raw.split("?", 1)
    path_part = parts[0]
    # 移除模板字符串变量，转为路径参数
    url = re.sub(r"\$\{(\w+)\}", r":\1", path_part)
    # 确保以 / 开头
    if url and not url.startswith("/") and not url.startswith("http"):
        url = "/" + url
    return url


def dedupe_matches(matches: List[ScanMatch]) -> List[ScanMatch]:
    """去重：同一 method + path 合并为一条，保留第一个匹配但记录所有源文件"""
    seen: Dict[tuple, ScanMatch] = {}
    sources: Dict[tuple, List[str]] = {}
    for m in matches:
        key = (m.method, m.path)
        if key not in seen:
            seen[key] = m
            sources[key] = [m.file]
        else:
            if m.file not in sources[key]:
                sources[key].append(m.file)
    # 将多源信息写入 context
    result: List[ScanMatch] = []
    for key, m in seen.items():
        if len(sources[key]) > 1:
            m.context = f"{m.context} [多处调用: {', '.join(sources[key])}]"
        result.append(m)
    return result


# =====================================================
# 主函数
# =====================================================

def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    scopes = parse_csv(args.scope)
    entry_hints = parse_csv(args.entry_hints)
    output_path = Path(args.output) if args.output else project_root / "scan_result.json"

    print(f"[scan] 项目根目录：{project_root}")
    print(f"[scan] 扫描范围：{scopes or '全项目'}")

    # 项目结构分析
    framework = detect_framework(project_root)
    api_dirs = discover_api_dirs(project_root)
    # 合并 entry_hints
    for hint in entry_hints:
        if hint not in api_dirs and (project_root / hint).is_dir():
            api_dirs.append(hint)

    # 收集文件
    files = iter_files(project_root, scopes)
    print(f"[scan] 文件数量：{len(files)}")
    print(f"[scan] 框架：{framework}")
    print(f"[scan] API 目录：{api_dirs or '未发现'}")

    # 检测 baseURL 和认证
    base_url = detect_base_url(project_root, files)
    auth_pattern = detect_auth(files)

    # 扫描所有文件
    all_matches: List[ScanMatch] = []
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        file_matches = scan_file(fp, content)
        # 转换为相对路径
        for m in file_matches:
            try:
                m.file = str(Path(m.file).relative_to(project_root))
            except ValueError:
                pass
        all_matches.extend(file_matches)

    # 优先排序：API 封装层目录中的匹配排在前面
    def sort_key(m: ScanMatch) -> int:
        for i, d in enumerate(api_dirs):
            if m.file.startswith(d):
                return i
        return 999

    all_matches.sort(key=sort_key)
    all_matches = dedupe_matches(all_matches)

    # 过滤掉非 API 路径
    valid_matches = [m for m in all_matches if m.path.startswith("/") or m.path.startswith("http") or m.path == "[需要 AI 分析]"]

    print(f"[scan] 识别到 {len(valid_matches)} 个 API 调用")

    # 构建输出
    result = ScanResult(
        projectRoot=str(project_root),
        framework=framework,
        baseURL=base_url,
        authPattern=auth_pattern,
        apiDirs=api_dirs,
        matches=[asdict(m) for m in valid_matches],
    )

    output_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[scan] 输出：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
