extends CharacterBody2D
## 通用 2D 玩家控制器
## 支持移动、跳跃、重力

@export var speed: float = 300.0
@export var jump_velocity: float = -400.0
@export var acceleration: float = 0.2
@export var friction: float = 0.1
@export var air_resistance: float = 0.05

@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var sprite: Sprite2D = $Sprite2D

var _velocity: Vector2 = Vector2.ZERO
var _input_dir: float = 0.0
var _jump_pressed: bool = false

func _physics_process(delta: float) -> void:
	# 输入
	_input_dir = Input.get_axis("ui_left", "ui_right")
	_jump_pressed = Input.is_action_just_pressed("ui_jump")
	
	# 水平移动
	if _input_dir != 0:
		_velocity.x = lerp(_velocity.x, _input_dir * speed, acceleration)
		sprite.flip_h = _input_dir < 0
	else:
		_velocity.x = lerp(_velocity.x, 0.0, friction if is_on_floor() else air_resistance)
	
	# 跳跃
	if _jump_pressed and is_on_floor():
		_velocity.y = jump_velocity
	
	# 重力
	if not is_on_floor():
		_velocity.y += get_gravity().y * delta
	
	# 应用移动
	velocity = _velocity
	move_and_slide()
	
	# 动画
	_update_animation()

func _update_animation() -> void:
	if not animation_player:
		return
	if not is_on_floor():
		animation_player.play("jump" if _velocity.y < 0 else "fall")
	elif _input_dir != 0:
		animation_player.play("run")
	else:
		animation_player.play("idle")
