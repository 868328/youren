# 🎮 2D Game Template

> Godot 4.6 2D 游戏项目模板 — 自动生成于 游刃 🎮

## 目录结构

```
project/
├── scenes/           # 场景文件
│   ├── main_menu.tscn    # 主菜单
│   ├── game.tscn         # 游戏场景
│   ├── player.tscn       # 玩家场景
│   └── hud.tscn          # HUD 界面
├── scripts/          # GDScript 逻辑
│   ├── game_manager.gd   # 全局游戏状态
│   ├── audio_manager.gd  # 音效管理
│   ├── player.gd         # 玩家控制器
│   └── ui/
│       ├── hud.gd
│       └── main_menu.gd
├── assets/           # 游戏资源
│   ├── sprites/          # 精灵图
│   ├── audio/            # 音频文件 (.ogg)
│   └── fonts/            # 字体文件
├── tests/            # 测试脚本
│   ├── run_tests.gd      # 测试运行器
│   └── test_game_manager.gd
├── project.godot     # 项目配置
├── export_presets.cfg # 导出配置
└── README.md         # 本文件
```

## 运行

```bash
# Godot 编辑器打开
godot --path .

# 无头模式运行测试
godot --headless --path . --script tests/run_tests.gd

# 导出 Windows 版
godot --headless --path . --export-release "Windows Desktop"
```

## 内置功能

- ✅ 主菜单 + 游戏场景切换
- ✅ 玩家移动/跳跃（键盘 WASD + 空格）
- ✅ 分数系统 + 最高分持久化
- ✅ 暂停/恢复
- ✅ 音效框架（Ogg Vorbis 格式）
- ✅ 单元测试框架
