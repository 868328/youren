"""
需求探寻 — 配置
"""
import os

# 代理（mihomo 本地）
PROXY = "http://127.0.0.1:7890"

# 存储
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 每次爬取的结果保存天数
KEEP_DAYS = 90

# GitHub Token（可选，不设也能搜，但 rate limit 低）
# 优先级：vault → 环境变量 → 空
_github_token = os.environ.get('GITHUB_TOKEN', '')
if not _github_token:
    try:
        import sys
        sys.path.insert(0, os.path.expanduser('~/.agent'))
        from security.vault import CredentialVault
        import yaml
        _cfg_path = os.path.expanduser('~/.agent/config.yaml')
        if os.path.exists(_cfg_path):
            _cfg = yaml.safe_load(open(_cfg_path))
            _vault = CredentialVault(_cfg)
            _vault.unlock()
            _github_token = _vault.get('github_token') or ''
    except Exception:
        pass
GITHUB_TOKEN = _github_token

# 默认搜索关键词组
# 英文词主要命中 GitHub Issues（开发者 bug/提案）
# 中文词主要命中掘金（国内开发者文章/心得）
DEFAULT_KEYWORDS = [
    "godot bug",
    "godot slow",
    "godot crash",
    "godot export issue",
    "godot 引擎",
    "独立游戏 开发",
    "游戏引擎 选型",
    "游戏开发 问题",
]

# 每个关键词每次抓多少结果
RESULTS_PER_KEYWORD = 20

# 默认扫描的子版块/节点
REDDIT_SUBREDDITS = ["godot", "gameDev", "indiegaming"]
V2EX_NODES = ["programmer", "game", "share", "create"]
