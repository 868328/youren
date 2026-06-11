"""
需求探寻 — JSON 存储
每次扫描生成一个带时间戳的 JSON 文件，同时维护一个合并的摘要文件。
"""
import json
import os
from datetime import datetime, timedelta
from config import DATA_DIR, KEEP_DAYS


def save_scan(source: str, keyword: str, results: list):
    """保存一次扫描结果"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_src = source.replace("/", "_")
    safe_kw = keyword.replace(" ", "_").replace("/", "_")
    fname = f"{ts}_{safe_src}_{safe_kw}.json"
    path = os.path.join(DATA_DIR, fname)
    payload = {
        "source": source,
        "keyword": keyword,
        "scanned_at": datetime.now().isoformat(),
        "count": len(results),
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def load_all_recent(days=KEEP_DAYS):
    """加载最近 N 天的所有扫描结果"""
    cutoff = datetime.now() - timedelta(days=days)
    all_results = []
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            scanned = datetime.fromisoformat(data["scanned_at"])
            if scanned >= cutoff:
                all_results.append(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return all_results


def cleanup_old():
    """删除过期文件"""
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    removed = 0
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff:
                os.remove(fpath)
                removed += 1
        except OSError:
            continue
    return removed
