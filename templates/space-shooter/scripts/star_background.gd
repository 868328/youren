extends Node2D
## 星空滚动背景 — 带彩色星星和星云效果

@export var star_count: int = 120
@export var min_speed: float = 20.0
@export var max_speed: float = 150.0

var _stars: Array[Dictionary] = []
var _screen_size: Vector2
var _nebula: Dictionary  # 预先计算的星云参数

func _ready() -> void:
	_screen_size = get_viewport().get_visible_rect().size
	_generate_nebula()
	_generate_stars()

func _generate_nebula() -> void:
	var colors = [
		Color(0.15, 0.05, 0.25, 0.025),  # 暗紫
		Color(0.02, 0.06, 0.15, 0.02),   # 暗蓝
		Color(0.1, 0.02, 0.1, 0.015),    # 暗粉
		Color(0.02, 0.1, 0.06, 0.015),   # 暗青
	]
	_nebula = {
		"patches": [],
	}
	for i in 4:
		_nebula["patches"].append({
			"pos": Vector2(randf_range(0.1, 0.9), randf_range(0.1, 0.9)),
			"radius": randf_range(0.25, 0.5),
			"color": colors[i],
		})

func _generate_stars() -> void:
	var star_colors = [
		Color(1, 1, 1),
		Color(0.8, 0.9, 1),
		Color(1, 0.9, 0.7),
		Color(1, 0.7, 0.5),
		Color(0.7, 0.8, 1),
	]
	
	for i in star_count:
		var c = star_colors[randi() % star_colors.size()]
		c.a = randf_range(0.3, 1.0)
		_stars.append({
			"pos": Vector2(randf_range(0, _screen_size.x), randf_range(0, _screen_size.y)),
			"speed": randf_range(min_speed, max_speed),
			"radius": randf_range(0.5, 2.5),
			"color": c,
			"twinkle": randf() > 0.7,
			"twinkle_offset": randf_range(0, TAU),
			"twinkle_speed": randf_range(1.0, 3.0),
		})

func _process(delta: float) -> void:
	queue_redraw()
	for star in _stars:
		star["pos"].y += star["speed"] * delta
		if star["pos"].y > _screen_size.y:
			star["pos"].y = -5
			star["pos"].x = randf_range(0, _screen_size.x)

func _draw() -> void:
	var time = Time.get_ticks_msec() / 1000.0
	var size = _screen_size
	
	# 星云色块
	for p in _nebula["patches"]:
		var cx = p["pos"].x * size.x
		var cy = p["pos"].y * size.y
		var r = p["radius"] * size.y
		draw_circle(Vector2(cx, cy), r, p["color"])
	
	# 画星星
	for star in _stars:
		var alpha = star["color"].a
		if star["twinkle"]:
			var tw = sin(time * star["twinkle_speed"] + star["twinkle_offset"]) * 0.3 + 0.7
			alpha *= tw
		
		var c = Color(star["color"].r, star["color"].g, star["color"].b, alpha)
		draw_circle(star["pos"], star["radius"], c)
		
		# 大星星光晕
		if star["radius"] > 1.8:
			var glow = Color(c.r, c.g, c.b, alpha * 0.15)
			draw_circle(star["pos"], star["radius"] * 2.5, glow)
