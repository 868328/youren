# 桥接协议规范 v2

游刃使用文件桥接协议实现 WSL ↔ Windows 之间的异步通信。

## 目录结构

```
game-dev/
├── inbox/          # WSL → Windows 指令
│   └── {id}.json
├── outbox/         # Windows → WSL 结果
│   └── result_{id}.json
├── tools.json      # 工具路径配置
└── status.json     # agent.py 运行状态
```

## 指令格式

每个指令是一个 JSON 文件，写入 `inbox/{uuid}.json`。

```json
{
    "action": "exec",
    "command": "...",
    "timeout": 30
}
```

## 支持的操作

| 操作 | 描述 |
|------|------|
| `exec` | 执行任意 shell 命令 |
| `write_file` | 写入文件 |
| `read_file` | 读取文件 |
| `copy_file` | 复制文件 |
| `list_dir` | 列出目录 |
| `godot_headless` | Godot headless 运行脚本 |
| `godot_version` | 检查 Godot 版本 |
| `ping` | 连通性测试 |
| `shutdown` | 关闭 agent |

## 结果格式

```json
{
    "ok": true,
    "stdout": "...",
    "stderr": "",
    "returncode": 0
}
```

## 协议细节

### exec 操作

```json
{
    "action": "exec",
    "command": "E:\\godot\\Godot_v4.6-stable_win64_console.exe --version",
    "timeout": 15
}
```

### godot_headless 操作

```json
{
    "action": "godot_headless",
    "project": "D:\\project\\space-shooter",
    "script": "res://tests/run_tests.gd",
    "timeout": 60
}
```

> **注意:** Godot Console 版使用时**不能加 `--headless`** 标志。Console 版本身就是非 GUI 运行，加 `--headless` 会导致挂起。

### tools.json 配置

```json
{
    "godot": "E:\\godot\\Godot_v4.6-stable_win64_console.exe",
    "code": "code",
    "git": "git"
}
```

> **Windows 安全提示:** 如果 `subprocess.run()` 通过 `cmd.exe` 调用时被组织策略拒绝（CreateProcess 被限制），使用 Console 版 Godot + `capture_output=True` 可绕过。GUI 版 Godot 的 stdout 无法被管道捕获。

## 通信流程

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

## 超时

- 默认超时: 30 秒
- Godot 测试/构建: 60-120 秒
- Agent 轮询间隔: 2 秒
- 最大等待超时: 120 秒

## 错误处理

- 命令解析失败 → 跳过该文件（标记 processed）
- 执行超时 → 返回 `{ "ok": false, "error": "执行超时" }`
- 未知操作 → 返回 `{ "ok": false, "error": "未知操作: xxx" }`
- 所有异常被捕获并返回错误信息
