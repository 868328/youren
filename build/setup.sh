#!/usr/bin/env bash
## setup.sh — 游刃一键部署脚本
## 用法: curl -fsSL https://raw.githubusercontent.com/.../setup.sh | bash

set -euo pipefail

echo "🚀 游刃 · 一键部署"
echo "=============================="
echo ""

# 检测系统
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
    echo "✅ 检测到 WSL 环境"
else
    echo "✅ 检测到 Linux 原生环境"
fi

# 检查依赖
echo ""
echo "📋 检查依赖..."

check_dep() {
    if command -v "$1" &>/dev/null; then
        echo "  ✅ $1 ($(command -v $1))"
        return 0
    else
        echo "  ❌ $1 — 未安装"
        return 1
    fi
}

check_dep python3
check_dep git

# 配置 Git 提示（如果是首次使用）
if ! git config --global user.name &>/dev/null; then
    echo ""
    echo "📝 Git 配置..."
    read -p "  输入 Git 用户名: " git_name
    read -p "  输入 Git 邮箱: " git_email
    git config --global user.name "$git_name"
    git config --global user.email "$git_email"
    echo "  ✅ Git 已配置"
fi

# 如果 WSL，检查 Windows 端
if $IS_WSL; then
    echo ""
    echo "🔧 检查 WSL↔Windows 桥接..."
    
    # 检查 /mnt/d 是否可用
    if [ -d "/mnt/d" ]; then
        echo "  ✅ D: 盘已挂载"
    else
        echo "  ⚠️  D: 盘未挂载，请确认 Windows 共享目录可用"
    fi
    
    echo ""
    echo "📝 下一步: 在 Windows 上运行 agent.py"
    echo ""
    echo "  cd path\\to\\youren\\agent"
    echo "  python agent.py"
    echo ""
fi

echo ""
echo "✅ 部署检查完成"
echo ""
echo "📖 快速开始:"
echo "  1. cd templates/space-shooter"
echo "  2. run_tests.bat   (Windows) 或"
echo "     ./build.sh --test (WSL)"
echo ""
echo "🎮 开玩!"
