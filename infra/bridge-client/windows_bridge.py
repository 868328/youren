#!/usr/bin/env python3
"""
🌐 windows_bridge.py — WSL 侧 HTTP 桥接客户端

通过 HTTP API（而非共享文件系统）向 Windows agent.py 发送指令。
完全绕过 9P 文件系统死锁问题。

零外部依赖，仅用 Python 标准库。

用法:
    python3 windows_bridge.py exec 'dir C:\\'
    python3 windows_bridge.py write_file 'D:/test.txt' 'hello'
    python3 windows_bridge.py ping

作为模块导入:
    from windows_bridge import send_command, get_bridge
    result = send_command({"action": "exec", "command": "echo hi"})
"""

import json
import logging
import sys
import urllib.error
import urllib.request

logger = logging.getLogger("bridge")

# ── 配置 ──────────────────────────────────────────────────────────────

# 在 WSL2 中，Windows 主机通过虚拟网络网关可达。
# 自动检测：WSL2 默认网关即 Windows 主机 IP。
def _detect_windows_host() -> str:
    """检测 WSL2 中 Windows 主机的 IP 地址"""
    import subprocess
    try:
        result = subprocess.run(
            ["/sbin/ip", "route"],
            capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines():
            if line.startswith("default via"):
                ip = line.split()[2]
                return ip
    except Exception:
        pass
    return "127.0.0.1"  # fallback

DEFAULT_HOST = _detect_windows_host()
DEFAULT_PORT = 9876
HTTP_TIMEOUT = 30  # 默认超时秒数

# 文件桥接 fallback 配置
SHARED_FS_PATH = "/mnt/d/openclawworkspace/game-dev"


# ── HTTP 客户端 ──────────────────────────────────────────────────────

class WindowsBridge:
    """通过 HTTP API 与 Windows agent.py 通信"""

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=HTTP_TIMEOUT):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout

    def send(self, cmd: dict, timeout: int = None) -> dict:
        """发送指令，返回结果字典"""
        timeout = timeout or self.timeout
        data = json.dumps(cmd, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"HTTP 连接失败: {e.reason}"}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return {"ok": False, "error": f"HTTP {e.code}: {body}"}
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return {"ok": False, "error": f"响应解析失败: {e}"}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def ping(self) -> bool:
        """健康检查"""
        result = self.send({"action": "ping"}, timeout=5)
        return result.get("ok", False)

    @property
    def url(self):
        return self.base_url


# ── 文件桥接 fallback ──────────────────────────────────────────────

def _file_bridge_send(cmd: dict, timeout: int = 30) -> dict:
    """使用文件桥接发送指令（fallback）"""
    import time
    import uuid
    from pathlib import Path

    shared = Path(SHARED_FS_PATH)
    inbox = shared / "inbox"
    outbox = shared / "outbox"
    inbox.mkdir(parents=True, exist_ok=True)
    outbox.mkdir(parents=True, exist_ok=True)

    cmd_id = str(uuid.uuid4())[:8]
    cmd_file = inbox / f"{cmd_id}.json"
    result_file = outbox / f"result_{cmd_id}.json"

    cmd_file.write_text(json.dumps(cmd, ensure_ascii=False), encoding="utf-8")
    logger.info(f"📤 文件桥接: {cmd.get('action')} (ID: {cmd_id})")

    for _ in range(timeout // 2):
        if result_file.exists():
            result = json.loads(result_file.read_text(encoding="utf-8"))
            result_file.unlink()
            return result
        time.sleep(2)

    return {"ok": False, "error": "文件桥接超时（agent.py 是否在运行？）"}


# ── 统一发送接口（HTTP 优先，文件 fallback）─────────────────────────

_http_bridges = {}  # port -> WindowsBridge 实例缓存


def get_http_bridge(port: int = None):
    """获取指定端口的 HTTP 桥接实例（按需创建）"""
    global _http_bridges
    port = port or DEFAULT_PORT
    if port not in _http_bridges:
        _http_bridges[port] = WindowsBridge(port=port)
    return _http_bridges[port]


def send_command(cmd: dict, timeout: int = 30, prefer_http: bool = True) -> dict:
    """
    发送指令到 Windows agent。

    策略：尝试 HTTP 一次 → 失败则立刻降级到文件桥接。
    不缓存可用状态（每次尝试都是新鲜的），避免 9P 断连后状态过时。

    参数:
        cmd: 指令字典
        timeout: 超时秒数
        prefer_http: 是否优先尝试 HTTP（True=HTTP优先，False=文件桥接优先）

    返回:
        结果字典
    """
    if prefer_http:
        bridge = get_http_bridge()
        # 快速尝试 HTTP，不缓存状态
        try:
            result = bridge.send(cmd, timeout)
            # HTTP 成功（ok=true 或非连接类错误）→ 返回结果
            if result.get("ok") or ("连接失败" not in result.get("error", "") and "Connection refused" not in result.get("error", "")):
                return result
        except Exception:
            pass
        # HTTP 失败（连接拒绝/超时等）→ 安静降级

    # 文件桥接（fallback）
    logger.info("📂 使用文件桥接（HTTP 不可用）")
    return _file_bridge_send(cmd, timeout)


def force_check():
    """检测 HTTP 桥接是否可用（不缓存结果）"""
    bridge = get_http_bridge()
    try:
        result = bridge.ping()
        status = "✅ 可用" if result else "⚠️ 异常"
        logger.info(f"🌐 HTTP 桥接: {status}")
        return result
    except Exception:
        logger.warning("🌐 HTTP 桥接: ❌ 不可用")
        return False


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Windows 桥接客户端")
    parser.add_argument("action", nargs="?", help="操作类型 (exec/write_file/read_file/...)")
    parser.add_argument("args", nargs="*", help="操作参数")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"HTTP 端口（默认 {DEFAULT_PORT}）")
    parser.add_argument("--file", action="store_true", help="强制使用文件桥接")
    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        print()
        print(__doc__)
        sys.exit(1)

    # 如果指定了 --port，创建对应端口的桥接
    global _http_bridges
    if args.port != DEFAULT_PORT:
        _http_bridges[DEFAULT_PORT] = WindowsBridge(port=args.port)
    elif DEFAULT_PORT not in _http_bridges:
        _http_bridges[DEFAULT_PORT] = WindowsBridge(port=args.port)

    action = args.action
    pos = args.args
    cmd = {"action": action}

    if action == "exec":
        cmd["command"] = pos[0] if pos else input("command? ")
        if len(pos) > 1:
            cmd["timeout"] = int(pos[1])
    elif action == "write_file":
        cmd["path"] = pos[0] if pos else ""
        cmd["content"] = pos[1] if len(pos) > 1 else sys.stdin.read()
    elif action == "read_file":
        cmd["path"] = pos[0] if pos else ""
    elif action == "godot_headless":
        cmd["project"] = pos[0] if pos else ""
        cmd["script"] = pos[1] if len(pos) > 1 else ""
        if len(pos) > 2:
            cmd["timeout"] = int(pos[2])
    elif action == "launch_godot":
        cmd["project"] = pos[0] if pos else "."
    elif action == "force_check":
        result = force_check()
        print(f"{'✅' if result else '❌'} HTTP 桥接: {'可用' if result else '不可用'}")
        return
    elif action == "ping":
        pass
    else:
        cmd["path"] = pos[0] if pos else "."

    # 尝试 HTTP（除非 --file），失败自动降级文件桥接
    result = send_command(cmd, prefer_http=not args.file)

    if result.get("ok"):
        if "stdout" in result:
            print(result["stdout"])
        elif "content" in result:
            print(result["content"])
        elif "message" in result:
            print(result["message"])
        elif "version" in result:
            print(result["version"])
        else:
            print("✅ 成功")
    else:
        print(f"❌ 失败: {result.get('error', '未知错误')}", file=sys.stderr)


if __name__ == "__main__":
    main()
