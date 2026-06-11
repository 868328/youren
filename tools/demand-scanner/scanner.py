#!/usr/bin/env python3
"""
需求探寻扫描器 — CLI 入口

用法:
  # 用默认关键词扫描全部平台
  python scanner.py

  # 指定关键词和平台
  python scanner.py --keywords "godot,gamedev" --sources github,reddit

  # 只输出摘要报告（读已有数据，不爬）
  python scanner.py --report

  # 清理过期数据
  python scanner.py --cleanup
"""
import sys
import json
import time
import argparse
from datetime import datetime

from config import DEFAULT_KEYWORDS, RESULTS_PER_KEYWORD, DATA_DIR
from storage import save_scan, load_all_recent, cleanup_old
from reporter import generate_report

from sources.github_issues import search_issues
from sources.reddit import search_reddit
from sources.v2ex import search_v2ex
from sources.zhihu import search_zhihu
from sources.bilibili import search_bilibili
from sources.juejin import search_juejin
from sources.hackernews import search_hackernews


def scan_all(keywords: list[str], sources: list[str],
             max_per_kw: int = RESULTS_PER_KEYWORD):
    """扫描所有平台 + 所有关键词"""
    all_saved = []

    for kw in keywords:
        print(f"\n{'='*50}")
        print(f"  关键词: {kw}")
        print(f"{'='*50}")

        for src_name in sources:
            print(f"\n  ▸ {src_name} ...", end=" ", flush=True)
            results = _run_source(src_name, kw, max_per_kw)
            if results:
                path = save_scan(src_name, kw, results)
                print(f"{len(results)} 条 → {path}")
                all_saved.append({"source": src_name, "keyword": kw,
                                  "count": len(results), "path": path})
            else:
                print("0 条")
            time.sleep(0.5)

    return all_saved


def _run_source(src_name: str, keyword: str, limit: int) -> list:
    """调度单个数据源"""
    try:
        if src_name == "github":
            return search_issues(keyword, limit)
        elif src_name == "reddit":
            return search_reddit(keyword, limit)
        elif src_name == "v2ex":
            return search_v2ex(keyword, limit)
        elif src_name == "zhihu":
            return search_zhihu(keyword, limit)
        elif src_name == "bilibili":
            return search_bilibili(keyword, limit)
        elif src_name == "juejin":
            return search_juejin(keyword, limit)
        elif src_name == "hackernews":
            return search_hackernews(keyword, limit)
        else:
            print(f"(未知数据源: {src_name})", end="")
            return []
    except Exception as e:
        print(f"(!{e})", end="")
        return []


def main():
    parser = argparse.ArgumentParser(description="需求探寻扫描器")
    parser.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS),
                        help="关键词（逗号分隔）")
    parser.add_argument("--sources", default="github,juejin,hackernews",
                        help="数据源（逗号分隔）")
    parser.add_argument("--report", action="store_true",
                        help="基于已有数据生成摘要报告")
    parser.add_argument("--cleanup", action="store_true",
                        help="清理过期数据")
    parser.add_argument("--days", type=int, default=30,
                        help="报告涵盖天数（默认 30）")
    parser.add_argument("--test", action="store_true",
                        help="测试各数据源连通性")
    args = parser.parse_args()

    if args.test:
        print(f"🔌 数据源连通性测试")
        print(f"   时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
        print()
        for src in ["github", "bilibili", "reddit", "v2ex", "zhihu"]:
            print(f"  ▸ {src} ...", end=" ", flush=True)
            results = _run_source(src, "test", 1)
            if results:
                print(f"✅ ({len(results)} 条)")
            else:
                print(f"❌")
            time.sleep(0.5)
        return

    if args.cleanup:
        n = cleanup_old()
        print(f"清理了 {n} 个过期文件")
        return

    if args.report:
        data = load_all_recent(days=args.days)
        if not data:
            print("没有数据，先运行 scanner.py（不带 --report）抓取")
            return
        report = generate_report(data, days=args.days)
        print(report)
        # 也存一份
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"{DATA_DIR}/_report_{ts}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存: {report_path}")
        return

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    print(f"🔍 需求探寻扫描器 v1.0")
    print(f"   时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"   关键词: {keywords}")
    print(f"   数据源: {sources}")
    print()

    scan_all(keywords, sources)

    print(f"\n{'='*50}")
    print(f"  扫描完成！数据保存在 {DATA_DIR}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
