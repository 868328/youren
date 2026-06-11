# Agent 框架架构对比报告
_生成时间: 2026-06-10 11:50_
共分析 4 个框架
---
## Claude Code (Anthropic) (`claude-code`)
扫描时间: 2026-06-10T11:51:00
### Tool Routing
- Permission-based architecture: strict read-only by default, explicit approval for modifications- Bash tool sandboxing: filesystem+network isolation, configurable with /sandbox command- Write access restricted to project folder and subfolders — cannot modify parent dirs without permission### Memory System
- CLAUDE.md: project-level Markdown file read at every session start (coding standards, architecture decisions)- Auto memory: Claude automatically saves learnings like build commands and debugging insights across sessions- Session context is conversation-based: subagents have separate context windows### Session Mgmt
- Multiple surfaces sharing same engine: Terminal, VS Code, Desktop, Web, JetBrains — same CLAUDE.md, settings, MCP- Session persistence: /resume to continue previous conversations- Remote Control: continue local sessions from mobile or browser### Context Mgmt
- Subagent architecture: each subagent runs in independent context window with custom system prompt- Built-in subagents: Explore (read-only, Haiku), Plan (read-only), General-purpose (full access)- Context isolation by design: subagents keep exploration results out of main conversation### Security Model
- SOC 2 Type 2, ISO 27001 certified- Sandboxed bash tool: filesystem and network isolation- Network command approval: curl/wget not auto-approved by default### Cli Ux
- Unix philosophy: composable, pipe-able, scriptable- Modes: interactive TUI, one-shot, JSON streaming, Yolo (auto-approve), Zen (background)- pipe input: cat file | claude -p 'summarize'### Mcp Protocol
- MCP (Model Context Protocol) is a core extension point for Claude Code- Connect to Google Drive, Jira, Slack, databases, APIs via MCP servers- MCP servers configured in project source code as part of Claude Code settings### Execution Model
- Agent teams: coordinator delegates to specialist agents with separate tools and context- Scheduled tasks: cron-like recurring automations (PR summaries, dependency checks)- Agent SDK for fully custom orchestration with control over tool access and permissions---
## Cline (Cline Bot Inc.) (`cline`)
扫描时间: 2026-06-10T11:51:45
### Tool Routing
- SDK-first: @cline/sdk for building custom agents with programmatic tool definitions- createTool API: name, description, inputSchema (JSON Schema), execute handler- Plugin system: register custom tools and lifecycle hooks### Memory System
- Checkpoints with /undo for workspace state rewinding- .clinerules files: project-specific rules guiding agent behavior (coding standards, architecture)- Subagent memory: team state persists across sessions### Session Mgmt
- Sessions span CLI, VS Code, JetBrains, Kanban — shared agent core- Chat connectors: Telegram, Slack, Google Chat, WhatsApp, Linear via cline connect- Each conversation thread maps to an agent session with full context### Context Mgmt
- Plan mode vs Act mode: separates exploration from execution- Plan mode: explores codebase, asks questions, lays out strategy- Act mode: executes with approval (or auto-approve for autonomous)### Security Model
- Human-in-the-loop: every file edit and terminal command requires approval by default- Yolo mode: skip approval prompts (opt-in)- Auto-approve toggle: per-tool or all-tools### Cli Ux
- npm install -g cline for CLI, or platform binaries (macOS/Linux/Windows)- Multiple modes: interactive TUI, one-shot, JSON (NDJSON), Yolo, Zen (background hub daemon)- Rich TUI: plan/act toggle, slash commands, file mentions, live tool approvals### Mcp Protocol
- Native MCP support for connecting custom tools- cline mcp command for managing MCP servers- Supports community-built MCP servers and custom ones### Execution Model
- Multi-agent teams: coordinator delegates to specialist agents- Kanban board: parallel agents with worktrees, auto-commit, dependency chains- Cron schedules: cline schedule create with --cron, --workspace, --provider flags---
## LangChain / LangGraph (`langchain`)
扫描时间: 2026-06-10T11:51:30
### Tool Routing
- Low-level orchestration framework: StateGraph with nodes, edges, START/END- Tool integration via LangChain components: models, tools, agent loops on top of LangGraph- Deep Agents SDK: planning, subagents, filesystem tools, and context management on top of LangGraph### Memory System
- Two-tier memory: short-term (thread-scoped) and long-term (cross-session)- Short-term: state persisted via checkpointer at each super-step boundary- Long-term: stores with custom namespaces, shared across threads### Session Mgmt
- Thread-based session model: thread_id as primary key for checkpoint storage- Human-in-the-loop: inspect, interrupt, approve graph steps at any point- Time travel: replay prior executions, fork state at arbitrary checkpoints### Context Mgmt
- Context window management via message filtering: trim/filter conversation history- Auto-compaction not built-in — manual message management techniques- Agent state includes conversation history + files + retrieved documents + artifacts### Security Model
- Durable execution: checkpoint persistence for fault tolerance- Pending writes: failed nodes don't require recomputing successful node writes- Human-in-the-loop is core security pattern — manual approval at graph steps### Cli Ux
- Python library, not terminal CLI — pip install langgraph- LangSmith CLI for tracing, datasets, experiments- LangSmith Studio: visual interface for designing and testing agents### Mcp Protocol
- No native MCP support mentioned — uses LangChain's own tool integration system### Execution Model
- StateGraph orchestration: nodes execute (potentially in parallel) per super-step- Invoke/stream/async execution modes- Agent Server for production deployment with automatic checkpointing---
## OpenClaw Gateway (`openclaw`)
扫描时间: 2026-06-10T11:50:00
### Tool Routing
- Gateway architecture: single long-lived Gateway owns all messaging surfaces, exposes typed WS API with requests/responses/events- Tools defined in ~/.../docs/tools/ — each tool has its own doc with schema. Tools invoke via HTTP API at /openresponses/... or gateway WS API- Config-tools system: tools can be enabled/disabled per agent via agents.defaults.tools/agents.list[].tools allow/deny lists### Memory System
- Three memory-related files: MEMORY.md (long-term curated), memory/YYYY-MM-DD.md (daily notes), DREAMS.md (optional dream diary)- Files are plain Markdown — no hidden state. Memory_search uses hybrid search (vector + keyword)- Pluggable memory backends: builtin (SQLite), QMD (local-first), Honcho (AI-native cross-session), LanceDB### Session Mgmt
- Sessions organized by source: DMs share one session by default, group chats isolated per group, cron jobs get fresh session per run- DM isolation modes: main, per-peer, per-channel-peer, per-account-channel-peer- Session lifecycle: daily reset (4AM local), idle reset (configurable), manual reset (/new or /reset)### Context Mgmt
- Context engine: pluggable system controlling message assembly, compaction, subagent lifecycle- Four lifecycle points: ingest → assemble → compact → after turn- Legacy engine: pass-through assembly, built-in summarization compaction. Plugin engines can implement custom strategies### Security Model
- THREAT MODEL documented in security/THREAT-MODEL-ATLAS.md with formal verification- WebSocket auth modes: shared-secret, trusted-proxy, Tailscale, none (private ingress only)- Sandboxing: sandbox vs tool-policy vs elevated — three tier security model### Cli Ux
- openclaw CLI commands: agents, channels, status, doctor, sessions, cron, gateway, memory, plugins, security- Status card shows: model, usage, time, cost, tasks. /status in chat shows context usage- Slash commands: /new, /reset, /stop, /status, /context list, /context detail### Mcp Protocol
- Mentioned as an extension point but OpenClaw does not use MCP as primary protocol- Gateway uses its own WebSocket protocol with JSON frames: connect request → typed messages with req/res/event lifecycle- No direct MCP server/client documentation found in core docs### Execution Model
- Agent loop: intake → context assembly → model inference → tool execution → streaming → persistence- Serialized per session: runs queued per session key + optional global lane to prevent race conditions- Streaming: assistant deltas, tool events, lifecycle events all streamed through WS events---

## 设计维度交叉对比

| 维度 | Claude Code (Anthropic) | Cline (Cline Bot Inc.) | LangChain / LangGraph | OpenClaw Gateway |
|---|---|---|---|---|
| Tool Routing | ✅ 5 条 | ✅ 5 条 | ✅ 4 条 | ✅ 4 条 |
| Memory System | ✅ 4 条 | ✅ 4 条 | ✅ 5 条 | ✅ 5 条 |
| Session Mgmt | ✅ 4 条 | ✅ 4 条 | ✅ 4 条 | ✅ 5 条 |
| Context Mgmt | ✅ 4 条 | ✅ 5 条 | ✅ 3 条 | ✅ 6 条 |
| Security Model | ✅ 6 条 | ✅ 5 条 | ✅ 3 条 | ✅ 5 条 |
| Cli Ux | ✅ 4 条 | ✅ 6 条 | ✅ 4 条 | ✅ 4 条 |
| Mcp Protocol | ✅ 4 条 | ✅ 4 条 | ✅ 1 条 | ✅ 3 条 |
| Execution Model | ✅ 5 条 | ✅ 6 条 | ✅ 5 条 | ✅ 6 条 |
