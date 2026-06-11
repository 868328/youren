"""
Bilibili 需求挖掘
通过 B站 公开搜索 API 获取视频/文章列表，以及相关热门讨论。
B站 上有大量教程、评测、吐槽视频，评论区是真实需求的富矿。
"""
import json
import time
import urllib.request
import urllib.parse


def search_bilibili(keyword: str, max_results: int = 20) -> list:
    """搜索 B站 视频和专栏，返回结构化结果"""
    results = []

    # 搜视频
    video_results = _search_video(keyword, max_results)
    results.extend(video_results)

    # 如果视频不够，补专栏
    if len(results) < max_results:
        article_results = _search_article(keyword, max_results - len(results))
        results.extend(article_results)

    return results[:max_results]


def _search_video(keyword: str, limit: int) -> list:
    """通过 B站 搜索 API 获取视频列表"""
    params = urllib.parse.urlencode({
        "keyword": keyword,
        "search_type": "video",
        "page": 1,
    })
    url = f"https://api.bilibili.com/x/web-interface/search/type?{params}"

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
        "Referer": "https://search.bilibili.com/",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [B站/视频] Error: {e}")
        return []

    if data.get("code") != 0:
        print(f"  [B站/视频] API error: {data.get('message', 'unknown')}")
        return []

    results = []
    for v in data.get("data", {}).get("result", [])[:limit]:
        results.append({
            "platform": "bilibili",
            "type": "video",
            "title": v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
            "body": v.get("description", "")[:300] if v.get("description") else "",
            "url": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
            "play": v.get("play", 0),
            "video_review": v.get("video_review", 0),  # 弹幕数
            "author": v.get("author", ""),
            "created": v.get("pubdate", 0),
            "tag": v.get("tag", ""),
        })

    return results


def _search_article(keyword: str, limit: int) -> list:
    """搜索 B站 专栏文章"""
    params = urllib.parse.urlencode({
        "keyword": keyword,
        "search_type": "article",
        "page": 1,
    })
    url = f"https://api.bilibili.com/x/web-interface/search/type?{params}"

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
        "Referer": "https://search.bilibili.com/",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [B站/专栏] Error: {e}")
        return []

    if data.get("code") != 0:
        return []

    results = []
    for a in data.get("data", {}).get("result", [])[:limit]:
        results.append({
            "platform": "bilibili",
            "type": "article",
            "title": a.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
            "body": a.get("description", "")[:300] if a.get("description") else "",
            "url": a.get("url", ""),
            "author": a.get("author_name", ""),
            "view": a.get("view", 0),
            "like": a.get("like", 0),
        })

    return results
