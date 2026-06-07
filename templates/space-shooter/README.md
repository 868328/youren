# 🚀 打飞机 — Space Shooter

> Godot 4.6 | 游刃 🎮 生成 | 经典竖版射击游戏

## 📋 项目概览

基于 Godot 4.6 引擎的经典竖版打飞机游戏。玩家控制飞船，在星空中消灭不断来袭的敌人，获取高分。

**项目状态:** 阶段二 — 工程化已完成（单元测试、构建脚本、版本管理）

## 🎮 操作

| 按键 | 功能 |
|------|------|
| A / ← | 左移 |
| D / → | 右移 |
| 空格 | 射击 |
| Shift | 暂停 |

## 🎯 玩法

- **消灭敌人**获得分数
- **3 条命**，撞敌人或被打中丢一条
- **波次系统**：每波敌人越来越强（更多、更快）
- **三种敌人**：普通（白色）、快速（橙色）、坦克（红色，3HP）
- **最高分**自动保存

## 🏗 项目架构

```
space-shooter/
├── scenes/                # Godot 场景文件
│   ├── main_menu.tscn     # 主菜单
│   ├── game.tscn          # 主游戏场景
│   ├── player.tscn        # 玩家飞船
│   ├── enemy.tscn         # 敌人
│   ├── bullet.tscn        # 子弹
│   ├── explosion.tscn     # 爆炸特效
│   └── hud.tscn           # HUD 显示
├── scripts/               # GDScript 脚本
│   ├── game_manager.gd    # 全局状态 (AutoLoad)
│   ├── player.gd          # 玩家控制器
│   ├── enemy.gd           # 敌人逻辑
│   ├── bullet.gd          # 子弹行为
│   ├── enemy_spawner.gd   # 波次生成器
│   ├── explosion.gd       # 爆炸粒子
│   ├── star_background.gd # 星空背景
│   └── ui/
│       ├── hud.gd         # HUD 逻辑
│       └── main_menu.gd   # 主菜单逻辑
├── assets/                # 资源文件
│   ├── sprites/           # 精灵贴图
│   └── audio/             # 音效（待添加）
├── tests/                 # 单元测试
│   ├── run_tests.gd       # 测试运行器
│   ├── test_game_manager.gd
│   ├── test_enemy_spawner.gd
│   └── test_enemy.gd
├── export/                # 构建产物（gitignored）
├── docs/                  # 工程文档
│   ├── bridge-upgrade-plan.md  # 桥接协议升级方案
│   └── template-guide.md      # 模板化指南
├── build.sh               # WSL 端构建脚本
├── build.bat              # Windows 端构建脚本
├── .gitignore             # Git 忽略规则
├── project.godot          # Godot 项目配置
├── export_presets.cfg     # 导出预设
└── README.md              # 本文件
```

## 🔧 构建

### 方式一：Windows 端直接构建

```bash
# 双击 build.bat, 或终端执行:
build.bat
```

### 方式二：WSL 端通过桥接

```bash
# 前置: agent.py 在 Windows 上运行
./build.sh              # 完整构建
./build.sh --check      # 仅检查导出状态
```

### 方式三：手动使用 Godot

```bash
# 编辑器
godot --path .

# 导出 Windows Desktop
godot --headless --path . --export-release "Windows Desktop"
```

构建产物输出到 `export/` 目录。

## 🧪 测试

```bash
# 运行所有单元测试（headless 模式）
godot --headless --path . --script tests/run_tests.gd
```

### 测试覆盖

| 测试文件 | 覆盖范围 |
|----------|---------|
| `test_game_manager.gd` | 分数管理、生命管理、最高分、信号（11 项） |
| `test_enemy_spawner.gd` | 波次逻辑、参数变化、类型分布（8 项） |
| `test_enemy.gd` | 类型初始化、伤害系统、得分（10 项） |

### 添加测试

1. 在 `tests/` 下新建 `test_*.gd` 文件
2. 继承要测试的脚本
3. 实现 `run_tests()` 方法
4. 使用 `assert()` 断言

## 📦 导出配置

- **平台:** Windows Desktop
- **应用名:** 打飞机
- **版本:** 1.0.0
- **公司:** GameWeaver
- **渲染:** 480×720 V-Sync 开启

## 🛠 开发环境

| 工具 | 版本 | 用途 |
|------|------|------|
| Godot | 4.6 stable | 游戏引擎 |
| GDScript | — | 脚本语言 |
| Python | 3.x | 桥接脚本 |
| Git | — | 版本管理 |

## 📝 许可

所有精灵资源来自 [Kenney.nl](https://kenney.nl) (CC0 许可)。  
游戏代码采用 MIT 许可。

## 🦐 关于

由 **游刃** 游戏开发框架自动生成并工程化。  
架构设计 / 代码生成 / 工程化：小虾 🦐
