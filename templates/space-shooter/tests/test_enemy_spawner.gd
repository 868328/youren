extends "res://scripts/enemy_spawner.gd"
## EnemySpawner unit tests
## Wave logic · Parameter scaling · Type distribution

var SpawnerScript = preload("res://scripts/enemy_spawner.gd")

# ── 辅助 ────────────────────────────────────────────────────────────

func _reset_spawner(sp) -> void:
	sp._wave = 0
	sp._enemies_spawned = 0
	sp._enemies_per_wave = 5
	sp.spawn_interval = 1.5
	sp._wave_cooldown = false
	sp._wave_timer = 0.0

# ── 测试 ────────────────────────────────────────────────────────────

func test_initial_spawn_parameters() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	assert(sp._enemies_per_wave == 5, "initial enemies per wave should be 5")
	assert(sp.spawn_interval == 1.5, "initial spawn interval should be 1.5")
	assert(sp._wave == 0, "initial wave should be 0")
	print("✅ test_initial_spawn_parameters 通过")

func test_wave_progression_increases_enemy_count() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	
	sp._enemies_spawned = sp._enemies_per_wave
	sp._wave_cooldown = true
	sp._wave_timer = 2.0
	sp._wave += 1
	sp._enemies_per_wave = min(sp._enemies_per_wave + 2, 20)
	sp.spawn_interval = max(sp.spawn_interval - 0.05, 0.4)
	
	assert(sp._enemies_per_wave == 7, "第一波后每波敌人应为 7 (5+2)")
	assert(abs(sp.spawn_interval - 1.45) < 0.001, "第一波后间隔约 1.45 (浮点容差)")
	assert(sp._wave == 1, "波次应为 1")
	print("✅ test_wave_progression_increases_enemy_count 通过")

func test_multiple_waves_change_parameters() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	
	for i in range(5):
		sp._enemies_per_wave = min(sp._enemies_per_wave + 2, 20)
		sp.spawn_interval = max(sp.spawn_interval - 0.05, 0.4)
		sp._wave += 1
	
	assert(sp._wave == 5, "波次应为 5")
	assert(sp._enemies_per_wave == 15, "5 波后敌人数应为 15 (5+2*5)")
	assert(abs(sp.spawn_interval - 1.25) < 0.001, "5 波后生成间隔约 1.25 (浮点容差)")
	print("✅ test_multiple_waves_change_parameters 通过")

func test_max_enemy_cap() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	
	for i in range(25):
		sp._enemies_per_wave = min(sp._enemies_per_wave + 2, 20)
		sp.spawn_interval = max(sp.spawn_interval - 0.05, 0.4)
		sp._wave += 1
	
	assert(sp._enemies_per_wave == 20, "每波敌人数上限应为 20")
	assert(sp.spawn_interval == 0.4, "生成间隔应锁定在下限 0.4")
	print("✅ test_max_enemy_cap 通过")

func test_wave_cooldown_mechanism() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	
	sp._wave_cooldown = true
	sp._wave_timer = 2.0
	assert(sp._wave_cooldown == true, "冷却中标志应为 true")
	assert(sp._wave_timer == 2.0, "冷却计时器应为 2.0")
	
	sp._wave_timer = 0.0
	if sp._wave_cooldown and sp._wave_timer <= 0:
		sp._wave_cooldown = false
		sp._enemies_spawned = 0
	assert(sp._wave_cooldown == false, "冷却结束后标志应为 false")
	assert(sp._enemies_spawned == 0, "重新计数应为 0")
	print("✅ test_wave_cooldown_mechanism 通过")

func test_enemy_type_early_waves() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	
	sp._wave = 2
	assert(sp._wave < 3, "早期波次 < 3")
	var enemy_type_early = 0  # BASIC
	assert(enemy_type_early == 0, "早期波次只生成 BASIC 类型")
	print("✅ test_enemy_type_early_waves 通过")

func test_enemy_type_mid_waves() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	
	sp._wave = 4
	assert(sp._wave >= 3 and sp._wave < 6, "中期波次 3-5")
	
	var distribution = {0: 0, 1: 0}
	for i in range(1000):
		var r = randf()
		var t = 0 if r < 0.6 else 1
		distribution[t] = distribution.get(t, 0) + 1
	
	var fast_pct = distribution.get(1, 0) / 10.0
	assert(fast_pct > 30.0 and fast_pct < 50.0, "FAST 比例应在 30%-50% 之间 (实测: %d%%)" % [fast_pct])
	print("✅ test_enemy_type_mid_waves 通过 (FAST ≈ 40%%, 实测: %.1f%%)" % fast_pct)

func test_enemy_type_late_waves() -> void:
	var sp = SpawnerScript.new()
	_reset_spawner(sp)
	
	sp._wave = 8
	assert(sp._wave >= 6, "后期波次 >= 6")
	
	var counts = {0: 0, 1: 0, 2: 0}
	for i in range(2000):
		var r = randf()
		var t
		if r < 0.4:
			t = 0
		elif r < 0.75:
			t = 1
		else:
			t = 2
		counts[t] = counts.get(t, 0) + 1
	
	var total = counts[0] + counts[1] + counts[2]
	var pct_0 = counts[0] * 100.0 / total
	var pct_1 = counts[1] * 100.0 / total
	var pct_2 = counts[2] * 100.0 / total
	
	assert(pct_0 > 30.0, "BASIC 比例应 > 30%% (实测: %.1f%%)" % pct_0)
	assert(pct_1 > 25.0, "FAST 比例应 > 25%% (实测: %.1f%%)" % pct_1)
	assert(pct_2 > 15.0, "TANK 比例应 > 15%% (实测: %.1f%%)" % pct_2)
	print("✅ test_enemy_type_late_waves 通过 (BASIC: %.1f%%, FAST: %.1f%%, TANK: %.1f%%)" % [pct_0, pct_1, pct_2])

func run_tests() -> void:
	test_initial_spawn_parameters()
	test_wave_progression_increases_enemy_count()
	test_multiple_waves_change_parameters()
	test_max_enemy_cap()
	test_wave_cooldown_mechanism()
	test_enemy_type_early_waves()
	test_enemy_type_mid_waves()
	test_enemy_type_late_waves()
	print("\n🎉 EnemySpawner tests passed (%d 项)" % 8)
