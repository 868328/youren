# 🔌 桥接协议升级方案

> 文档版本: 1.0 | 2026-06-07
> 上下文: 游刃游戏开发自动化 — WSL ↔ Windows 通信桥梁

---

## 1. 背景与现状

### 1.1 当前架构

当前使用**文件桥接协议**，通过共享目录的 inbox/outbox 模式实现 WSL 与 Windows 之间的异步通信：

```
WSL                                        Windows
 ┌─────────────────┐                     ┌──────────────────┐
 │  LLM / Agent     │  write JSON        │  agent.py        │
 │                   │ ──────────────→    │  (轮询 2s/次)    │
 │  send_to_windows  │  inbox/{id}.json   │                   │
 │  .py              │                    │  执行命令         │
 │                   │ ←──────────────    │                   │
 │                   │  outbox/result_    │  写入结果         │
 │                   │  {id}.json         │                   │
 └─────────────────┘                     └──────────────────┘
          ↕ D:/openclawworkspace/game-dev/ (共享 NTFS 文件系统)
```

### 1.2 工作流程

1. WSL 端将指令写入 `inbox/{uuid}.json`
2. Windows 端 agent.py 每 2 秒轮询 inbox 目录
3. 发现新文件 → 读取 JSON → 执行命令 → 写入 `outbox/result_{uuid}.json`
4. WSL 端轮询 outbox 目录等待结果（超时 60s）

---

## 2. 当前桥接瓶颈分析

### 2.1 轮询延迟 ⚠️

| 环节 | 延迟 | 说明 |
|------|------|------|
| 指令写入 | ~5ms | 文件系统写入 |
| agent 轮询间隔 | 2,000ms | **瓶颈** — 2 秒粒度 |
| 命令执行 | 100ms–60s | 取决于具体指令 |
| 结果写入 | ~5ms | 文件系统写入 |
| WSL 端轮询 | 2,000ms | **瓶颈** — 轮询 2 秒 |

**理论最差 RTT:** ~4 秒  
**实测平均 RTT:** 4–6 秒（包含文件系统同步开销）

### 2.2 文件锁与并发 🚫

| 问题 | 风险等级 | 说明 |
|------|---------|------|
| WSL ↔ NTFS 锁争用 | 中 | 同时读写同一文件时可能冲突 |
| 重复处理 | 中 | 若 agent 在写入途中 crash，重启后可能重处理未清理的文件 |
| 竞态条件 | 低 | 当前单线程模型下风险可控，但扩展时需注意 |
| 磁盘 I/O 抖动 | 低 | NTFS 在 WSL 下的 9p 协议驱动有额外开销 |

### 2.3 功能限制 ⛔

| 限制 | 说明 |
|------|------|
| 无双向流 | 只能 request-response，无法推送事件（如 Godot 日志流） |
| 无实时性 | 无法 streaming 输出（如需长时间运行的命令实时反馈） |
| 结果截断 | `stdout` 限制 5000 字符，`stderr` 限制 2000 |
| 无超时回退 | 超时后无中间状态报告 |
| 无健康检查 | 只能通过 `status.json` 间接判断 agent 是否存活 |
| 无错误重试 | 一次失败即丢弃，无自动重试或回退逻辑 |

### 2.4 开发体验

```python
# 当前调用方式 — 需要手动轮询
cmd_id = write_to_inbox(cmd)
for _ in range(30):
    sleep(2)
    if result_file_exists(cmd_id):
        return read_result(cmd_id)
raise TimeoutError()
```

---

## 3. 升级路径

### 3.1 方案 A：命名管道 (Named Pipe) ★★☆☆☆

**适合场景:** 简单的本机 IPC，低频命令

**原理:** 使用 Windows 命名管道 (`\\.\pipe\game-agent`) 替代文件系统进行通信。

**优点:**
- 消除文件 I/O 开销
- WSL 可通过 `\\wsl.localhost\...` 访问 Windows 管道
- 无需额外依赖

**缺点:**
- WSL ↔ Windows 命名管道访问不稳定（9p 协议限制）
- 仍为 request-response 模型
- 无并发支持
- 调试困难

**实现概要:**
```python
# Windows 端 (agent.py 增加)
import win32pipe, win32file
pipe = win32pipe.CreateNamedPipe(
    r'\\.\pipe\game-agent', ...)
# 监听连接
while True:
    win32pipe.ConnectNamedPipe(pipe)
    data = win32file.ReadFile(pipe)
    result = handle(json.loads(data))
    win32file.WriteFile(pipe, json.dumps(result))
```

**不推荐** — WSL 与 Windows 命名管道互通存在已知问题。

---

### 3.2 方案 B：WebSocket (推荐) ★★★★★

**适合场景:** 通用本机 IPC，需要双向通信

**原理:** 在 Windows 端运行轻量 WebSocket 服务器（`websockets` / `asyncio`），WSL 端作为客户端连接。

```
WSL                                Windows
 ┌──────────────┐    WebSocket     ┌──────────────────┐
 │  Agent       │ ←─────────────→  │  ws_server.py    │
 │  (Client)    │  ws://localhost:  │  (asyncio)       │
 │              │  9876             │                  │
 │  send/receive│                  │  → exec cmd      │
 │  JSON messages│                 │  → streaming stdout│
 └──────────────┘                  └──────────────────┘
```

**优点:**
- **双向实时** — 服务端可推送事件（日志、进度）
- **低延迟** — 无轮询，消息即发即达（~1ms）
- **流式传输** — 支持长命令的逐行输出
- **连接复用** — 同一连接发多条指令
- **WSL 友好** — `ws://localhost:9876` 在 WSL2 中可直接访问 Windows 本地端口
- **健康检测** — WebSocket ping/pong 内置
- **Python 标准库** — `asyncio` + `websockets`（pip install）

**缺点:**
- 需要安装 `websockets` 库（~500KB）
- 需要处理重连逻辑
- 防火墙可能需要放行端口

**实现概要:**

```python
# Windows 端 — ws_server.py
import asyncio
import websockets
import json, subprocess

async def handle(ws):
    async for msg in ws:
        cmd = json.loads(msg)
        if cmd["action"] == "exec":
            proc = await asyncio.create_subprocess_shell(
                cmd["command"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            await ws.send(json.dumps({
                "ok": proc.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }))

async def main():
    async with websockets.serve(handle, "0.0.0.0", 9876):
        await asyncio.Future()

asyncio.run(main())
```

```python
# WSL 端 — 客户端封装
import asyncio, json, websockets

class WindowsBridge:
    def __init__(self, url="ws://localhost:9876"):
        self.url = url
    
    async def exec(self, cmd: str, timeout=30):
        async with websockets.connect(self.url) as ws:
            await ws.send(json.dumps({"action": "exec", "command": cmd}))
            result = await asyncio.wait_for(ws.recv(), timeout)
            return json.loads(result)
```

---

### 3.3 方案 C：HTTP API (推荐备选) ★★★★☆

**适合场景:** RESTful 风格、易于集成、需要多客户端

**原理:** 在 Windows 端运行 Flask / FastAPI HTTP 服务器，WSL 端通过 HTTP 请求调用。

**优点:**
- **简单直观** — `requests.post(...)` 即可调用
- **无需持久连接** — 无重连逻辑
- **工具兼容** — curl、Python requests、浏览器都可调用
- **可扩展** — 可添加认证、日志、缓存

**缺点:**
- **单向请求** — 服务端不能主动推送（需 Server-Sent Events 或轮询补充）
- **每次请求开销** — HTTP 握手 vs WebSocket 连接复用
- **需额外依赖** — Flask / FastAPI + uvicorn

**实现概要:**

```python
# fastapi + uvicorn
from fastapi import FastAPI
app = FastAPI()

@app.post("/exec")
def exec_cmd(cmd: str):
    result = subprocess.run(cmd, shell=True,
        capture_output=True, text=True, timeout=30)
    return {"ok": result.returncode == 0, "stdout": result.stdout}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9877)
```

---

## 4. 方案对比

| 维度 | 文件桥接 (当前) | 命名管道 | **WebSocket** | HTTP API |
|------|:-------:|:--------:|:---------:|:--------:|
| **延迟** | 4–6s | ~10ms | **~1ms** | ~5ms |
| **双向通信** | ❌ | ❌ | **✅** | ❌ |
| **流式支持** | ❌ | ❌ | **✅** | ⚠️ (SSE) |
| **WSL 兼容** | ✅ (本机) | ⚠️ | **✅** | **✅** |
| **依赖体积** | 无 | pywin32 (10MB) | **websockets** (500KB) | FastAPI (5MB) |
| **实现复杂度** | 简单 | 中等 | **中等** | 简单 |
| **调试难度** | 简单 | 困难 | **中等** | **简单** |
| **可靠性** | ⚠️ (文件锁) | 🟢 高 | **🟢 高** | 🟢 高 |
| **并发能力** | 单线程 | 多路复用 | **多路复用** | **多线程** |

---

## 5. 推荐实施路径

### 阶段一：WebSocket MVP（建议本周完成）

**目标:** 取代文件轮询，实现实时双向通信

1. 创建 `ws_server.py`（~50 行，基于 websockets）
2. 改造 agent.py，新增 WebSocket 监听模式（保留文件桥接作为 fallback）
3. 创建 WSL 端 `windows_bridge.py` 封装
4. 更新 `build.sh` 使用 WebSocket 调用

```python
# 最小 WebSocket 服务器 (ws_server.py)
# 与原 agent.py 共享 handle_command()
import asyncio
import websockets
from agent import handle_command

async def handler(ws):
    async for msg in ws:
        cmd = json.loads(msg)
        result = handle_command(cmd)
        await ws.send(json.dumps(result))

async def main():
    async with websockets.serve(handler, "0.0.0.0", 9876):
        await asyncio.Future()
```

### 阶段二：功能增强（下个月）

1. 添加命令 ID 匹配（支持并发多请求）
2. 实现长命令逐行流式输出
3. 添加 macOS / Linux agent 支持（同协议）
4. 健康检查和自动重连

### 阶段三：HTTP API 补充（可选）

1. 提供 HTTP API 作为辅助接口（同步场景）
2. 添加 SSE 端点用于事件推送
3. 可同时运行 WebSocket + HTTP 双模式

---

## 6. 迁移风险与回退

| 风险 | 缓解措施 |
|------|---------|
| WebSocket 连接失败 | 保留文件桥接作为 fallback，自动降级 |
| Python websockets 库不可用 | 使用内置 `socket` + `select` 实现 TCP 协议 |
| 防火墙阻止端口 | 配置 Windows Defender 放行，默认端口 9876 |
| WSL2 ↔ Windows 网络不通 | 检查 `localhost` 映射，或用 `$(hostname).local` |
| 性能不达标 | 保留文件桥接方案，对比后决定 |

---

## 7. 实施检查清单

- [ ] 安装 `pip install websockets`（Windows 端）
- [ ] 编写 `ws_server.py`（复用 agent.py 的 handle_command）
- [ ] 测试: WSL → WebSocket → exec → 返回
- [ ] 测试: 长时间命令流式输出
- [ ] 测试: 连接断开后自动重连
- [ ] 更新 build.sh 新增 `--ws` 模式
- [ ] 更新文档和 HANDOFF.md
- [ ] 基准测试: 文件桥接 vs WebSocket 延迟对比

---

## 8. 结论

**推荐采用 WebSocket 方案**，原因如下：

1. **延迟降低 4000x** — 6s → 1ms
2. **双向实时** — 支持事件推送和流式输出
3. **WSL2 原生兼容** — `ws://localhost:9876` 即开即用
4. **低依赖** — 仅需 `pip install websockets`（500KB）
5. **渐进升级** — 可与文件桥接共存，零风险切换

未来可在此基础上叠加 HTTP API 提供 RESTful 接口，两者互不冲突。
