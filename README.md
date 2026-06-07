<p align="center">
  <img src="docs/logo.png" alt="游刃" width="128" />
</p>

<h1 align="center">游刃 · Youren</h1>

<p align="center">
  <em>AI-native game development toolkit — LLM + WSL ↔ Windows ↔ Godot</em>
</p>

<p align="center">
  <a href="#english">English</a> ·
  <a href="#chinese">中文</a>
</p>

---

<a name="chinese"></a>

# 游刃 — AI 原生游戏开发工具包

> 游刃有余，庖丁解牛。
>
> 出自《庄子·养生主》 — 在复杂中游刃有余。

## 这是什么

**游刃** 是一个 AI 原生游戏开发工具包，让大语言模型（LLM）能直接驱动 Godot 引擎开发游戏。

### 架构

```
┌─────────────────────────────────────────────────┐
│                 LLM (你的 AI 大脑)                │
│  写 GDScript · 设计游戏架构 · 生成配置 · 跑测试   │
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────▼────────┐
              │   WSL / Linux    │
              │  (代码生成层)     │
              └────────┬────────┘
                       │ 文件桥接 (inbox/outbox)
              ┌────────▼────────┐
              │   agent.py       │
              │  (Windows 躯壳)   │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   Godot 4.x      │
              │  · 构建 & 导出    │
              │  · headless 测试  │
              │  · 资源处理       │
              └─────────────────┘
```

**核心价值：** LLM 写游戏代码 → 通过桥接存盘 → Godot 编译/测试 → 人工验收。全部在本地完成，零第三方 API 依赖，数据不出本机。

## 功能

- ✅ **GDScript 代码生成** — LLM 直接写游戏逻辑
- ✅ **一键构建** — `./build.sh` 跨 WSL→Windows 执行 Godot 导出
- ✅ **自动化测试** — Godot headless 模式运行 29+ 项单元测试
- ✅ **模板系统** — 从空间射击模板开始新建游戏项目
- ✅ **WSL↔Windows 桥** — 唯一公开的 WSL + Windows + Godot 交叉工作流
- ✅ **数据不出本机** — 本地优先，零持续成本

## 快速开始

### 前置条件

- **Windows** 10/11 已安装：
  - [Godot 4.x](https://godotengine.org/download/windows/) (下载 **Console 版**)
  - [Python 3.8+](https://www.python.org/downloads/)
- **WSL** (Ubuntu 推荐) — WSL2 已启用
- **Git**

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/youren.git
cd youren

# 2. 配置工具路径
cp agent/tools.example.json agent/tools.json
# 编辑 tools.json，填入 Godot 实际路径

# 3. 启动 Windows 躯壳
# 在 Windows 上运行:
python agent/agent.py

# 4. 运行测试确认一切正常
cd templates/space-shooter
# WSL 端:
./build.sh --test
# 或 Windows 端:
run_tests.bat
```

### 工具路径配置 (`tools.json`)

```json
{
    "godot": "E:\\godot\\Godot_v4.6-stable_win64_console.exe",
    "code": "code"
}
```

> **注意：** 如果 Godot 的 zip 解压后是一个目录（例如 `Godot_v4.6-stable_win64.exe\`），路径应为：
> ```
> E:\godot\Godot_v4.6-stable_win64.exe\Godot_v4.6-stable_win64_console.exe
> ```

## 项目结构

```
youren/
├── agent/                    # Windows 躯壳脚本
│   ├── agent.py              # 主代理（轮询 inbox/outbox）
│   ├── tools.example.json    # 工具路径配置示例
│   └── protocol.md           # 通信协议文档
├── templates/                # Godot 游戏模板
│   ├── space-shooter/        # 🚀 空间射击 demo
│   │   ├── scripts/          # GDScript 源代码
│   │   ├── scenes/           # Godot 场景
│   │   ├── tests/            # 单元测试 (29 项)
│   │   ├── assets/           # 资源文件 (Kenney)
│   │   ├── build.sh          # WSL 端构建
│   │   └── build.bat         # Windows 端构建
│   └── 2d-template/          # 通用 2D 游戏模板
├── docs/                     # 文档
│   ├── architecture.md       # 架构详解
│   ├── quickstart.md         # 快速开始
│   ├── bridge-protocol.md    # 桥接协议规范
│   └── template-guide.md     # 模板使用指南
├── build/                    # 构建工具
│   └── setup.sh              # 一键部署
├── LICENSE                   # MIT
└── README.md                 # 本文件
```

## 测试

```bash
cd templates/space-shooter

# Windows 端（推荐）
run_tests.bat

# WSL 端（通过桥接）
./build.sh --test
```

测试覆盖：分数管理、生命管理、敌人生成、波次逻辑、伤害系统。

## 模板使用

创建新项目：

```bash
cp -r templates/2d-template my-new-game
cd my-new-game
# 编辑 project.godot，开始开发！
```

详见 [模板指南](docs/template-guide.md)。

## 常见问题

**Q: 为什么不用云端 SaaS？**
A: 本地运行 = 零持续成本 + 数据不出本机 + 可离线

**Q: 必须用 WSL 吗？**
A: 当前推荐 WSL2 + Ubuntu，因为大多数 LLM 工具链在 Linux 上更成熟。macOS/Linux 原生用户可以直接运行 agent。

**Q: 为什么 Windows 上要跑 agent.py？**
A: Godot 导出、构建和 headless 测试需要 Windows 原生环境。agent.py 是 LLM 大脑的"躯壳"。

## 技术栈

| 组件 | 工具 |
|------|------|
| 游戏引擎 | Godot 4.x (GDScript) |
| 桥接代理 | Python 3 |
| LLM 大脑 | 任意 LLM (OpenClaw, Ollama, OpenAI…) |
| 操作系统 | WSL2 (Ubuntu) + Windows 10/11 |
| 版本管理 | Git |
| 资源工具 | Aseprite / Blender / ffmpeg (可选) |

## 许可

MIT License © 2026 GameWeaver

## 致谢

- [Kenney](https://kenney.nl) — 太空射击素材 (CC0)
- Godot 社区 — 优秀的开源游戏引擎

---

<a name="english"></a>

# Youren — AI-Native Game Development Toolkit

> *"Youren" (游刃) — to handle a butcher's cleaver with effortless skill.
> From Zhuangzi's classic, meaning to move freely and masterfully through complexity.*

## What is this

**Youren** is an AI-native game development toolkit that bridges LLMs with the Godot engine. It lets your AI assistant write, build, test, and iterate on games — entirely on your local machine.

## Architecture

```
LLM Brain (WSL/Linux) → JSON Bridge → agent.py (Windows) → Godot 4.x
```

## Quick Start

See [中文快速开始](#步骤) above.

## Features

- **AI-Assisted GDScript Generation** — Let your LLM write game logic
- **One-Click Build** — WSL→Windows bridge for Godot exports
- **Automated Testing** — 29+ unit tests running in Godot headless
- **Template System** — Start new projects from battle-tested templates
- **Local-First** — Zero API costs, data never leaves your machine

## License

MIT — do whatever you want, just don't sue us.
