"""
掘金 (juejin.cn) 需求挖掘
通过掘金公开搜索 API 获取开发者文章。
掘金是国内高质量开发者社区，比 B站 的开发者信号密度高得多。
"""
import json
import time
import urllib.request
import urllib.parse

# 掘金搜索 API（无需认证，有频率限制）
SEARCH_API = "https://api.juejin.cn/search_api/v1/search"


def search_juejin(keyword: str, max_results: int = 20) -> list:
    """搜索掘金文章，返回结构化结果"""
    results = []
    cursor = "0"

    while len(results) < max_results:
        params = {
            "key_word": keyword,
            "limit": min(10, max_results - len(results)),
            "cursor": cursor,
        }
        url = f"{SEARCH_API}?{urllib.parse.urlencode(params)}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Origin": "https://juejin.cn",
            "Referer": "https://juejin.cn/search",
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[掘金/搜索] Error: {e}", end="")
            break

        if data.get("err_no") != 0:
            print(f"[掘金/API] err_no={data.get('err_no')}: {data.get('err_msg', '')}", end="")
            break

        items = data.get("data", [])
        if not items:
            break

        for item in items:
            if len(results) >= max_results:
                break

            model = item.get("result_model", {})
            info = model.get("article_info", {})
            title = info.get("title", "").strip()
            article_id = info.get("article_id", "")
            
            if not title or not article_id:
                continue

            result = {
                "title": title,
                "url": f"https://juejin.cn/post/{article_id}",
                "summary": info.get("brief_content", "").strip(),
                "source": "juejin",
                "platform": "juejin",
                "keyword": keyword,
                "author": info.get("user_name", "") or model.get("author", ""),
                "created_at": info.get("ctime", ""),
            }

            # 尝试提取标签（GameDev / Godot 相关分类）
            tags = model.get("tags", [])
            result["tags"] = [t.get("tag_name", "") for t in tags if t.get("tag_name")]

            results.append(result)

        # 翻页
        cursor = data.get("cursor", "0")
        has_more = data.get("has_more", False)
        if not has_more:
            break

        time.sleep(0.3)

    return results
