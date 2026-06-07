# 🧬 模板化指南 — 基于 Space Shooter 创建新的 Godot 2D Shooter

> 本文档说明如何基于当前项目创建新的 Godot 2D 射击游戏。
> 标注哪些是"通用模板代码"，哪些是"游戏特有代码"。

---

## 一、通用模板代码 vs 游戏特有代码

### 📦 目录层级划分

```
space-shooter/                      # 项目根（重命名为你的游戏名）
├── scenes/                         # [通用架构] 场景是 Godot 标准组织方式
│   ├── main_menu.tscn              # [模板] 场景结构可复用，内容需替换
│   ├── game.tscn                   # [模板] 场景结构可复用
│   ├── player.tscn                 # [模板] 场景结构可复用
│   ├── enemy.tscn                  # [模板] 场景结构可复用
│   ├── bullet.tscn                 # [模板] 场景结构可复用
│   ├── explosion.tscn              # [模板] 场景结构可复用
│   └── hud.tscn                    # [模板] 场景结构可复用
├── scripts/                        # [通用架构] 脚本组织方式
│   ├── game_manager.gd             # [模板] 但方法体需根据新游戏重写
│   ├── player.gd                   # [游戏特有] 输入/移动/射击逻辑
│   ├── enemy.gd                    # [模板] 类型系统可复用，具体值需调整
│   ├── bullet.gd                   # [模板-简单] 移动+碰撞
│   ├── enemy_spawner.gd            # [模板] 波次系统可复用，参数需调整
│   ├── explosion.gd                # [模板-简单] 动画播放+清理
│   ├── star_background.gd          # [模板] 纯视觉，几乎不改
│   └── ui/
│       ├── hud.gd                  # [游戏特有] 显示内容需重做
│       └── main_menu.gd            # [游戏特有] UI 文案/按钮需重做
├── tests/                          # [通用架构] 测试目录结构可复用
│   ├── run_tests.gd                # [模板] 直接复用
│   ├── test_game_manager.gd        # [模板] 测试结构可复用
│   ├── test_enemy_spawner.gd       # [模板] 测试结构可复用
│   └── test_enemy.gd               # [模板] 测试结构可复用
├── assets/                         # [游戏特有] 所有素材需替换
├── build.sh                        # [模板] 直接复用
├── build.bat                       # [模板] 直接复用
├── .gitignore                      # [模板] 直接复用
├── project.godot                   # [不可复用] 每项目独立配置
├── export_presets.cfg              # [模板] 需修改 product_name 等
└── README.md                       # [模板] 需重写为你的游戏信息
```

### 🔄 可复用的模板文件

以下文件可以直接复制到新项目，**无需修改**：

| 文件 | 说明 |
|------|------|
| `tests/run_tests.gd` | 通用测试运行器 |
| `build.sh` | WSL 端构建脚本 |
| `build.bat` | Windows 端构建脚本 |
| `.gitignore` | Godot 通用忽略规则 |
| `assets/sprites/LICENSE_kenney.txt` | 资源许可（如果使用相同素材） |
| `docs/template-guide.md` | 这个文件本身也可以作为参考 |

### ✂️ 需要调整的模板文件

这些文件需要**少量调整**即可在新项目中使用：

| 文件 | 修改内容 |
|------|---------|
| `scripts/game_manager.gd` | 信号定义、游戏规则（积分/生命逻辑） |
| `scripts/enemy_spawner.gd` | 生成参数（间隔/速度/波次公式） |
| `scripts/enemy.gd` | 敌人类型、属性值（速度/血量/得分） |
| `scripts/explosion.gd` | 无修改需求，纯视觉组件 |
| `scripts/star_background.gd` | 无修改需求，纯视觉组件 |
| `scripts/bullet.gd` | 速度/方向/碰撞层（如果射击方式不同） |
| `export_presets.cfg` | product_name, company_name 等信息 |

### 🆕 需要完全重写的游戏特有代码

这些文件**大部分代码需重写**：

| 文件 | 重写原因 |
|------|---------|
| `scripts/player.gd` | 移动方式、武器系统、碰撞逻辑因游戏而异 |
| `scripts/ui/hud.gd` | 显示的 UI 元素因游戏而异 |
| `scripts/ui/main_menu.gd` | 菜单项、过渡动画因游戏而异 |
| `scenes/*.tscn` | 场景节点结构因游戏设计而异 |
| `assets/` | 所有资源替换为游戏自有素材 |

---

## 二、创建新游戏的步骤

### 步骤 1：复制项目

```bash
# 创建新项目目录
cp -r /mnt/d/openclawworkspace/game-dev/projects/space-shooter \
      /mnt/d/openclawworkspace/game-dev/projects/my-new-shooter

cd /mnt/d/openclawworkspace/game-dev/projects/my-new-shooter

# 删除 git 历史（重新开始）
rm -rf .git

# 清理旧导出
rm -rf export/
```

### 步骤 2：配置项目基础信息

编辑 `project.godot`，修改：
```
config/name="你的游戏名"
config/description="你的游戏描述"
config/icon="res://assets/sprites/你的图标.png"
```

编辑 `export_presets.cfg`，修改：
```
application/product_name="你的产品名"
application/company_name="你的公司名"
application/file_version="1.0.0"
application/icon="res://assets/sprites/你的图标.png"
```

### 步骤 3：设计游戏机制

以当前项目的 MVC 模式为参考：

```
GameManager (Model)   →   Scene Nodes (View)   →   GDScripts (Controller)
  └── 游戏状态              ├── player.tscn           ├── player.gd
  └── 分数/生命             ├── enemy.tscn            ├── enemy.gd
  └── 信号                  ├── bullet.tscn           ├── bullet.gd
                             ├── hud.tscn             ├── ui/hud.gd
                             └── main_menu.tscn       └── ui/main_menu.gd
```

**推荐保持的设计模式：**
1. **AutoLoad 单例** — 使用 GameManager 管理全局状态
2. **信号驱动** — 状态变化通过信号通知 UI
3. **场景解耦** — 每个游戏对象独立场景文件
4. **分组管理** — 使用 `add_to_group()` + `get_tree().get_nodes_in_group()`

### 步骤 4：替换资源

```bash
# 替换精灵
cp 你的新精灵.png assets/sprites/

# 在 Godot 编辑器中重新导入
# 或者打开编辑器自动刷新（Godot 4 自动检测文件变化）
```

### 步骤 5：修改核心脚本

**修改 player.gd 示例：**
```gdscript
# space-shooter 版本
func _physics_process(delta):
    # 左右移动 + 射击
    pass

# 你的新版本（例如改为四方向移动）
func _physics_process(delta):
    # WASD 四方向 + 自动射击
    pass
```

**修改 enemy_spawner.gd 示例：**
```gdscript
# 调整生成参数
@export var spawn_interval: float = 2.0  # 从 1.5 改为 2.0
@export var initial_enemies_per_wave: int = 3  # 从 5 改为 3

func _ready():
    _enemies_per_wave = initial_enemies_per_wave
```

### 步骤 6：添加新敌人类型

在 `enemy.gd` 的 `enum` 中添加新类型：

```gdscript
enum EnemyType { BASIC, FAST, TANK, BOSS, SNIPER, SWARM }

func _ready():
    match type:
        EnemyType.BASIC:  # 保持不变
            ...
        EnemyType.SNIPER:  # 新增
            speed = 100.0; hp = 2; score_value = 200
            # 添加射击逻辑...
```

### 步骤 7：更新测试

```gdscript
# tests/test_enemy.gd 新增方法
func test_sniper_initialization():
    var e = Enemy.new()
    _init_enemy(e, Enemy.EnemyType.SNIPER)
    assert(e.speed == 100.0, "SNIPER 速度应为 100")
    assert(e.hp == 2, "SNIPER 血量应为 2")
    ...
```

### 步骤 8：初始化 Git

```bash
git init
git add .
git commit -m "🎮 初始提交: 基于 Space Shooter 模板创建"
```

---

## 三、常见扩展模式

### 3.1 添加新武器类型

1. **bullet.gd** 中添加 `enum BulletType { NORMAL, SPREAD, LASER, MISSILE }`
2. **player.gd** 中添加武器切换逻辑（数字键或道具）
3. **game_manager.gd** 中添加武器等级状态

### 3.2 添加道具系统

1. 创建 `scenes/powerup.tscn` 和 `scripts/powerup.gd`
2. 在 `enemy_spawner.gd` 中添加道具生成逻辑
3. 定义道具类型：加速、护盾、全屏清场等

### 3.3 添加关卡/Boss

1. 扩展 `enemy_spawner.gd` 支持关卡定义（可配置 JSON 数据）
2. 创建 `scenes/boss.tscn` 和 `scripts/boss.gd`
3. 在特定波次后触发 Boss 战

### 3.4 添加排行榜

1. 扩展 `game_manager.gd` 的高分系统
2. 创建本地排行榜 UI
3. 可选：添加在线排行榜（HTTP API）

### 3.5 移动端适配

1. `project.godot` 中添加触屏输入
2. 创建虚拟摇杆 UI
3. 调整 UI 缩放

---

## 四、最佳实践

### ✅ 推荐做法

- **使用 Autoload** 管理跨场景全局状态
- **信号先行** — 数据变化 → 发信号 → UI 响应（解耦核心逻辑和显示）
- **分组管理** — 用 `add_to_group` 管理同类节点
- **场景独立** — 每个游戏对象一个 .tscn 文件
- **资源复用** — 将通用工具函数放到 `scripts/utils/`
- **小步提交** — 每个功能点一次 commit

### ❌ 反模式

- **场景名硬编码** — 用 `preload()` 替代字符串路径
- **魔法数值** — 用 `@export` 在编辑器中配置参数
- **耦合 UI 和逻辑** — 信号先行，UI 只响应信号
- **全局变量** — 用 Autoload 管理状态，不要用全局 `var`
- **长方法** — 一个方法做一件事，保持 < 50 行

### 🔧 开发工具

```bash
# Godot 编辑器
godot --path .

# 运行测试
godot --headless --path . --script tests/run_tests.gd

# 导出 Windows
godot --headless --path . --export-release "Windows Desktop"

# 导出 Linux
godot --headless --path . --export-release "Linux/X11"

# 导出 Web
godot --headless --path . --export-release "Web"
```

---

## 五、文件清单（复用时检查）

创建新项目后，确认以下文件已正确处理：

### 直接复用的文件
- [ ] `.gitignore`
- [ ] `build.sh`
- [ ] `build.bat`
- [ ] `tests/run_tests.gd`
- [ ] `docs/template-guide.md`

### 需修改的文件
- [ ] `project.godot` — 修改项目名、描述、图标
- [ ] `export_presets.cfg` — 修改产品信息
- [ ] `README.md` — 重写为你的游戏说明
- [ ] `scripts/game_manager.gd` — 调整游戏规则
- [ ] `scripts/enemy_spawner.gd` — 调整波次参数
- [ ] `scripts/enemy.gd` — 调整敌人属性

### 需重写的文件
- [ ] `scripts/player.gd` — 玩家控制逻辑
- [ ] `scripts/ui/hud.gd` — HUD 显示
- [ ] `scripts/ui/main_menu.gd` — 主菜单
- [ ] `assets/sprites/` — 替换所有精灵
- [ ] `scenes/*.tscn` — 重新设计场景

### 需删除的文件
- [ ] `docs/bridge-upgrade-plan.md` — 如果不需要
- [ ] `assets/sprites/LICENSE_kenney.txt` — 如果使用自有素材
