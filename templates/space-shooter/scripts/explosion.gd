extends Node2D
## Explosion — sprite animation frames

@export var frame_duration: float = 0.06

var _frames: Array[Texture2D] = []
var _frame_idx: int = 0
var _sprite: Sprite2D

func _ready() -> void:
	# 加载爆炸素材帧
	for i in range(1, 6):
		var tex = load("res://assets/sprites/explosion_%02d.png" % i)
		if tex:
			_frames.append(tex)
	
	if _frames.is_empty():
		queue_free()
		return
	
	_sprite = Sprite2D.new()
	_sprite.texture = _frames[0]
	_sprite.scale = Vector2(0.8, 0.8)
	_sprite.centered = true
	add_child(_sprite)
	
	# 启动帧动画
	_next_frame()

func _next_frame() -> void:
	if not is_inside_tree():
		return
	_frame_idx += 1
	if _frame_idx >= _frames.size():
		queue_free()
		return
	_sprite.texture = _frames[_frame_idx]
	var t = get_tree().create_timer(frame_duration)
	t.timeout.connect(_next_frame)
