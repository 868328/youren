"""
知乎需求挖掘
通过知乎搜索 API 和热门话题页面，发现中文互联网上普通人的需求和痛点。
"""
import json
import time
import urllib.request
import urllib.parse
from config import PROXY
from sources.bridge_fetch import fetch_url


def search_zhihu(keyword: str, max_results: int = 20) -> list:
    """搜索知乎，返回问题和文章"""
    results = []
    results.extend(_search_zhihu_api(keyword, max_results // 2))
    results.extend(_search_zhihu_api(keyword, max_results // 2, "article"))
    return results[:max_results]


def _search_zhihu_api(keyword: str, limit: int, search_type: str = "content") -> list:
    """知乎搜索 API（通过 web 搜索页）"""
    params = {
        "q": keyword,
        "type": search_type,
    }
    url = "https://www.zhihu.com/search?" + urllib.parse.urlencode(params)

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cookie": "",
    }

    result = fetch_url(url, timeout=15, headers=headers)
    if not result.get("ok"):
        print(f"  [知乎] {result.get('error','失败')}")
        return []
    html = result["body"]

    # 从 HTML 中提取问题和回答标题（知乎搜索结果页面）
    results = []
    # 知乎页面是 SSR，标题在 <title> 和搜索结果块中
    import re

    # 提取搜索结果块
    # 知乎搜索结果中，每条结果大约格式：
    #   <a ...>标题</a> 或者 data-title="..."
    # 用简单策略：找所有带 href="/question/" 的链接

    seen = set()
    for match in re.finditer(
        r'<a[^>]*href="(/(?:question|answer|p|zhuanlan)/[^"]+)"[^>]*>(.*?)</a>',
        html, re.DOTALL
    ):
        href = match.group(1)
        title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if not title or len(title) < 5:
            continue
        if title in seen:
            continue
        seen.add(title)

        # 提取摘要（附近文本）
        snippet = ""
        context_start = max(0, match.start() - 200)
        context = html[context_start:match.end() + 200]
        # 找附近的中文文本作为摘要
        text_parts = re.findall(r'[^<>]{10,}', context)
        for part in text_parts:
            part = part.strip()
            if len(part) > 20 and keyword in part:
                snippet = part[:200]
                break

        results.append({
            "platform": "zhihu",
            "title": title,
            "body": snippet,
            "url": f"https://www.zhihu.com{href}",
            "search_type": search_type,
        })

        if len(results) >= limit:
            break

    return results


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
