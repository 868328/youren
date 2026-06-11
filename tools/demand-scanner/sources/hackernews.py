"""
Hacker News 需求挖掘（Algolia 搜索 API）
通过 Algolia 的 HN 搜索 API 按关键词搜索历史帖子。
支持排序、时间范围过滤，适合定向需求挖掘。
完全免费，无需 token。
"""
import json
import re
import urllib.request
import urllib.parse
from config import PROXY

_proxy_set = False


def _ensure_proxy():
    global _proxy_set
    if not _proxy_set:
        handler = urllib.request.ProxyHandler({"https": PROXY, "http": PROXY})
        urllib.request.install_opener(urllib.request.build_opener(handler))
        _proxy_set = True


def search_hackernews(keyword: str, max_results: int = 20) -> list:
    """通过 Algolia HN 搜索 API 搜索帖子"""
    _ensure_proxy()

    params = urllib.parse.urlencode({
        "query": keyword,
        "tags": "story",
        "hitsPerPage": min(max_results, 50),
    })

    try:
        req = urllib.request.Request(
            f"https://hn.algolia.com/api/v1/search?{params}",
            headers={"User-Agent": "demand-scanner/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [HN] 搜索失败: {e}")
        return []

    results = []
    for hit in data.get("hits", []):
        title = hit.get("title", "")
        url = hit.get("url", "") or hit.get("story_url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        text = hit.get("comment_text", "") or hit.get("story_text", "") or ""

        results.append({
            "platform": "hackernews",
            "title": title,
            "body": re.sub(r"<[^>]+>", "", text).strip()[:300],
            "url": url,
            "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
            "score": hit.get("points", 0),
            "comments": hit.get("num_comments", 0),
            "author": hit.get("author", ""),
            "created_at": hit.get("created_at_i", 0),
        })

    return results[:max_results]
