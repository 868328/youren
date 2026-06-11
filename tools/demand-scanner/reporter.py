"""
需求探寻 — 摘要报告生成
从收集到的原始数据里提取核心信号：高频话题、高共鸣帖、潜在需求方向。
"""
from collections import Counter, defaultdict
from datetime import datetime


def generate_report(all_data: list, days: int = 30) -> str:
    """生成人类可读的摘要报告"""
    lines = []

    # ── 头部 ──
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"# 📊 需求探寻报告")
    lines.append(f"生成时间: {now}")
    lines.append(f"覆盖范围: 最近 {days} 天，共 {len(all_data)} 次扫描")
    lines.append("")

    # ── 基础统计 ──
    total_items = sum(d["count"] for d in all_data)
    source_counts = Counter(d["source"] for d in all_data)
    kw_counts = Counter(d["keyword"] for d in all_data)

    lines.append("## 📈 基础统计")
    lines.append(f"- 总条目数: {total_items}")
    lines.append(f"- 数据源分布:")
    for src, cnt in source_counts.most_common():
        lines.append(f"  - {src}: {cnt} 次扫描")
    lines.append("")

    # ── 聚合所有结果（去重） ──
    all_results = []
    seen_urls = set()
    for scan in all_data:
        for r in scan.get("results", []):
            url = r.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            all_results.append(r)

    if not all_results:
        lines.append("*(暂无数据)*")
        return "\n".join(lines)

    # ── 高频词统计（标题） ──
    title_words = Counter()
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                  "to", "of", "in", "for", "on", "with", "at", "by", "from",
                  "and", "or", "not", "but", "if", "as", "it", "its", "this",
                  "that", "do", "does", "did", "has", "have", "had", "can",
                  "will", "would", "could", "should", "may", "might", "i",
                  "my", "me", "we", "our", "you", "your", "he", "she", "it",
                  "they", "them", "what", "which", "who", "how", "why",
                  "no", "yes", "so", "up", "out", "about", "just", "like",
                  "all", "also", "very", "more", "some", "any", "get", "need",
                  "help", "use", "way", "one", "two", "new", "now", "then",
                  "here", "there", "when", "where", "been", "after", "into",
                  "over", "still", "while", "than", "too", "much", "many",
                  "even", "only", "each", "other", "such", "through", "able",
                  "want", "looking", "trying", "having", "doing", "going",
                  "know", "think", "make", "take", "work", "try", "see"}

    for r in all_results:
        title = r.get("title", "")
        for word in title.lower().split():
            word = word.strip(".,!?;:'\"()[]{}<>")
            if len(word) > 2 and word not in stop_words and word.isalpha():
                title_words[word] += 1

    lines.append("## 🔥 标题高频词（Top 20）")
    lines.append("| 词 | 出现次数 |")
    lines.append("|---|--------:|")
    for word, cnt in title_words.most_common(20):
        lines.append(f"| {word} | {cnt} |")
    lines.append("")

    # ── 高互动条目（回复/评论/分数最多） ──
    def sort_key(r):
        return r.get("reactions", 0) + r.get("comments", 0) + \
               r.get("score", 0) + r.get("replies", 0) * 2

    sorted_items = sorted(all_results, key=sort_key, reverse=True)

    lines.append("## 💬 最高互动条目（Top 15）")
    lines.append("")
    for item in sorted_items[:15]:
        platform = item.get("platform", "?")
        title = item.get("title", "(无标题)")
        url = item.get("url", "")
        score = sort_key(item)
        body = item.get("body", "")
        lines.append(f"### [{platform}] {title}")
        lines.append(f"- 互动指数: {score}  |  {url}")
        if body:
            # 取前 200 字摘要
            preview = body[:200].replace("\n", " ").strip()
            if len(body) > 200:
                preview += "..."
            lines.append(f"- 摘要: {preview}")
        lines.append("")

    # ── 按平台统计 ──
    by_platform = defaultdict(list)
    for r in all_results:
        by_platform[r.get("platform", "unknown")].append(r)

    lines.append("## 🏷️ 按平台分析")
    for platform, items in by_platform.items():
        lines.append(f"\n### {platform} ({len(items)} 条)")
        # Top 5 by interaction
        top5 = sorted(items, key=sort_key, reverse=True)[:5]
        for item in top5:
            score = sort_key(item)
            t = item.get("title", "(无标题)")
            u = item.get("url", "")
            lines.append(f"- [{score}] {t}  {u}")
    lines.append("")

    return "\n".join(lines)
