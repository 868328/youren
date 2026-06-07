extends Area2D
## Player ship

@export var speed: float = 400.0
@export var fire_rate: float = 0.2

@onready var sprite: Sprite2D = $Sprite2D
@onready var muzzle: Marker2D = $Muzzle
@onready var shoot_timer: Timer = $ShootTimer
@onready var invincible_timer: Timer = $InvincibleTimer

var _can_shoot: bool = true
var _invincible: bool = false
var _input_dir: float = 0.0
var _screen_size: Vector2

func _ready() -> void:
	_screen_size = get_viewport().get_visible_rect().size
	shoot_timer.wait_time = fire_rate
	position.x = _screen_size.x / 2.0
	position.y = _screen_size.y - 60
	add_to_group("player")
	_generate_ship_texture()

func _generate_ship_texture() -> void:
	var tex = load("res://assets/sprites/player_ship.png")
	if tex:
		sprite.texture = tex
	else:
		# Fallback: simple colored square
		var img = Image.create(32, 32, false, Image.FORMAT_RGBA8)
		img.fill(Color(0.2, 0.6, 1.0, 1.0))
		sprite.texture = ImageTexture.create_from_image(img)

func _process(delta: float) -> void:
	if not GameManager.is_playing:
		return
	
	_input_dir = Input.get_axis("move_left", "move_right")
	if _input_dir != 0:
		position.x += _input_dir * speed * delta
		position.x = clamp(position.x, 20, _screen_size.x - 20)
	
	if Input.is_action_pressed("shoot") and _can_shoot:
		_fire()

func _fire() -> void:
	_can_shoot = false
	shoot_timer.start()
	
	var bullet = preload("res://scenes/bullet.tscn").instantiate()
	bullet.position = muzzle.global_position
	get_tree().current_scene.add_child(bullet)

func _on_shoot_timer_timeout() -> void:
	_can_shoot = true

func hit() -> void:
	if _invincible or not GameManager.is_playing:
		return
	
	GameManager.lose_life()
	
	if GameManager.is_playing:
		_invincible = true
		invincible_timer.start()
		var tween = create_tween()
		tween.tween_property(sprite, "modulate:a", 0.3, 0.1)
		tween.tween_property(sprite, "modulate:a", 1.0, 0.1)
		tween.set_loops(5)
		tween.finished.connect(func(): sprite.modulate.a = 1.0)

func _on_invincible_timer_timeout() -> void:
	_invincible = false
	sprite.modulate.a = 1.0

func _on_area_entered(area: Area2D) -> void:
	if area.is_in_group("enemies"):
		hit()
		area.queue_free()
