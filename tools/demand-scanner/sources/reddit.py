"""
Reddit 需求挖掘
通过 Reddit JSON API 搜索指定子版块的热门帖子和抱怨帖。
"""
import json
import time
import urllib.request
import urllib.parse
from config import PROXY
from sources.bridge_fetch import fetch_url


def search_reddit(keyword: str, max_results: int = 20,
                  subreddits: list | None = None) -> list:
    """搜索 Reddit 多个子版块"""
    if subreddits is None:
        from config import REDDIT_SUBREDDITS
        subreddits = REDDIT_SUBREDDITS

    results = []
    for sub in subreddits:
        fetched = _search_sub(sub, keyword, max_results // len(subreddits) + 1)
        results.extend(fetched)
        time.sleep(1)  # 礼貌延迟

    # 按分数排序取前 max_results
    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return results[:max_results]


def _search_sub(subreddit: str, keyword: str, limit: int) -> list:
    """搜索单个子版块"""
    query = urllib.parse.quote(keyword)
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={query}"
        "&sort=top"
        "&t=year"
        "&restrict_sr=on"
        f"&limit={min(limit, 100)}"
    )

    headers = {
        "User-Agent": "demand-scanner/1.0 (by /u/anon)",
        "Accept": "application/json",
    }

    result = fetch_url(url, timeout=15, headers=headers)
    if not result.get("ok"):
        print(f"  [Reddit/r/{subreddit}] {result.get('error','失败')}")
        return []

    try:
        data = json.loads(result["body"])
    except Exception as e:
        print(f"  [Reddit/r/{subreddit}] JSON解析失败: {e}")
        return []

    results = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        if post.get("stickied"):
            continue
        results.append({
            "platform": "reddit",
            "subreddit": subreddit,
            "title": post.get("title", ""),
            "body": _truncate(post.get("selftext", ""), 500),
            "url": "https://reddit.com" + post.get("permalink", ""),
            "score": post.get("score", 0),
            "comments": post.get("num_comments", 0),
            "created_utc": post.get("created_utc", 0),
        })

    return results


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
