extends Area2D
## 玩家子弹

@export var speed: float = 600.0
@export var damage: int = 1

var _screen_height: float = 0.0

func _ready() -> void:
	_screen_height = get_viewport().get_visible_rect().size.y
	add_to_group("bullets")
	_set_bullet_texture()

func _set_bullet_texture() -> void:
	var tex = load("res://assets/sprites/bullet_01.png")
	if tex:
		$Sprite2D.texture = tex

func _process(delta: float) -> void:
	position.y -= speed * delta
	if position.y < -20:
		queue_free()

func _on_area_entered(area: Area2D) -> void:
	if area.is_in_group("enemies"):
		area.take_damage(damage)
		queue_free()
