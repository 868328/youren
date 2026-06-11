"""
V2EX 需求挖掘
通过 V2EX 公开 API 获取各节点最新主题，筛选包含关键词的帖子。
对外开发者的吐槽、求助、项目展示中蕴含真实需求。
"""
import json
import time
import urllib.request
import urllib.parse
from config import PROXY
from sources.bridge_fetch import fetch_url


def search_v2ex(keyword: str, max_results: int = 20,
                nodes: list | None = None) -> list:
    """在 V2EX 多个节点中搜索包含关键词的主题"""
    if nodes is None:
        from config import V2EX_NODES
        nodes = V2EX_NODES

    headers = {
        "User-Agent": "demand-scanner/1.0",
    }

    results = []
    seen_ids = set()

    for node in nodes:
        topics = _get_node_topics(headers, node, limit=20)
        for t in topics:
            tid = t.get("id")
            if tid in seen_ids:
                continue
            seen_ids.add(tid)

            title = t.get("title", "")
            content = t.get("content_rendered", "") or ""

            # 关键词匹配（标题或内容含关键词）
            if keyword.lower() not in title.lower() and keyword.lower() not in content.lower():
                continue

            results.append({
                "platform": "v2ex",
                "node": node,
                "title": title,
                "body": _truncate(content, 500),
                "url": f"https://www.v2ex.com/t/{tid}",
                "replies": t.get("replies", 0),
                "created": t.get("created", 0),
                "member": t.get("member", {}).get("username", ""),
            })

            if len(results) >= max_results:
                break

        time.sleep(1)  # 礼貌延迟

    results.sort(key=lambda r: r.get("replies", 0), reverse=True)
    return results[:max_results]


def _get_node_topics(headers, node_name: str, limit: int = 20) -> list:
    """获取某节点最新的主题列表"""
    url = f"https://www.v2ex.com/api/v2/nodes/{node_name}/topics"
    result = fetch_url(url, timeout=10, headers=headers)
    if not result.get("ok"):
        return []
    try:
        data = json.loads(result["body"])
        if isinstance(data, list):
            return data[:limit]
        return []
    except Exception:
        return []


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
