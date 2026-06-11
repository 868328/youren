#!/usr/bin/env python3
"""
Agent 框架架构扫描器 — CLI 入口

分析主流 AI agent 框架的架构设计，输出结构化对比报告。

用法:
  # 扫描并分析全部框架
  python scanner.py

  # 只看指定框架
  python scanner.py --frameworks claude-code,langchain

  # 基于已有数据生成报告（不重新抓取）
  python scanner.py --report

  # 列出所有已存储的数据
  python scanner.py --list
"""
import sys
import json
import os
import re
import argparse
from datetime import datetime

from config import FRAMEWORKS, DIMENSIONS, DATA_DIR, OUTPUT_DIR


def extract_architecture(raw_text: str, framework: str) -> dict:
    """从原始文档中提取架构信息"""
    analysis = {
        "framework": framework,
        "tool_routing": _find_section(raw_text, ["tool", "function call", "MCP", "plugin"]),
        "memory_system": _find_section(raw_text, ["memory", "context", "history", "state"]),
        "session_mgmt": _find_section(raw_text, ["session", "conversation", "thread"]),
        "context_mgmt": _find_section(raw_text, ["context", "window", "token", "prompt"]),
        "security_model": _find_section(raw_text, ["security", "sandbox", "permission", "allow"]),
        "CLI_UX": _find_section(raw_text, ["CLI", "command", "terminal", "interface"]),
        "mcp_protocol": _find_section(raw_text, ["MCP", "protocol", "model context"]),
        "execution_model": _find_section(raw_text, ["async", "stream", "loop", "event"]),
    }
    return analysis


def _find_section(text: str, keywords: list[str]) -> list[str]:
    """在文本中找到包含关键词的段落"""
    results = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        lower = line.lower()
        for kw in keywords:
            if kw.lower() in lower and len(line.strip()) > 20:
                # 提取这段和前后文
                start = max(0, i - 1)
                end = min(len(lines), i + 3)
                snippet = "\n".join(lines[start:end])
                snippet = snippet.strip()[:500]
                if snippet not in results:
                    results.append(snippet)
                break
            if len(results) >= 5:
                break
        if len(results) >= 5:
            break
    return results


def save_analysis(framework_id: str, analysis: dict, sources: list[str]):
    """保存分析结果到 JSON"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(DATA_DIR, f"{ts}_{framework_id}.json")
    payload = {
        "framework_id": framework_id,
        "framework_name": FRAMEWORKS.get(framework_id, {}).get("name", framework_id),
        "scanned_at": datetime.now().isoformat(),
        "sources": sources,
        "analysis": analysis,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def load_analyses() -> list[dict]:
    """加载所有已保存的分析数据"""
    results = []
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  ⚠ 跳过 {fname}: {e}")
    return results


def generate_report(analyses: list[dict]) -> str:
    """生成可读的架构对比报告"""
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"# Agent 框架架构对比报告\n")
    lines.append(f"_生成时间: {ts}_\n")
    lines.append(f"共分析 {len(analyses)} 个框架\n")
    lines.append("---\n")

    # 按框架汇总
    for data in analyses:
        name = data["framework_name"]
        fid = data["framework_id"]
        analysis = data.get("analysis", {})

        lines.append(f"## {name} (`{fid}`)\n")
        lines.append(f"扫描时间: {data.get('scanned_at', 'unknown')[:19]}\n")

        for dim in DIMENSIONS:
            key = dim
            items = analysis.get(key, [])
            dim_label = dim.replace("_", " ").title()
            if items:
                lines.append(f"### {dim_label}\n")
                for item in items[:3]:
                    lines.append(f"- {item[:200]}")
                    if len(item) > 200:
                        lines[-1] += "…"
                    lines.append("")
            else:
                lines.append(f"### {dim_label} — (未提取到)\n")

        lines.append("---\n")

    # 交叉对比表
    lines.append("\n## 设计维度交叉对比\n\n")
    lines.append("| 维度 | " + " | ".join(d["framework_name"] for d in analyses) + " |\n")
    lines.append("|" + "|".join("---" for _ in range(len(analyses) + 1)) + "|\n")

    for dim in DIMENSIONS:
        dim_label = dim.replace("_", " ").title()
        row = [dim_label]
        for data in analyses:
            items = data.get("analysis", {}).get(dim, [])
            if items:
                row.append(f"✅ {len(items)} 条")
            else:
                row.append("❌")
        lines.append("| " + " | ".join(row) + " |\n")

    return "".join(lines)


def list_data():
    """列出已存储的数据"""
    analyses = load_analyses()
    if not analyses:
        print("📭 没有已存储的分析数据")
        return

    by_framework = {}
    for data in analyses:
        fid = data["framework_id"]
        by_framework.setdefault(fid, []).append(data)

    print(f"\n📊 共 {len(analyses)} 条分析记录:")
    for fid, items in sorted(by_framework.items()):
        name = FRAMEWORKS.get(fid, {}).get("name", fid)
        print(f"\n  {fid} ({name}):")
        for item in items[-3:]:
            ts = item["scanned_at"][:19]
            dims = sum(1 for v in item.get("analysis", {}).values() if v)
            print(f"    {ts} — {dims}/8 维度有数据")


def main():
    parser = argparse.ArgumentParser(description="Agent 框架架构扫描器 v1.0")
    parser.add_argument("--frameworks", default=",".join(FRAMEWORKS.keys()),
                        help="要分析的框架（逗号分隔）")
    parser.add_argument("--report", action="store_true",
                        help="基于已有数据生成报告")
    parser.add_argument("--list", action="store_true",
                        help="列出已存储的数据")
    parser.add_argument("--output", default="",
                        help="报告输出路径")
    args = parser.parse_args()

    if args.list:
        list_data()
        return

    if args.report:
        analyses = load_analyses()
        if not analyses:
            print("📭 没有数据，先运行 scanner.py（不带 --report）进行分析")
            return
        report = generate_report(analyses)
        output_path = args.output or os.path.join(OUTPUT_DIR, "architecture-report.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(report[:2000])
        print(f"\n... (全文 {len(report)} 字符)")
        print(f"\n📄 报告已保存: {output_path}")
        return

    # 交互式模式：输出要抓取的内容指南
    frameworks = [s.strip() for s in args.frameworks.split(",") if s.strip()]
    valid = [f for f in frameworks if f in FRAMEWORKS]

    print(f"\n🔍 Agent 框架架构扫描器 v1.0")
    print(f"   时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"   待分析框架: {', '.join(FRAMEWORKS[f]['name'] for f in valid)}")
    print()
    print("=" * 60)
    print("  需要手动/自动抓取以下文档: ")
    print("=" * 60)

    for fid in valid:
        cfg = FRAMEWORKS[fid]
        print(f"\n  📄 {cfg['name']} ({fid})")
        if cfg.get("urls"):
            for url in cfg["urls"]:
                print(f"    ▸ {url}")
        if cfg.get("local_docs"):
            print(f"    ▸ [本地] {cfg['local_docs']}")
        print(f"    分析维度: {', '.join(cfg['dimensions'])}")

    print()
    print("=" * 60)
    print("  运行方式:")
    print("  1. 手动抓取：用 web_fetch 抓取上述 URL")
    print("  2. 写入 data/ 目录作为原始数据")
    print("  3. python scanner.py --report 生成对比报告")
    print("=" * 60)


if __name__ == "__main__":
    main()
