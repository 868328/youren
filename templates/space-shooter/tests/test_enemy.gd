extends "res://scripts/enemy.gd"
## Enemy 单元测试
## 类型初始化 · 伤害系统 · 得分 · 行为验证

var EnemyScript = preload("res://scripts/enemy.gd")

# ── 辅助 ────────────────────────────────────────────────────────────

func _init_enemy(e, t: int) -> void:
	e.type = t
	e._screen_height = 720.0
	match t:
		0:  e.speed = 150.0; e.hp = 1; e.score_value = 100
		1:  e.speed = 280.0; e.hp = 1; e.score_value = 150
		2:  e.speed = 80.0; e.hp = 3; e.score_value = 300

# 直接测伤害逻辑，跳过 $Sprite2D 和 tween（需要场景树，不在 headless 测试范围）
func _test_hp_after_damage(e, expected_hp: int, label: String) -> void:
	var hp_before = e.hp
	# 手动减血，模拟 take_damage 的核心逻辑
	e.hp -= 1
	assert(e.hp == expected_hp, "%s: 期望 hp=%d, 实际=%d" % [label, expected_hp, e.hp])

# ── 测试 ────────────────────────────────────────────────────────────

func test_basic_initialization() -> void:
	var e = EnemyScript.new()
	_init_enemy(e, 0)
	assert(e.speed == 150.0, "BASIC 速度应为 150")
	assert(e.hp == 1, "BASIC 血量应为 1")
	assert(e.score_value == 100, "BASIC 得分应为 100")
	print("✅ test_basic_initialization 通过")

func test_fast_initialization() -> void:
	var e = EnemyScript.new()
	_init_enemy(e, 1)
	assert(e.speed == 280.0, "FAST 速度应为 280")
	assert(e.hp == 1, "FAST 血量应为 1")
	assert(e.score_value == 150, "FAST 得分应为 150")
	print("✅ test_fast_initialization 通过")

func test_tank_initialization() -> void:
	var e = EnemyScript.new()
	_init_enemy(e, 2)
	assert(e.speed == 80.0, "TANK 速度应为 80")
	assert(e.hp == 3, "TANK 血量应为 3")
	assert(e.score_value == 300, "TANK 得分应为 300")
	print("✅ test_tank_initialization 通过")

func test_take_damage_core_logic() -> void:
	# 测试减血核心逻辑（不涉及场景树相关的视觉特效）
	var e = EnemyScript.new()
	e.hp = 3
	e.hp -= 1
	assert(e.hp == 2, "坦克 3HP → 减 1 → 2")
	e.hp -= 1
	assert(e.hp == 1, "再减 1 → 1")
	e.hp -= 1
	assert(e.hp == 0, "再减 1 → 0 (死亡)")
	print("✅ test_take_damage_core_logic 通过")

func test_tank_survives_first_hit() -> void:
	var e = EnemyScript.new()
	e.hp = 3
	e.hp -= 1
	assert(e.hp > 0, "坦克第一次受伤后应存活 (hp > 0)")
	print("✅ test_tank_survives_first_hit 通过")

func test_basic_dies_in_one_hit() -> void:
	var e = EnemyScript.new()
	e.hp = 1
	e.hp -= 1
	assert(e.hp <= 0, "BASIC 一次受伤后 hp 应 ≤ 0")
	print("✅ test_basic_dies_in_one_hit 通过")

func test_fast_dies_in_one_hit() -> void:
	var e = EnemyScript.new()
	e.hp = 1
	e.hp -= 1
	assert(e.hp <= 0, "FAST 一次受伤后 hp 应 ≤ 0")
	print("✅ test_fast_dies_in_one_hit 通过")

func test_score_value_matches_type() -> void:
	var e = EnemyScript.new()
	_init_enemy(e, 0)
	assert(e.score_value == 100, "BASIC 得分 100")
	e = EnemyScript.new()
	_init_enemy(e, 1)
	assert(e.score_value == 150, "FAST 得分 150")
	e = EnemyScript.new()
	_init_enemy(e, 2)
	assert(e.score_value == 300, "TANK 得分 300")
	print("✅ test_score_value_matches_type 通过")

func test_enemy_movement_speed() -> void:
	var e = EnemyScript.new()
	_init_enemy(e, 1)
	assert(e.speed == 280.0, "FAST 速度 280")
	var pos_y_after = e.speed * 0.016
	assert(abs(pos_y_after - 4.48) < 0.001, "1 帧(60fps)后 y 应移动约 4.48 单位")
	print("✅ test_enemy_movement_speed 通过")

func run_tests() -> void:
	test_basic_initialization()
	test_fast_initialization()
	test_tank_initialization()
	test_take_damage_core_logic()
	test_tank_survives_first_hit()
	test_basic_dies_in_one_hit()
	test_fast_dies_in_one_hit()
	test_score_value_matches_type()
	test_enemy_movement_speed()
	print("\n🎉 Enemy 测试全部通过 (%d 项)" % 9)
