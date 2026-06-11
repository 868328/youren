# 桥接协议规范 v3

游刃使用**双桥接协议**实现 WSL ↔ Windows 之间的异步通信：

1. **HTTP 桥接（主通道）** — 通过本地 TCP 端口通信，完全绕过共享文件系统（**避免 9P 死锁**）
2. **文件桥接（fallback）** — 通过共享目录 inbox/outbox 通信，HTTP 不可用时自动降级

---

## 1. HTTP 桥接（主通道）

### 原理

Windows 端的 agent.py 在后台启动 HTTP 服务器（默认 `0.0.0.0:9876`），WSL 端通过 `http://<Windows-Host-IP>:9876/` 发送 JSON 指令。

> **WSL2 注意事项：** WSL2 有独立的虚拟网络，`127.0.0.1` 在 WSL2 中指 WSL 自己，不是 Windows。
> 必须使用 Windows 主机在 WSL2 网络中的 IP 地址（通常为默认网关 `172.x.x.1`）才能访问。
> WSL 侧客户端 (`windows_bridge.py`) 会自动通过 `ip route` 检测此 IP。

> **Windows Firewall：** HTTP 服务器绑定到 `0.0.0.0`，需确保 Windows Defender 防火墙放行端口 9876。
> 建议限制到 WSL2 子网：
> ```powershell
> netsh advfirewall firewall add rule name="游刃 HTTP Bridge (WSL2)" dir=in action=allow protocol=TCP localport=9876 remoteip=172.27.80.0/20
> ```

```
WSL (Linux)                        Windows
    │                                  │
    │  POST /  {"action":"exec",...}   │
    │─────────────────────────────────→│  HTTP 服务器 (:9876)
    │                                  │  → handle_command()
    │←─────────────────────────────────│  {"ok":true, "stdout":"..."}
    │  200 OK  JSON 响应               │
```

### 优势

| 对比 | 文件桥接 | HTTP 桥接 |
|------|---------|----------|
| **延迟** | 4-6 秒（2s 轮询 × 2） | ~5 毫秒 |
| **死锁风险** | ⚠️ 9P 文件系统可能死锁 | ✅ 纯 TCP，无文件系统依赖 |
| **依赖** | 无 | 无（纯 stdlib） |
| **可靠性** | 文件锁竞争 | 可靠 |
| **WSL2 兼容** | ✅ | ✅ `localhost` 直通 |

### API 端点

#### `POST /` — 执行指令

**请求体 (JSON):**
```json
{
    "action": "exec",
    "command": "E:\\godot\\Godot_v4.6-stable_win64_console.exe --version",
    "timeout": 30
}
```

**响应体 (JSON):**
```json
{
    "ok": true,
    "stdout": "4.6",
    "stderr": "",
    "returncode": 0
}
```

#### `GET /health` — 健康检查

```json
{
    "ok": true,
    "status": "running",
    "time": "2026-06-08T09:00:00"
}
```

### 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 监听地址 | `0.0.0.0` | 所有网络接口（WSL2 需要） |
| 端口 | `9876` | HTTP 端口 |
| 超时 | 30 秒 | 请求超时 |

> 端口 9876 可通过 `agent.py --port 9877` 修改。
> 监听地址可通过 `agent.py --host 127.0.0.1` 限制到本机（WSL2 无法访问）。

---

## 2. 文件桥接（fallback）

仅在 HTTP 桥接不可用时自动降级使用。

### 目录结构

```
game-dev/
├── inbox/          # WSL → Windows 指令
│   └── {id}.json
├── outbox/         # Windows → WSL 结果
│   └── result_{id}.json
├── tools.json      # 工具路径配置
└── status.json     # agent.py 运行状态
```

### 通信流程

```
LLM (WSL)                    agent.py (Windows)
    │                              │
    ├── 写 inbox/cmd.json ────────→│
    │                              ├── 读取 JSON
    │                              ├── 执行操作
    │                              ├── 写 outbox/result.json
    │←───── 读 outbox/result.json ─┤
    │                              │
    ├── 清理 result.json ──────────│
    │                              │
```

---

## 3. 支持的操作

| 操作 | 描述 | HTTP | 文件 |
|------|------|:----:|:----:|
| `exec` | 执行任意 shell 命令 | ✅ | ✅ |
| `write_file` | 写入文件 | ✅ | ✅ |
| `read_file` | 读取文件 | ✅ | ✅ |
| `copy_file` | 复制文件 | ✅ | ✅ |
| `list_dir` | 列出目录 | ✅ | ✅ |
| `launch_godot` | 启动 Godot 编辑器 | ✅ | ✅ |
| `godot_headless` | Godot headless 运行脚本 | ✅ | ✅ |
| `godot_version` | 检查 Godot 版本 | ✅ | ✅ |
| `ping` | 连通性测试 | ✅ | ✅ |
| `shutdown` | 关闭 agent | ✅ | ✅ |

### 指令格式

所有操作使用统一 JSON 格式：

```json
{
    "action": "<操作名>",
    "timeout": 30,
    // 操作相关参数...
}
```

### 结果格式

```json
{
    "ok": true,
    // 成功时:
    "stdout": "...",       // exec 操作
    "stderr": "...",
    "returncode": 0,
    "content": "...",      // read_file 操作
    "message": "...",      // 其他操作
    // 失败时:
    "error": "错误描述"
}
```

---

## 4. 双桥接自动降级

### 优先级

```
HTTP 桥接 → 可用? → 是 → 使用 HTTP
                ↓ 否
         文件桥接 (fallback)
```

### 检测逻辑

1. 首次调用时尝试 HTTP `GET /health`
2. 成功 → 标记 HTTP 可用，后续请求走 HTTP
3. 失败 → 降级到文件桥接，标记 HTTP 不可用
4. 可通过 `force_check` 手动重试 HTTP

### 超时

| 场景 | 默认超时 |
|------|---------|
| HTTP 请求 | 30 秒 |
| 文件桥接轮询 | 30 秒（每 2s 轮询一次） |
| Godot 测试/构建 | 60-120 秒 |
| 健康检查 | 5 秒 |

---

## 5. 文件列表

| 文件 | 位置 | 说明 |
|------|------|------|
| `agent/agent.py` | Windows | 躯壳脚本 v2.1，启动 HTTP+文件双桥接 |
| `agent/agent_http.py` | Windows | HTTP 桥接服务器（零依赖） |
| `infra/bridge-client/windows_bridge.py` | WSL | HTTP 客户端 + 文件 fallback |
| `.agent/tools/send_to_windows.py` | WSL | CLI 工具（HTTP 优先） |
| `.agent/tools/windows.py` | WSL | 工具类（HTTP 优先） |

---

## 6. 快速开始

### Windows 端

```bash
cd agent
python agent.py
# 输出:
# 🦐 小虾躯壳脚本 v2.1 — HTTP+文件双桥接
# 🌐 HTTP 桥接已启动: http://0.0.0.0:9876
```

HTTP-only 模式（不启动文件轮询）:
```bash
python agent.py --http-only
```

### WSL 端

```bash
# 测试连接
python3 ~/projects/youren/infra/bridge-client/windows_bridge.py ping

# 执行命令
python3 ~/projects/youren/infra/bridge-client/windows_bridge.py exec "dir C:\\"

# 检查桥接状态
python3 ~/.agent/tools/send_to_windows.py force_check
```
