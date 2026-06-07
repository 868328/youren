# 游刃架构

## 总体架构

```
┌────────────────────────────────────────────────────────────┐
│                     LLM (大脑层)                           │
│  写 GDScript · 设计游戏架构 · 生成场景 · 编写测试          │
│  通过文件桥接协议向 Windows 发送指令                        │
└──────────┬─────────────────────────────────────────────────┘
           │  JSON 文件协议 (inbox/outbox)
           │  /mnt/d/openclawworkspace/game-dev/
           ▼
┌────────────────────────────────────────────────────────────┐
│                agent.py (Windows 躯壳层)                   │
│  轮询 inbox 目录 → 执行命令 → 写回结果到 outbox            │
│                                                           │
│  支持的指令: exec / write_file / read_file / godot_headless│
│            godot_version / launch_godot / ping / shutdown  │
└──────────┬─────────────────────────────────────────────────┘
           │
           ├──→ Godot 4.x (游戏引擎)
           ├──→ 文件系统 (项目文件读写)
           ├──→ Git / Aseprite / Blender (可选工具)
           └──→ 命令行 (任意 shell 命令)
```

## 分层职责

### 大脑层 (LLM)
- **在哪运行:** WSL / Linux / 任何 Python 环境
- **做什么:** 理解需求、生成代码、设计架构、写测试
- **不做什么:** 不直接与 Windows 工具交互、不直接启动 Godot

### 躯壳层 (agent.py)
- **在哪运行:** Windows (原生)
- **做什么:** 文件操作、Godot 执行、shell 命令、构建导出
- **不做什么:** 不做设计决策、不写业务代码

### 引擎层 (Godot)
- **在哪运行:** Windows (原生)
- **做什么:** 编译 GDScript、运行游戏、导出 exe、跑测试
- **不做什么:** 不写代码、不做设计

## 数据流

```
LLM 决策写代码
    │
    ▼
写 .gd 文件到项目目录
    │
    ▼
agent.py 接收指令 → Godot headless 编译/测试
    │
    ▼
结果写回 → LLM 读结果 → 迭代
```

## 关键设计决策

1. **文件桥接而非 WebSocket/HTTP** — 简单、可靠、零依赖。文件就是消息队列
2. **JSON 格式而非 protobuf** — 人类可读、LLM 可直接生成和解析
3. **异步轮询而非推送** — 避免网络配置、防火墙问题。2 秒间隔足够
4. **agent.py 单线程** — 简单可靠。阻塞操作自然成为"一次一个命令"的同步
5. **Windows 做躯壳，WSL 做大脑** — WSL 上 LLM 工具链成熟，Windows 上 Godot 原生

## 升级路线

```
当前: 文件桥接 (inbox/outbox JSON)
    │
  下一步: 命名管道 (Windows Named Pipe)
    │
  最终: WebSocket / 本地 HTTP API
```
