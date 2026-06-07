extends Node
## Global game state — AutoLoad singleton

signal game_started()
signal score_changed(score: int)
signal lives_changed(lives: int)
signal game_over(final_score: int)

var score: int = 0
var lives: int = 3
var high_score: int = 0
var is_playing: bool = false

func _ready() -> void:
	_load_high_score()

func start_game() -> void:
	score = 0
	lives = 3
	is_playing = true
	game_started.emit()
	score_changed.emit(score)
	lives_changed.emit(lives)

func add_score(points: int) -> void:
	score += points
	score_changed.emit(score)

func lose_life() -> void:
	lives -= 1
	lives_changed.emit(lives)
	if lives <= 0:
		is_playing = false
		if score > high_score:
			high_score = score
			_save_high_score()
		game_over.emit(score)

func _load_high_score() -> void:
	var cfg = ConfigFile.new()
	if cfg.load("user://settings.cfg") == OK:
		high_score = cfg.get_value("stats", "high_score", 0)

func _save_high_score() -> void:
	var cfg = ConfigFile.new()
	cfg.set_value("stats", "high_score", high_score)
	cfg.save("user://settings.cfg")
