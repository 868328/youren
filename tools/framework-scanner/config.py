"""
框架扫描 — 配置
"""
import os

PROXY = "http://127.0.0.1:7890"

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 每个框架的分析配置
# url: 要抓取的文档页面
# priority: 分析优先级 (1=最高)
# dimensions: 要重点分析的设计维度
FRAMEWORKS = {
    "claude-code": {
        "name": "Claude Code (Anthropic)",
        "urls": [
            "https://docs.anthropic.com/en/docs/claude-code/overview",
            "https://docs.anthropic.com/en/docs/claude-code/setup",
            "https://docs.anthropic.com/en/docs/claude-code/security",
        ],
        "priority": 1,
        "dimensions": ["CLI设计", "工具路由", "MCP协议", "安全模型"],
        "keywords": ["tool routing", "MCP", "agent loop", "tool definition"],
    },
    "langchain": {
        "name": "LangChain / LangGraph",
        "urls": [
            "https://docs.langchain.com/docs/category/architecture",
            "https://docs.langchain.com/docs/concepts/agent",
            "https://langchain-ai.github.io/langgraph/",
        ],
        "priority": 1,
        "dimensions": ["工作流编排", "记忆系统", "工具集成", "状态管理"],
        "keywords": ["agent", "tool", "memory", "workflow", "graph"],
    },
    "cline": {
        "name": "Cline (VS Code Agent)",
        "urls": [
            "https://docs.cline.bot/overview/about-cline",
            "https://docs.cline.bot/overview/architecture",
            "https://github.com/cline/cline",
        ],
        "priority": 1,
        "dimensions": ["文件系统集成", "工具定义", "MCP协议", "执行沙箱"],
        "keywords": ["tool", "MCP", "sandbox", "file operations"],
    },
    "openclaw": {
        "name": "OpenClaw Gateway",
        "urls": [],  # 本地读取
        "priority": 1,
        "dimensions": ["会话管理", "工具自省", "路由设计", "定时任务"],
        "local_docs": "/home/wssl/.nvm/versions/node/v24.16.0/lib/node_modules/openclaw/docs/",
        "keywords": ["gateway", "session", "tool", "routing"],
    },
    "cursor": {
        "name": "Cursor IDE",
        "urls": [
            "https://docs.cursor.com/get-started/overview",
            "https://docs.cursor.com/context/rules-for-ai",
            "https://docs.cursor.com/advanced/custom-models-and-providers",
        ],
        "priority": 2,
        "dimensions": ["上下文管理", "代码补全架构", "Agent模式", "规则系统"],
        "keywords": ["context", "agent", "rules", "composer"],
    },
}

# 架构分析维度
DIMENSIONS = [
    "tool_routing",       # 工具/函数的路由和调用机制
    "memory_system",      # 记忆架构（短期/长期/向量）
    "session_mgmt",       # 会话管理
    "context_mgmt",       # 上下文窗口管理
    "security_model",     # 安全策略
    "CLI_UX",            # CLI/交互设计
    "mcp_protocol",       # MCP 或类似协议支持
    "execution_model",    # 执行模型（同步/异步/流式）
]

# 每批最大学术查询
DEFAULT_RESULTS = 3
