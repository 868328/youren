extends Area2D
## Enemy

enum EnemyType { BASIC, FAST, TANK }

@export var type: EnemyType = EnemyType.BASIC

var speed: float = 150.0
var hp: int = 1
var score_value: int = 100
var _screen_height: float = 0.0

func _ready() -> void:
	_screen_height = get_viewport().get_visible_rect().size.y
	add_to_group("enemies")
	match type:
		EnemyType.BASIC:
			speed = 150.0; hp = 1; score_value = 100
			_set_ship_texture("enemy_basic_01.png")
		EnemyType.FAST:
			speed = 280.0; hp = 1; score_value = 150
			_set_ship_texture("enemy_fast_01.png")
		EnemyType.TANK:
			speed = 80.0; hp = 3; score_value = 300
			_set_ship_texture("enemy_tank_01.png")

func _set_ship_texture(name: String) -> void:
	var tex = load("res://assets/sprites/" + name)
	if tex:
		$Sprite2D.texture = tex

func _process(delta: float) -> void:
	position.y += speed * delta
	if position.y > _screen_height + 50:
		queue_free()

func take_damage(dmg: int = 1) -> void:
	hp -= dmg
	if hp <= 0:
		GameManager.add_score(score_value)
		_spawn_explosion()
		queue_free()
	else:
		var tween = create_tween()
		tween.tween_property($Sprite2D, "modulate", Color(2, 2, 2), 0.05)
		tween.tween_property($Sprite2D, "modulate", Color.WHITE, 0.05)

func _spawn_explosion() -> void:
	var explosion = preload("res://scenes/explosion.tscn").instantiate()
	explosion.position = position
	get_tree().current_scene.add_child(explosion)

func _on_area_entered(area: Area2D) -> void:
	if area.is_in_group("player"):
		_spawn_explosion()
		queue_free()
