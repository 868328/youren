#!/usr/bin/env python3
"""
🦐 工具收割机 — 扫描其他 agent 框架的工具源码，提取并转换为我们 ToolV2 格式

支持的数据源：
    - Cline: GitHub 上开源的 VS Code 扩展工具定义
    - OpenClaw: 本地 docs/ 中的工具文档
    - Claude Code: MCP 服务器 / 内置工具
    - LangChain: 社区工具插件

用法：
    python tool_harvester.py                        # 扫描全部
    python tool_harvester.py --source cline          # 只扫 Cline
    python tool_harvester.py --convert data/*.json   # 从已有数据分析
"""

import os
import sys
import json
import re
import logging
import argparse
from datetime import datetime

# 确保在 project 目录运行
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(_SCRIPT_DIR)
sys.path.insert(0, os.path.expanduser("~/.agent"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tool_harvester")

SOURCES_DIR = os.path.join(_SCRIPT_DIR, "sources")
OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "output")
os.makedirs(SOURCES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# 数据源: Cline (GitHub 开源工具定义)
# ══════════════════════════════════════════════════════════════════════════

CLINE_TOOLS_URL = "https://raw.githubusercontent.com/cline/cline/main/src/agent/tools/"

CLINE_TOOL_FILES = [
    "ReadFileTool.ts",
    "WriteFileTool.ts",
    "ListDirectoryTool.ts",
    "BashTool.ts",
    "WebFetchTool.ts",
    "WebSearchTool.ts",
    "FileSearchTool.ts",
    "GitTool.ts",
    "GlobTool.ts",
    "GrepTool.ts",
    "ListFilesTool.ts",
    "EditTool.ts",
]


def scan_cline_tools() -> list[dict]:
    """扫描 Cline 开源工具源码"""
    import urllib.request

    tools = []
    for filename in CLINE_TOOL_FILES:
        url = CLINE_TOOLS_URL + filename
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                source = resp.read().decode("utf-8")
            tool = _parse_cline_tool(filename, source)
            if tool:
                tools.append(tool)
                logger.info(f"Cline: 提取 {tool['name']}")
        except Exception:
            logger.debug(f"Cline: {filename} 不可用")

    return tools


def _parse_cline_tool(filename: str, source: str) -> dict:
    """解析 Cline TypeScript 工具定义"""
    tool = {
        "source": "cline",
        "source_file": filename,
        "name": filename.replace("Tool.ts", "").lower(),
        "description": "",
        "schema": {"type": "object", "properties": {}, "required": []},
        "permission": "write",
        "implementation_hints": [],
    }

    # 提取 description
    m = re.search(r'description:\s*"([^"]+)"', source)
    if m:
        tool["description"] = m.group(1)

    # 提取 inputSchema
    m = re.search(r"inputSchema:\s*({.*?}),?\s*(?:description|name|\\n)", source, re.DOTALL)
    if m:
        try:
            schema = json.loads(m.group(1))
            tool["schema"] = schema
        except json.JSONDecodeError:
            pass

    # 判断权限级别
    if any(kw in source.lower() for kw in ["read", "search", "list", "grep"]):
        tool["permission"] = "read"
    elif any(kw in source.lower() for kw in ["bash", "exec", "run"]):
        tool["permission"] = "exec"
    elif any(kw in source.lower() for kw in ["write", "edit", "create", "delete"]):
        tool["permission"] = "write"

    # 提取实现提示
    if "exec" in source:
        tool["implementation_hints"].append("uses subprocess/shell")
    if "readFile" in source:
        tool["implementation_hints"].append("uses fs.readFile")
    if "fetch" in source:
        tool["implementation_hints"].append("uses HTTP fetch")

    return tool


# ══════════════════════════════════════════════════════════════════════════
# 数据源: OpenClaw (本地文档中的工具定义)
# ══════════════════════════════════════════════════════════════════════════

def scan_openclaw_tools() -> list[dict]:
    """从本地文档扫描 OpenClaw 工具定义"""
    docs_dir = os.path.expanduser(
        "~/.nvm/versions/node/v24.16.0/lib/node_modules/openclaw/docs/tools"
    )
    if not os.path.isdir(docs_dir):
        logger.warning("OpenClaw 工具文档目录不可用")
        return []

    tools = []
    for fname in sorted(os.listdir(docs_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(docs_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            tool = _parse_openclaw_tool(fname, content)
            if tool:
                tools.append(tool)
        except Exception as e:
            logger.debug(f"OpenClaw: {fname} 解析失败: {e}")

    return tools


def _parse_openclaw_tool(fname: str, content: str) -> dict:
    """解析 OpenClaw 工具 Markdown 文档"""
    tool = {
        "source": "openclaw",
        "source_file": fname,
        "name": fname.replace(".md", "").replace("-", "_"),
        "description": "",
        "schema": {"type": "object", "properties": {}, "required": []},
        "permission": "write",
        "implementation_hints": [],
    }

    # 提取标题作为名称
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        tool["name"] = m.group(1).strip().lower().replace(" ", "_").replace("-", "_")

    # 提取 description（第一段）
    m = re.search(r"^>.+$\n\n(.+?)\n\n", content, re.MULTILINE)
    if not m:
        m = re.search(r"^# .+\n\n(.+?)\n\n", content, re.MULTILINE)
    if m:
        tool["description"] = m.group(1).strip()[:200]

    # 提取参数
    params = re.findall(r"\*\*`([^`]+)`\*\*", content)
    if params:
        tool["schema"]["properties"] = {p: {"type": "string"} for p in params}
        tool["schema"]["required"] = params[:1]

    return tool


# ══════════════════════════════════════════════════════════════════════════
# 转换器: 提取的工具 → ToolV2 Python 代码
# ══════════════════════════════════════════════════════════════════════════

TOOL_TEMPLATE = '''"""
🦐 工具: {name}
来源: {source} ({source_file})
"""

from tools import ToolV2, ToolResult


class {class_name}(ToolV2):
    """{description}"""

    name = "{name}"
    description = "{description}"
    permission = "{permission}"
    category = "{category}"
    version = "2.0.0"

    schema = {schema}

    def run(self{params}) -> ToolResult:
        """
        TODO: 实现工具逻辑
        参考来源: {source}
        """
        # {hints_text}
        raise NotImplementedError("工具待实现: {name}")
'''


def _to_class_name(name: str) -> str:
    """tool_name → ToolName"""
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def _to_params(schema: dict) -> str:
    """schema properties → 函数参数"""
    props = schema.get("properties", {})
    required = schema.get("required", [])
    params = []
    for pname, pinfo in props.items():
        ptype = pinfo.get("type", "str")
        type_map = {"string": "str", "integer": "int", "boolean": "bool", "number": "float", "array": "list", "object": "dict"}
        py_type = type_map.get(ptype, "str")
        if pname in required:
            params.append(f"{pname}: {py_type}")
        else:
            default = pinfo.get("default", "")
            if default != "":
                params.append(f'{pname}: {py_type} = {repr(default)}')
            else:
                params.append(f'{pname}: {py_type} = None')
    if params:
        return ", " + ", ".join(params)
    return ""


def generate_tool_code(tool: dict) -> str:
    """生成 ToolV2 Python 代码"""
    name = tool["name"]
    class_name = _to_class_name(name)
    description = tool.get("description", "")
    permission = tool.get("permission", "write")
    schema = tool.get("schema", {"type": "object", "properties": {}, "required": []})
    source = tool.get("source", "unknown")
    source_file = tool.get("source_file", "")
    params = _to_params(schema)

    # 分类
    name_lower = name.lower()
    if any(kw in name_lower for kw in ("read", "list", "search", "grep", "get")):
        category = "read"
    elif any(kw in name_lower for kw in ("write", "edit", "create", "delete")):
        category = "write"
    elif any(kw in name_lower for kw in ("shell", "bash", "exec", "run")):
        category = "exec"
    else:
        category = "general"

    hints = tool.get("implementation_hints", [])
    hints_text = "; ".join(hints) if hints else "待实现"

    code = TOOL_TEMPLATE.format(
        name=name,
        class_name=class_name,
        description=description[:200],
        permission=permission,
        category=category,
        schema=json.dumps(schema, indent=4, ensure_ascii=False),
        params=params,
        source=source,
        source_file=source_file,
        hints_text=hints_text,
    )
    return code


# ══════════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════════

def save_tools(tools: list[dict], prefix: str = ""):
    """保存工具分析数据 + 生成代码"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存 JSON 分析
    json_path = os.path.join(OUTPUT_DIR, f"{ts}_{prefix}_tools.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tools, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON: {json_path} ({len(tools)} 个工具)")

    # 生成 Python 文件
    py_path = os.path.join(OUTPUT_DIR, f"{ts}_{prefix}_tools.py")
    lines = []
    lines.append('"""')
    lines.append(f"🦐 自动生成的工具 — 来源: {prefix}")
    lines.append(f"生成时间: {ts}")
    lines.append(f"工具数量: {len(tools)}")
    lines.append('"""')
    lines.append("")
    lines.append("from tools import ToolV2, ToolResult")
    lines.append("")

    for tool in tools:
        code = generate_tool_code(tool)
        lines.append(code)
        lines.append("")

    with open(py_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Python: {py_path} ({len(tools)} 个工具)")

    return {"json": json_path, "python": py_path, "count": len(tools)}


def main():
    parser = argparse.ArgumentParser(description="🦐 工具收割机")
    parser.add_argument("--source", default="all", help="数据源: cline, openclaw, all")
    parser.add_argument("--output", default="", help="输出目录")
    args = parser.parse_args()

    if args.output:
        global OUTPUT_DIR
        OUTPUT_DIR = args.output
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n  🦐 工具收割机")
    print(f"  {'=' * 40}")
    print(f"  输出: {OUTPUT_DIR}")
    print()

    all_tools = []
    results = []

    if args.source in ("all", "cline"):
        print("  📡 Cline...")
        cline_tools = scan_cline_tools()
        if cline_tools:
            r = save_tools(cline_tools, "cline")
            results.append(r)
            all_tools.extend(cline_tools)
            print(f"     ✅ {len(cline_tools)} 个工具")
        else:
            print("     ⚠️ 不可用（跳过）")

    if args.source in ("all", "openclaw"):
        print("  📡 OpenClaw...")
        oc_tools = scan_openclaw_tools()
        if oc_tools:
            r = save_tools(oc_tools, "openclaw")
            results.append(r)
            all_tools.extend(oc_tools)
            print(f"     ✅ {len(oc_tools)} 个工具")
        else:
            print("     ⚠️ 不可用（跳过）")

    if not all_tools:
        print("  ❌ 没有获取到任何工具\n")
        return

    # 汇总
    total = sum(r["count"] for r in results)
    print(f"\n  {'=' * 40}")
    print(f"  共收割 {total} 个工具")
    for r in results:
        print(f"    {r['python'].split('/')[-1]}")
    print(f"\n  下一步:")
    print(f"    1. 审查生成的 tools/*.py 文件")
    print(f"    2. 实现 TODO 标记的函数体")
    print(f"    3. 复制到 ~/.agent/tools/ 即可自动发现")
    print()


if __name__ == "__main__":
    main()
