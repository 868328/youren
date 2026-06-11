"""
GitHub Issues 需求挖掘
搜索指定关键词相关的 Issue，提取标题和正文，用于发现用户的痛点和需求。
"""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from config import GITHUB_TOKEN


def search_issues(keyword: str, max_results: int = 20) -> list:
    """搜索 GitHub Issues，返回结构化结果列表。

    搜索 godotengine/ 仓库的 issues（聚焦游戏引擎本身的问题/建议）。
    使用 GitHub Search API:
      GET /search/issues?q=KEYWORD+repo:godotengine/...&sort=reactions&order=desc
    """
    # 在 godotengine/ 相关仓库中搜索
    repos = ["godotengine/godot", "godotengine/godot-proposals", "godotengine/godot-docs"]
    repo_query = "+".join(f"repo:{r}" for r in repos)
    url = (
        "https://api.github.com/search/issues"
        f"?q={urllib.parse.quote(keyword)}+{repo_query}+is:issue"
        "&sort=reactions"
        "&order=desc"
        f"&per_page={min(max_results, 100)}"
    )
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "demand-scanner/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  [GitHub] HTTP {e.code}: {e.reason}")
        return []
    except Exception as e:
        print(f"  [GitHub] Error: {e}")
        return []

    results = []
    for item in data.get("items", []):
        results.append({
            "platform": "github",
            "title": item.get("title", ""),
            "body": _truncate(item.get("body", ""), 500),
            "url": item.get("html_url", ""),
            "repo": item.get("repository_url", "").replace(
                "https://api.github.com/repos/", ""
            ),
            "state": item.get("state", ""),
            "reactions": item.get("reactions", {}).get("total_count", 0),
            "comments": item.get("comments", 0),
            "created_at": item.get("created_at", ""),
        })

    return results


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
