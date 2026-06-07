#!/usr/bin/bash
## build.sh — WSL 端一键构建脚本
##
## 功能:
##   1. 通过 inbox/outbox 桥接向 Windows agent.py 发送指令
##   2. 执行 Godot --headless --export-release "Windows Desktop"
##   3. 检查导出结果并返回状态
##
## 用法:
##   ./build.sh                  # 导出 Windows 版
##   ./build.sh --check          # 仅检查导出目录状态
##   ./build.sh --help           # 显示帮助
##
## 依赖:
##   - Windows agent.py 正在运行
##   - D:\openclawworkspace\game-dev\ 共享目录可用
##   - Godot 4.6 已安装在 Windows 上 (路径配置在 agent.py)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="$(basename "$SCRIPT_DIR")"
SHARED_DIR="/mnt/d/openclawworkspace/game-dev"
INBOX="$SHARED_DIR/inbox"
OUTBOX="$SHARED_DIR/outbox"
EXPORT_DIR="$SCRIPT_DIR/export"

# ── 颜色 ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ── 帮助 ──────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--help" ]]; then
    echo "🛠  $PROJECT_NAME — 构建脚本"
    echo ""
    echo "用法:"
    echo "  ./build.sh                  导出 Windows 版"
    echo "  ./build.sh --check          检查导出状态"
    echo "  ./build.sh --help           显示此帮助"
    echo ""
    echo "出口码:"
    echo "  0  构建成功"
    echo "  1  出错或构建失败"
    echo "  2  agent.py 未运行"
    echo "  3  导出目录为空"
    exit 0
fi

# ── 检查共享目录 ──────────────────────────────────────────────────────
check_prereqs() {
    if [[ ! -d "$SHARED_DIR" ]]; then
        err "共享目录不存在: $SHARED_DIR"
        err "请确保 D: 盘已挂载到 /mnt/d/"
        exit 1
    fi

    # 检查 agent.py 是否运行（通过 status.json）
    if [[ -f "$SHARED_DIR/status.json" ]]; then
        local running
        running=$(python3 -c "import json; d=json.load(open('$SHARED_DIR/status.json')); print(d.get('running', False))" 2>/dev/null || echo "false")
        if [[ "$running" != "True" ]]; then
            warn "agent.py 状态文件显示未运行"
            warn "请确保 Windows 上 agent.py 正在运行"
            echo ""
            echo "  启动方法:"
            echo "    1. 在 Windows 上打开终端"
            echo "    2. 运行: python D:\\openclawworkspace\\game-dev\\agent.py"
            echo ""
            exit 2
        fi
    else
        warn "agent.py 状态文件不存在，可能未运行"
        warn "请在 Windows 上启动 agent.py 后重试"
        exit 2
    fi

    ok "前置检查通过"
}

# ── 发送指令到 Windows agent ──────────────────────────────────────────
send_cmd() {
    local action="$1"
    shift
    local cmd_id
    cmd_id="build_$(date +%s)_$$"

    # 构建指令 json
    local cmd_json
    if [[ "$action" == "godot_headless" ]]; then
        cmd_json=$(cat <<EOF
{
    "action": "godot_headless",
    "project": "$(echo "$1" | sed 's|/mnt/d/|D:/|')",
    "script": "$2",
    "timeout": 120
}
EOF
)
    elif [[ "$action" == "exec" ]]; then
        cmd_json=$(cat <<EOF
{
    "action": "exec",
    "command": "$1",
    "timeout": ${2:-120}
}
EOF
)
    else
        err "不支持的操作: $action"
        return 1
    fi

    # 写入 inbox
    echo "$cmd_json" > "$INBOX/${cmd_id}.json"
    info "指令已发送: $action (ID: $cmd_id)"

    # 轮询等待结果
    local max_wait=90
    local waited=0
    while [[ $waited -lt $max_wait ]]; do
        if [[ -f "$OUTBOX/result_${cmd_id}.json" ]]; then
            local result
            result=$(cat "$OUTBOX/result_${cmd_id}.json")
            rm -f "$OUTBOX/result_${cmd_id}.json"
            echo "$result"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    err "等待指令结果超时 (${max_wait}s)"
    return 1
}

# ── 导出 Godot 项目 ──────────────────────────────────────────────────
do_export() {
    info "开始导出 Windows Desktop 版本..."

    # 构建导出命令
    local win_project_path
    win_project_path="D:/openclawworkspace/game-dev/projects/space-shooter"

    # 直接通过 exec 执行 godot headless export
    local godot_cmd="\"$(python3 -c "
import json
d=json.load(open('$SHARED_DIR/status.json'))
print(d.get('tool_paths', {}).get('godot', 'godot'))
" 2>/dev/null)\""

    local export_cmd="${godot_cmd} --headless --path \"${win_project_path}\" --export-release \"Windows Desktop\""
    
    local result
    result=$(send_cmd "exec" "$export_cmd" 180)
    
    # 解析结果
    local ok
    ok=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ok', False))" 2>/dev/null)
    local stdout
    stdout=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); d.get('stdout','')" 2>/dev/null)
    local stderr
    stderr=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); d.get('stderr','')" 2>/dev/null)

    if [[ "$ok" == "True" ]]; then
        ok "Godot 导出命令执行成功"
        if [[ -n "$stdout" ]]; then
            echo "$stdout"
        fi
    else
        err "Godot 导出失败"
        if [[ -n "$stdout" ]]; then
            echo "$stdout"
        fi
        if [[ -n "$stderr" ]]; then
            echo "STDERR: $stderr"
        fi
        return 1
    fi

    # 等待导出文件生成
    sleep 3

    # 检查导出结果
    check_export
}

# ── 检查导出目录 ──────────────────────────────────────────────────────
check_export() {
    info "检查导出结果..."

    if [[ ! -d "$EXPORT_DIR" ]]; then
        warn "导出目录不存在: $EXPORT_DIR"
        return 3
    fi

    local files
    files=$(find "$EXPORT_DIR" -type f 2>/dev/null | head -20)
    if [[ -z "$files" ]]; then
        warn "导出目录为空"
        return 3
    fi

    echo ""
    echo "📦 导出目录内容 ($EXPORT_DIR):"
    find "$EXPORT_DIR" -type f -exec ls -lh {} \; 2>/dev/null | awk '{print "  " $5 "  " $9}'
    echo ""

    # 检查关键文件
    local exe_count
    exe_count=$(find "$EXPORT_DIR" -name "*.exe" 2>/dev/null | wc -l)
    local pck_count
    pck_count=$(find "$EXPORT_DIR" -name "*.pck" 2>/dev/null | wc -l)

    if [[ $exe_count -gt 0 ]]; then
        ok "找到 $exe_count 个可执行文件"
    fi
    if [[ $pck_count -gt 0 ]]; then
        ok "找到 $pck_count 个数据包文件"
    fi

    local total_size
    total_size=$(du -sh "$EXPORT_DIR" 2>/dev/null | cut -f1)
    ok "导出总大小: $total_size"
    return 0
}

# ── 主流程 ──────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║     🚀  打飞机 — 构建脚本               ║"
    echo "║     Godot 4.6 | Windows Desktop          ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""

    case "${1:-}" in
        --check)
            check_export
            exit $?
            ;;
        *)
            check_prereqs
            echo ""
            do_export
            exit $?
            ;;
    esac
}

main "$@"
