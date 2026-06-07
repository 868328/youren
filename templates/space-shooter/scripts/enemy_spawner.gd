extends Node
## 敌人生成器 — 按波次生成

@export var spawn_interval: float = 1.5
@export var spawn_margin: float = 30.0

var _screen_size: Vector2
var _wave: int = 0
var _spawn_timer: float = 0.0
var _enemies_spawned: int = 0
var _enemies_per_wave: int = 5
var _wave_cooldown: bool = false
var _wave_timer: float = 0.0

func _ready() -> void:
	_screen_size = get_viewport().get_visible_rect().size

func _process(delta: float) -> void:
	if not GameManager.is_playing:
		return
	
	if _wave_cooldown:
		_wave_timer -= delta
		if _wave_timer <= 0:
			_wave_cooldown = false
			_enemies_spawned = 0
		return
	
	_spawn_timer -= delta
	if _spawn_timer <= 0:
		_spawn_enemy()
		_enemies_spawned += 1
		_spawn_timer = spawn_interval
		
		if _enemies_spawned >= _enemies_per_wave:
			_wave_cooldown = true
			_wave_timer = 2.0
			_wave += 1
			# 每波变难
			_enemies_per_wave = min(_enemies_per_wave + 2, 20)
			spawn_interval = max(spawn_interval - 0.05, 0.4)

func _spawn_enemy() -> void:
	var enemy_type: int
	var r = randf()
	if _wave < 3:
		enemy_type = 0  # BASIC
	elif _wave < 6:
		enemy_type = 0 if r < 0.6 else 1  # BASIC + FAST
	else:
		if r < 0.4:
			enemy_type = 0
		elif r < 0.75:
			enemy_type = 1
		else:
			enemy_type = 2  # TANK
	
	var enemy = preload("res://scenes/enemy.tscn").instantiate()
	enemy.type = enemy_type
	enemy.position.x = randf_range(spawn_margin, _screen_size.x - spawn_margin)
	enemy.position.y = -30
	get_tree().current_scene.add_child(enemy)
