#!/usr/bin/env python3
"""
🌐 agent_http.py — HTTP 桥接服务器

为 WSL↔Windows 通信提供 HTTP API，完全绕过共享文件系统（避免 9P 死锁）。
零外部依赖，仅用 Python 标准库。

与 agent.py 集成：agent.py 在后台线程启动此服务器。

使用方法（独立运行）:
    python agent_http.py --port 9876

API:
    POST /  — JSON body: {"action": "...", ...}
              JSON response: {"ok": true/false, ...}

    GET  /health — 健康检查
"""

import json
import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

logger = logging.getLogger("agent.http")

# 默认端口
DEFAULT_PORT = 9876

# 命令处理器引用（由 agent.py 注入）
_command_handler = None


def set_command_handler(handler):
    """注入命令处理器函数"""
    global _command_handler
    _command_handler = handler


# ── HTTP 请求处理器 ──────────────────────────────────────────────

class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP API 请求处理"""

    # 关闭默认日志（用 agent 自己的日志）
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        """CORS preflight"""
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "ok": True,
                "status": "running",
                "time": datetime.now().isoformat(),
            })
        else:
            self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            cmd = json.loads(body)

            if _command_handler is None:
                self._send_json(503, {
                    "ok": False,
                    "error": "命令处理器未初始化（agent.py 未完全启动）",
                })
                return

            result = _command_handler(cmd)
            self._send_json(200, result)

        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "error": "无效的 JSON"})
        except Exception as e:
            self._send_json(500, {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
            })


# ── HTTP 服务器 ──────────────────────────────────────────────

class BridgeHttpServer:
    """HTTP 桥接服务器封装"""

    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self._server = None
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}"

    def start(self):
        """在后台线程启动 HTTP 服务器"""
        self._server = HTTPServer((self.host, self.port), BridgeHandler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="http-bridge",
        )
        self._thread.start()
        logger.info(f"🌐 HTTP 桥接已启动: {self.url}")
        return True

    def stop(self):
        """关闭服务器"""
        if self._server:
            self._server.shutdown()
            self._server = None
            logger.info("🌐 HTTP 桥接已停止")
            return True
        return False

    def is_running(self):
        return self._server is not None


# ── 独立运行 ──────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="游刃 HTTP 桥接服务器")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"监听端口（默认 {DEFAULT_PORT}）")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 独立运行模式，注入一个简单的命令处理器
    def dummy_handler(cmd):
        from agent import handle_command
        return handle_command(cmd)

    set_command_handler(dummy_handler)

    server = BridgeHttpServer(host=args.host, port=args.port)
    server.start()
    logger.info(f"🦐 HTTP 桥接服务器运行中: {server.url}")
    logger.info("按 Ctrl+C 停止")

    try:
        threading.Event().wait()  # 无限等待
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        logger.info("服务器已关闭")


if __name__ == "__main__":
    main()
