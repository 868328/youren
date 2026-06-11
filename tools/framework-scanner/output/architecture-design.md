# 🦐 小虾副脑 2.0 — 架构设计书

> 基于 Claude Code、Cline、LangGraph、OpenClaw 四框架分析
> 编写于 2026-06-10

---

## 一、现状与目标

### 现状 (1.0)

`.agent/` 已经有一个可工作的框架：

| 子系统 | 状态 | 说明 |
|--------|------|------|
| brain/ | ✅ | 多后端抽象：OpenClaw/Ollama/OpenAI，可切换 |
| tools/ | ✅ | 工具注册 + 自动发现，14 个工具可运行 |
| memory/ | ✅ | 文件记忆 + 索引，与 OpenClaw 共享 |
| plugins/ | ✅ | 动态插件加载 |
| daemon/ | ✅ | 守护进程 + 调度器 |

问题：
- **工具定义不够规范** — 没有 JSON Schema 强约束，description 随意
- **没有 MCP 兼容层** — 无法接入生态工具
- **记忆只有文件层** — 没有向量检索或结构化存储
- **执行模型弱** — 没有 session/checkpoint，没有上下文窗口管理
- **安全模型空白** — 没有权限分层

### 目标 (2.0)

不依赖 OpenClaw 也能完全自主运行，同时保留 OpenClaw 作为"可选宿主"。

核心原则：
1. **模块可替换** — 每个子系统都能独立升级/替换
2. **MCP 兼容** — 能消费和提供 MCP 工具
3. **本地优先** — 零 API 成本也能跑
4. **渐进增强** — 有 API 则用，没有则降级

---

## 二、架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    小虾副脑 2.0                          │
├───────────┬───────────┬───────────┬─────────────────────┤
│  Orchestrator           │  Memory     │  Bridge Layer       │
│  (执行引擎)             │  (记忆引擎) │  (桥接/跨域)        │
│                          │            │                     │
│  Agent Loop              │  Short-term│  WSL↔Windows HTTP   │
│  Session Manager         │  Long-term │  OpenClaw 寄生      │
│  Context Engine          │  Vector KB │  CLI 原生运行       │
│  Tool Router             │  Profile   │                     │
│  Security Gate           │            │                     │
├───────────┴───────────┼────────────┼─────────────────────┤
│  Tool System           │  Plugin    │  Brain               │
│  (工具引擎)            │  (插件)     │  (大脑后端)          │
│                        │            │                      │
│  Native Tools          │  Lifecycle │  OpenClaw            │
│  MCP Client            │  Data      │  Ollama              │
│  MCP Server Host       │  Pipeline  │  OpenAI/Copilot      │
└────────────────────────┴────────────┴──────────────────────┘
```

---

## 三、核心子系统设计

### 3.1 执行引擎 (Orchestrator)

**职责**：管理 agent 的执行生命周期，串联工具、记忆、大脑。

```
AgentLoop:
  1. receive(input)           ← 来自 CLI / WebSocket / API
  2. context = build_context(  ← Context Engine
       session.history,
       memory.relevant,
       tools.available
     )
  3. response = brain.think(   ← Brain Backend
       prompt,
       context,
       tools_schemas
     )
  4. if response has tool_call:
       result = tool_router.dispatch(response.tool_call)
       goto 2 (with result appended)
  5. session.save(response)
     memory.maybe_store(key_info)
  6. emit(output)
```

**核心接口**：

```python
class Orchestrator:
    def run(self, input: str, session_id: str = None) -> AsyncIterator[Event]: ...
    def run_stream(self, input: str, session_id: str = None) -> AsyncIterator[Event]: ...
```

**Session 模型**（借鉴 LangGraph + OpenClaw）：

```python
@dataclass
class Session:
    id: str                    # UUID
    created_at: datetime
    last_active: datetime
    messages: list[Message]    # 消息历史
    state: dict                # 执行状态（checkpoint）
    metadata: dict             # 来源/模型/配置
```

- Session 序列化到 JSONL（吸取 OpenClaw 的经验）
- Checkpoint 机制：每轮交互保存一次完整状态（吸取 LangGraph 的经验）
- 索引文件管理 session 列表

**Context Engine**（借鉴 OpenClaw 引擎设计）：

```python
class ContextEngine:
    def assemble(
        self, session: Session, token_budget: int
    ) -> AssembledContext: ...

    def compact(
        self, session: Session, force: bool = False
    ) -> CompactResult: ...
```

- `legacy` 引擎：保留最后 N 条消息 + 总结之前
- `vector` 引擎：消息向量化 + 语义检索历史
- `plugin` 引擎：由插件完全接管

---

### 3.2 工具系统 (Tool System)

**借鉴 Cline 的 SDK-first 设计**：

```python
from agent.tools import Tool

class CodeAnalyzer(Tool):
    """分析代码文件结构"""
    
    name = "code_analyzer"
    description = "Analyze code file structure and extract metadata"
    
    schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to analyze"},
            "deep": {"type": "boolean", "description": "Deep analysis mode"}
        },
        "required": ["path"]
    }
    
    def run(self, path: str, deep: bool = False) -> str:
        ...
```

**与 1.x 的兼容**：保留现有 Tool 基类，新增 `ToolV2` 提供更严格的类型系统。

**MCP 协议支持**（核心差异化能力）：

```python
# MCP Client — 消费外部 MCP 服务器
class MCPClient(Tool):
    name = "mcp"
    description = "Connect to MCP server tools"
    
    def __init__(self, config):
        self.servers = {}  # name -> MCPConnection
    
    def register_server(self, name: str, command: str): ...
    def list_tools(self) -> list[ToolSchema]: ...
    
# MCP Server Host — 向外暴露我们的工具
class MCPServerHost:
    """启动 MCP server，让外部 agent 可以调用我们的工具"""
    def serve(self, tools: list[Tool], port: int = 9877): ...
```

**工具权限分层**（借鉴 Claude Code）：

| 级别 | 说明 | 默认策略 |
|------|------|----------|
| read | 只读工具（文件读取、搜索、浏览） | 自动 |
| write | 写工具（文件修改、代码生成） | 提示确认 |
| exec | 命令执行（shell、代码运行） | 严格确认 |
| dangerous | 危险操作（网络、系统修改） | 默认拒绝 |

---

### 3.3 记忆引擎 (Memory Engine)

**双层架构**（借鉴 LangGraph 的 short-term + long-term）：

```
Memory Engine
├── Short-term (Session-scoped)
│   ├── 消息历史 (JSONL)
│   └── 会话状态 (Checkpoints)
├── Long-term (Cross-session)
│   ├── daily_memory/        ← 现有，与 OpenClaw 共享
│   ├── MEMORY.md             ← 现有，长期精华
│   ├── vector_store/        ← 新增，语义检索
│   └── profile.json         ← 新增，用户画像
└── Retrieval
    ├── keyword_search       ← 现有
    ├── vector_search        ← 新增
    └── hybrid_search        ← 结合上述两者
```

**Long-term 记忆类型**（借鉴 LangGraph 分类）：

| 类型 | 用途 | 存储形式 | 示例 |
|------|------|----------|------|
| Semantic | 事实知识 | JSON profile / 向量 | "wssl 用 Java Spring Boot" |
| Episodic | 经验回放 | 结构化日志 | "上次部署遇到了 MySQL 连接问题" |
| Procedural | 指令/规则 | Markdown 文件 | "部署步骤：先 mvn compile" |

**向量存储设计**：

```
Layer 0: 无 embedding（零成本）
  - 只在记忆不可用时启用
  - 降级为关键词搜索
  
Layer 1: 本地 embedding（Ollama）
  - 用 Ollama 的 embedding 模型
  - 本地运行，零 API 成本
  
Layer 2: 云端 embedding（OpenAI/other）
  - 只在有 API key 时启用
  - 最佳检索质量
```

---

### 3.4 安全模型 (Security Gate)

借鉴 Claude Code 的三层 + Cline 的 HITL：

```
SecurityGate
├── Policy Engine
│   ├── allowlists / denylists   ← 工具级别
│   ├── permission profiles      ← 用户/项目级别
│   └── mode presets             ← read-only / normal / yolo
│
├── Approval System
│   ├── auto-approve (read tools)
│   ├── prompt-approve (write tools)
│   ├── strict-approve (exec tools)
│   └── deny (dangerous tools)
│
├── Sandbox Manager
│   ├── filesystem isolation
│   ├── network isolation
│   └── process sandbox (可选)
│
└── Audit Log
    ├── every tool call logged
    ├── approval decisions recorded
    └── session replay support
```

**模式预设**：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `normal` | 读写需确认，exec 严格确认 | 日常使用 |
| `read-only` | 所有修改/执行都拒绝 | 代码审查 |
| `auto-write` | 文件修改自动批准，exec 确认 | 快速迭代 |
| `yolo` | 全部自动批准 | 信任脚本 / 定时任务 |
| `sandbox` | 在沙箱中允许全部操作 | 代码实验 / 教育 |

---

### 3.5 桥接层 (Bridge Layer)

这是我们的**核心差异化**，不照搬任何框架：

```
Bridge Layer
├── Native CLI          ← 直接运行（Linux/macOS）
├── OpenClaw Adapter    ← 作为 OpenClaw 的 agent 运行
│   ├── 使用 OpenClaw 的工具定义
│   ├── 通过 OpenClaw 的会话管理
│   └── 逐步接管自身能力
│
├── WSL↔Windows Bridge  ← 跨域控制
│   ├── HTTP 协议 (9876)
│   ├── 文件 fallback (inbox/outbox)
│   └── 进程管理器
│
└── MCP Server          ← 标准接口
    └── 暴露/订阅 MCP 工具
```

**Layer 架构**（渐进增强）：

```
裸 CLI ─→ OpenClaw Adapter ─→ MCP Server

每一层 100% 功能独立，上层只是添加更多集成方式。
```

---

## 四、组件接口定义

### 4.1 Plugin 系统升级

当前 Plugin 接口（1.x）：
```python
class Plugin:
    setup() -> bool
    on_heartbeat()
    on_tick()
    cleanup()
```

升级后（2.0）：
```python
class PluginV2:
    # 元数据
    name: str
    version: str
    description: str
    
    # 生命周期
    async def setup(self) -> bool
    
    # 钩子点
    async def on_session_start(self, session_id: str)
    async def on_session_end(self, session_id: str)
    async def on_tool_call(self, tool_name: str, args: dict) -> dict | None
    async def on_tool_result(self, tool_name: str, result: str)
    async def on_message(self, role: str, content: str)
    async def on_brain_call(self, prompt: str) -> str | None
    
    # 清理
    async def cleanup(self)
```

### 4.2 事件系统

```
EventBus (单例)
├── subscribe(event_type, handler)  ← 注册监听
├── emit(event_type, data)          ← 发布事件
└── unsubscribe(event_type, handler)

事件类型：
  session:start    session:end
  tool:before      tool:after
  brain:call       brain:response
  memory:read      memory:write
  error:occurred
```

---

## 五、与现有系统的兼容

### 对 1.x 的向后兼容

| 1.x 组件 | 2.0 策略 |
|----------|----------|
| `tools/*.py` | ✅ 继续可用，自动注册为 Tool v1 |
| `memory/daily/*.md` | ✅ 继续读写，新增向量索引层 |
| `config.yaml` | ✅ 增量扩展，兼容老字段 |
| `plugins/*/__init__.py` | ⚠️ PluginV2 新增钩子，旧插件继续可用 |
| `brain/*.py` | ✅ BrainV2 新增方法（默认实现），旧后端兼容 |

### 对 OpenClaw 的策略

```
OpenClaw (宿主)         小虾副脑 (寄生)
├── gateway              ├── bridge_adapter.py
├── session mgmt         │   ├── tool_translator.py
├── tool definitions     │   ├── memory_sync.py
├── memory system        │   └── hook_injector.py
└── cron/scheduling      └── 
```

过渡路径：
1. 当前：完全寄生，通过 OpenClaw 的 session/tools/memory
2. 中期：副脑内部开始接管记忆和工具路由，OpenClaw 作为"通信层"
3. 终期：副脑独立运行，OpenClaw 只做消息路由（gateway）

---

## 六、实现路线图

### Phase 1 — 基础升级 (2-3 天)

| 任务 | 文件 | 依赖 |
|------|------|------|
| Tool v2 规范 + 参数 Schema 强化 | `tools/__init__.py` | — |
| Session 管理器 (JSONL + checkpoint) | `session_manager.py` | — |
| Context Engine (legacy 引擎) | `context_engine.py` | Session |
| 配置升级 (session/security/context 字段) | `config.yaml` | — |

### Phase 2 — 记忆与智能 (3-5 天)

| 任务 | 文件 | 依赖 |
|------|------|------|
| Vector Store 集成 (Ollama 优先) | `memory/vector_store.py` | Ollama |
| Hybrid Search (关键词 + 向量) | `memory/search.py` | Vector Store |
| Memory Profile (用户画像) | `memory/profile.py` | Memory |
| Memory Maintenance (自动总结+清理) | `memory/maintenance.py` | 全部记忆模块 |

### Phase 3 — 安全与集成 (3-5 天)

| 任务 | 文件 | 依赖 |
|------|------|------|
| Security Gate (权限分层) | `security/gate.py` | Tool v2 |
| 审批系统 (CLI/Web) | `security/approval.py` | Security Gate |
| MCP Client | `tools/mcp/client.py` | Tool v2 |
| MCP Server Host | `tools/mcp/server.py` | Tool v2 |
| Plugin 钩子系统升级 | `plugins/__init__.py` | EventBus |

### Phase 4 — 独立运行 (5-7 天)

| 任务 | 文件 | 依赖 |
|------|------|------|
| 原生 CLI (替代部分 OpenClaw 功能) | `cli/` | 全部 Phase 1-3 |
| 独立 session 管理 (JSONL) | `session/` | CLI |
| OpenClaw 降级模式 | `bridge/openclaw_adapter.py` | 全部 |
| 副脑自检 + 一键部署 | `setup.sh` v2 | 全部 |

---

## 七、设计决策记录 (ADR)

### ADR-001: 文件事件总线，不用消息队列

- **决策**：EventBus 是进程内单例，不引入 RabbitMQ / Redis
- **理由**：单进程场景不需要分布式消息，减少部署复杂度
- **后续**：如果未来需要多进程，可替换为 Redis PubSub

### ADR-002: 记忆默认用文件，向量为可选增强

- **决策**：文件系统是"零成本层"，向量检索是"增强层"
- **理由**：没有 GPU 也能跑，ollama embedding 也可选
- **后续**：衡量 token 成本 vs 检索质量，决定默认配置

### ADR-003: MCP 兼容优先于自定义协议

- **决策**：我们的工具代理默认暴露 MCP 接口
- **理由**：MCP 是 Claude Code / Cline 的共同标准，生态最大
- **后续**：如果 MCP 协议改动，我们的 adapter 层隔离变更

### ADR-004: Session 不从 OpenClaw 同步

- **决策**：副脑自己管理 session，OpenClaw 的 session 只做消息路由
- **理由**：解耦后，副脑可以独立于 OpenClaw 运行
- **后续**：通过 adapter 桥接两个 session 系统

### ADR-005: 权限系统不依赖 OpenClaw 的 sandbox

- **决策**：副脑有自己的 SecurityGate，不完全信任宿主的沙箱
- **理由**：副脑需要在不跑在 OpenClaw 上时也有安全保障
- **后续**：OpenClaw 上运行时，两套安全策略叠加

---

## 八、成功指标

```
Phase 1 完成时:
  ✅ Session 持久化 + 恢复
  ✅ Tool v2 所有工具带 JSON Schema
  ✅ Context Engine 自适应窗口

Phase 2 完成时:
  ✅ 记忆检索切换到 hybrid search
  ✅ Profile 自动构建
  ✅ 记忆每天自动总结 + 清理

Phase 3 完成时:
  ✅ 权限分层可配置
  ✅ MCP Server 运行中
  ✅ 插件系统覆盖主要生命周期钩子

Phase 4 完成时:
  ✅ CLI 可直接启动副脑
  ✅ 不依赖 OpenClaw 也能完整运行
  ✅ 同时支持 OpenClaw 寄生 + 独立运行双模式
```

---

> 本文档将同步到 `~/.agent/ARCHITECTURE.md`
> 各 Phase 拆分到 GitHub Issues 跟踪进度

