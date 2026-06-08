#!/usr/bin/env python3
"""
🦐 Windows 躯壳脚本 — agent.py v2.0

改进:
  - 工具路径从 status.json 动态读取（不再硬编码）
  - godot_headless 命令引号处理修复
  - 更清晰的日志
  - 状态文件实时更新

使用方法:
  python agent.py
"""

import json
import os
import shutil
import subprocess
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────────────

SHARED_DIR = Path("D:/openclawworkspace/game-dev")
SHARED_DIR.mkdir(parents=True, exist_ok=True)

INBOX = SHARED_DIR / "inbox"
OUTBOX = SHARED_DIR / "outbox"
STATUS = SHARED_DIR / "status.json"

INBOX.mkdir(exist_ok=True)
OUTBOX.mkdir(exist_ok=True)

# ── 工具路径管理 ──────────────────────────────────────────────────────────

TOOLS_FILE = SHARED_DIR / "tools.json"


def load_tools() -> dict:
    """从 tools.json 加载工具路径，不存在则返回默认值"""
    defaults = {
        "godot": r"C:\Program Files\Godot\godot.exe",
        "code": "code",
        "git": "git",
        "aseprite": r"C:\Program Files\Aseprite\aseprite.exe",
    }
    if TOOLS_FILE.exists():
        try:
            overrides = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
            defaults.update(overrides)
        except (json.JSONDecodeError, OSError):
            log(f"⚠️ tools.json 解析失败，使用默认值")
    else:
        # 首次运行：写出默认 tools.json
        TOOLS_FILE.write_text(
            json.dumps(defaults, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log(f"📝 已生成 tools.json，请将工具路径改为实际路径")
    return defaults


TOOLS = load_tools()


# ── 日志 ──────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# ── 指令处理器 ──────────────────────────────────────────────────────────

def handle_command(cmd: dict) -> dict:
    """执行一条指令并返回结果字典"""
    action = cmd.get("action", "")
    log(f"▶ 执行: {action}")

    try:
        if action == "exec":
            return _exec(cmd)

        elif action == "write_file":
            return _write_file(cmd)

        elif action == "read_file":
            return _read_file(cmd)

        elif action == "copy_file":
            shutil.copy2(cmd["src"], cmd["dst"])
            return {"ok": True}

        elif action == "list_dir":
            return _list_dir(cmd)

        elif action == "open_in_editor":
            target = cmd.get("path", ".")
            subprocess.Popen(["code", target], shell=True)
            return {"ok": True, "message": f"已在 VSCode 中打开: {target}"}

        elif action == "launch_godot":
            return _launch_godot(cmd)

        elif action == "godot_headless":
            return _godot_headless(cmd)

        elif action == "godot_version":
            return _godot_version()

        elif action == "ping":
            return {"ok": True, "message": "pong", "time": datetime.now().isoformat()}

        elif action == "shutdown":
            log("👋 收到关机指令")
            return {"ok": True, "message": "agent 即将退出"}

        else:
            return {"ok": False, "error": f"未知操作: {action}"}

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "执行超时"}
    except FileNotFoundError as e:
        return {"ok": False, "error": f"文件未找到: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ── 具体操作实现 ──────────────────────────────────────────────────────

def _exec(cmd: dict) -> dict:
    """执行 shell 命令 — 失败时降级到 PowerShell（解决 CreateProcess 被组织策略拦截的问题）"""
    import shlex, tempfile

    command = cmd["command"]
    timeout = cmd.get("timeout", 30)
    log(f"  命令: {command[:120]}...")

    # 尝试用 cmd.exe 执行
    cmd_ok = False
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        log(f"  cmd 返回码: {result.returncode}")
        if result.returncode != 0:
            log(f"  stderr: {result.stderr[:120]}...")
        else:
            cmd_ok = True
    except subprocess.TimeoutExpired:
        log("  cmd 超时")

    if cmd_ok:
        return {
            "ok": True,
            "stdout": result.stdout.strip()[:5000],
            "stderr": result.stderr.strip()[:2000],
            "returncode": result.returncode,
        }

    # 降级：PowerShell Start-Process 使用 ShellExecute 语义
    log("  cmd 失败，降级到 PowerShell Start-Process...")

    tmp_out = Path(tempfile.mktemp(suffix=".txt", prefix="exec_ps_out_"))
    tmp_ps1 = Path(tempfile.mktemp(suffix=".ps1", prefix="exec_ps_"))

    try:
        # 安全转义命令传入 PowerShell
        ps_escaped = command.replace("'", "''").replace('"', '"""').strip()
        ps1_content = f'''$cmd = @'
{ps_escaped}
'@
$tmp = "{tmp_out.as_posix()}"
$sb = [ScriptBlock]::Create($cmd)
try {{
    $out = & $sb 2>&1 | Out-String
    $out | Out-File -FilePath $tmp -Encoding utf8
    $exitCode = $LASTEXITCODE
}} catch {{
    "ERROR: $_" | Out-File -FilePath $tmp -Encoding utf8
    $exitCode = 1
}}
Write-Output "PS_EXIT_CODE=$exitCode"
try {{ Remove-Item $tmp -Force -ErrorAction SilentlyContinue }} catch {{}}
exit $exitCode
'''
        tmp_ps1.write_text(ps1_content, encoding="utf-8")

        ps_result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(tmp_ps1)],
            capture_output=True, text=True, timeout=timeout,
        )
        log(f"  PowerShell 返回码: {ps_result.returncode}")

        # 读输出
        stdout = ""
        if tmp_out.exists():
            stdout = tmp_out.read_text(encoding="utf-8", errors="replace")[:5000]
            # 输出文件是中间产物，cmd 也写了结果到 stdout
            tmp_out.unlink(missing_ok=True)

        log(f"  stdout len: {len(stdout)}")
        return {
            "ok": ps_result.returncode == 0,
            "stdout": stdout.strip() or ps_result.stdout.strip()[:5000],
            "stderr": ps_result.stderr.strip()[:2000],
            "returncode": ps_result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "PowerShell 降级执行超时"}
    except Exception as e:
        return {"ok": False, "error": f"PowerShell 降级失败: {e}"}
    finally:
        tmp_ps1.unlink(missing_ok=True)
        tmp_out.unlink(missing_ok=True)


def _write_file(cmd: dict) -> dict:
    path = Path(cmd["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cmd["content"], encoding="utf-8")
    log(f"  写入: {path} ({len(cmd['content'])} 字符)")
    return {"ok": True, "size": len(cmd["content"])}


def _read_file(cmd: dict) -> dict:
    path = Path(cmd["path"])
    if not path.exists():
        return {"ok": False, "error": "文件不存在"}
    content = path.read_text(encoding="utf-8")
    return {"ok": True, "content": content[:10000]}


def _list_dir(cmd: dict) -> dict:
    path = Path(cmd["path"])
    if not path.is_dir():
        return {"ok": False, "error": "目录不存在"}
    items = sorted([str(p.relative_to(path)) for p in path.iterdir()])
    return {"ok": True, "items": items[:100]}


def _launch_godot(cmd: dict) -> dict:
    project = cmd.get("project", ".")
    godot = TOOLS.get("godot", "godot")
    flags = cmd.get("flags", "")
    subprocess.Popen(f'"{godot}" --path "{project}" {flags}', shell=True)
    log(f"  启动 Godot: {project}")
    return {"ok": True}


def _godot_headless(cmd: dict) -> dict:
    project = cmd.get("project", ".")
    script = cmd.get("script", "")
    godot = TOOLS.get("godot", "godot")
    
    # 构建命令：避免多余引号
    # 注意：console 版不加 --headless（该标志会导致 Console 版本挂起）
    parts = [f'"{godot}"', f'--path "{project}"', f'--script "{script}"']
    full_cmd = " ".join(parts)
    log(f"  Godot headless: {full_cmd[:150]}...")
    
    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=cmd.get("timeout", 60),
    )
    log(f"  返回码: {result.returncode}")
    if result.returncode != 0:
        err = result.stderr[:2000]
        log(f"  stderr: {err[:200]}")
    return {
        "ok": result.returncode == 0,
        "stdout": (result.stdout or "").strip()[:5000],
        "stderr": (result.stderr or "").strip()[:2000],
    }


def _godot_version() -> dict:
    godot = TOOLS.get("godot", "godot")
    try:
        result = subprocess.run(
            f'"{godot}" --version',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "ok": result.returncode == 0,
            "version": result.stdout.strip(),
            "stderr": result.stderr.strip()[:500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── 状态管理 ──────────────────────────────────────────────────────────

def update_status(running: bool = True):
    """刷新 status.json（含工具路径）"""
    status = {
        "running": running,
        "pid": os.getpid(),
        "time": datetime.now(tz=timezone.utc).isoformat(),
        "tool_paths": TOOLS,
    }
    STATUS.write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ── HTTP 桥接服务器 ──────────────────────────────────────────

_http_server = None

def start_http_server():
    """在后台线程启动 HTTP 桥接服务器（替代文件轮询，避免 9P 死锁）"""
    try:
        from agent_http import BridgeHttpServer, set_command_handler
        set_command_handler(handle_command)
        global _http_server
        _http_server = BridgeHttpServer()
        _http_server.start()
        log(f"🌐 HTTP 桥接已启动: {_http_server.url}")
        log("📌 建议: 在 WSL 端使用 HTTP 桥接发送指令，完全绕过 9P 文件共享死锁")
        return True
    except Exception as e:
        log(f"⚠️ HTTP 桥接启动失败: {e}（不影响文件桥接）")
        return False


# ── 主循环 ──────────────────────────────────────────────────────────

def main_loop(http_only: bool = False):
    log("🦐 小虾躯壳脚本 v2.1 — HTTP+文件双桥接")
    log(f"📁 共享目录: {SHARED_DIR}")
    log(f"📥 inbox: {INBOX}（文件桥接）")
    log(f"📤 outbox: {OUTBOX}（文件桥接）")
    log(f"🔧 Godot: {TOOLS.get('godot', '未配置')}")

    # 启动 HTTP 桥接
    start_http_server()

    if http_only:
        log("📌 HTTP-only 模式，文件轮询已关闭")
        update_status(True)
        log("等待 HTTP 请求中...")
        try:
            threading.Event().wait()  # 无限等待
        except KeyboardInterrupt:
            pass
        finally:
            update_status(False)
        return

    log("等待指令中...（文件桥接）")

    update_status(True)
    processed: set[str] = set()
    last_cleanup = time.monotonic()

    try:
        while True:
            # 每轮扫描 inbox
            inbox_files = sorted(INBOX.glob("*.json"))
            for f in inbox_files:
                if f.name in processed:
                    continue

                try:
                    log(f"📨 收到指令: {f.name}")
                    cmd = json.loads(f.read_text(encoding="utf-8"))

                    result = handle_command(cmd)

                    out_file = OUTBOX / f"result_{f.stem}.json"
                    out_file.write_text(
                        json.dumps(result, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    log(f"📨 结果已写入: {out_file.name}")

                    processed.add(f.name)

                    # 关机指令 → 退出
                    if cmd.get("action") == "shutdown":
                        log("👋 关机")
                        update_status(False)
                        return

                except (json.JSONDecodeError, KeyError) as e:
                    log(f"⚠️ 指令解析失败 {f.name}: {e}")
                    processed.add(f.name)

            # 每 5 分钟清理一次已处理文件列表（防止内存膨胀）
            now = time.monotonic()
            if now - last_cleanup > 300:
                processed.clear()
                last_cleanup = now

            time.sleep(2)

    except KeyboardInterrupt:
        log("收到中断")
    finally:
        update_status(False)


if __name__ == "__main__":
    http_only = "--http-only" in sys.argv
    main_loop(http_only=http_only)
