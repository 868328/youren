"""
Windows 桥接 HTTP 抓取工具
通过 Windows HTTP 桥接发送 HTTP 请求，绕过 WSL 代理 IP 被封的问题。

Windows 有独立网络连接（不走代理），所以不会触发 Reddit/V2EX/知乎的 IP 封禁。

用法：
    from sources.bridge_fetch import fetch_url
    result = fetch_url("https://www.reddit.com/r/godot/search.json?q=bug")
    if result["ok"]:
        data = json.loads(result["body"])

降级策略（优先级）:
    1. Windows 桥接（HTTP）— 最快，绕过代理 IP 封禁
    2. 直连（无代理）— WSL 可能没网络
    3. 本地代理（mihomo）— 可能 IP 被封
"""

import json
import time
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger("bridge_fetch")

# Windows 桥接地址（WSL2 中 Windows 主机 IP = 默认网关）
_win_ip = None
_bridge_port = 9876


def _get_windows_ip() -> str:
    """自动检测 Windows 主机 IP"""
    global _win_ip
    if _win_ip:
        return _win_ip
    try:
        import subprocess
        result = subprocess.run(
            ["ip", "route"],
            capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines():
            if line.startswith("default via "):
                _win_ip = line.split()[2]
                return _win_ip
    except Exception:
        pass
    return "172.27.80.1"  # 默认回退


def _bridge_available() -> bool:
    """检查 Windows 桥接是否在线"""
    win_ip = _get_windows_ip()
    url = f"http://{win_ip}:{_bridge_port}/health"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _fetch_via_bridge(url: str, timeout: int = 15) -> dict:
    """
    通过 Windows 桥接抓取 URL。

    Windows 端执行 curl 或 python urllib 抓取页面，返回结果。
    """
    win_ip = _get_windows_ip()
    bridge_url = f"http://{win_ip}:{_bridge_port}/"

    # 用 Python 在 Windows 端抓取（兼容性好，无额外依赖）
    # 注意：JSON 中的引号需要转义
    escaped_url = url.replace("\\", "\\\\").replace('"', '\\"')
    py_code = (
        "import urllib.request, urllib.error, json, sys; "
        f"try: "
        f"  r = urllib.request.urlopen('{escaped_url}', timeout={timeout}); "
        f"  b = r.read(); "
        f"  print(json.dumps({{'ok': True, 'body': b.decode('utf-8','replace'), 'status': r.status}})) "
        f"except Exception as e: "
        f"  print(json.dumps({{'ok': False, 'error': str(e)[:200]}}))"
    )

    payload = {
        "action": "exec",
        "command": f'python -c "{py_code}"',
        "timeout": timeout,
    }

    try:
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                try:
                    return json.loads(result.get("stdout", "{}"))
                except json.JSONDecodeError:
                    return {"ok": False, "error": "Bridge returned invalid JSON"}
            return {"ok": False, "error": result.get("error", "Bridge exec failed")}
    except Exception as e:
        return {"ok": False, "error": f"Bridge connection failed: {e}"}


def fetch_url(url: str, timeout: int = 15, headers: dict = None) -> dict:
    """
    抓取 URL，自动尝试多种方式。

    优先级：
        1. Windows 桥接（绕过代理封禁）
        2. 非代理直连
        3. 本地代理（mihomo）

    Returns:
        {"ok": bool, "body": str, "status": int, "method": str}
        或 {"ok": False, "error": str}
    """
    # 方法 1: Windows 桥接
    if _bridge_available():
        try:
            result = _fetch_via_bridge(url, timeout)
            if result.get("ok"):
                result["method"] = "bridge"
                return result
        except Exception:
            pass

    # 方法 2: 直连
    try:
        req = urllib.request.Request(url)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {"ok": True, "body": body, "status": resp.status, "method": "direct"}
    except Exception as e:
        pass

    # 方法 3: 通过代理
    from config import PROXY
    try:
        req = urllib.request.Request(url)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        proxy_handler = urllib.request.ProxyHandler({"https": PROXY, "http": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {"ok": True, "body": body, "status": resp.status, "method": "proxy"}
    except Exception as e:
        pass

    return {"ok": False, "error": "所有方式均失败"}
