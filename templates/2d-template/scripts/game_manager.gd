extends Node
## 全局游戏状态管理
## AutoLoad 单例，跨场景持久化

signal game_started()
signal game_paused(is_paused: bool)
signal game_over(final_score: int)
signal score_changed(score: int)

enum GameState { MENU, PLAYING, PAUSED, GAME_OVER }

var state: GameState = GameState.MENU
var score: int = 0
var high_score: int = 0

func _ready() -> void:
	_load_high_score()

func start_game() -> void:
	score = 0
	state = GameState.PLAYING
	game_started.emit()

func pause_game() -> void:
	state = GameState.PAUSED
	game_paused.emit(true)
	Engine.time_scale = 0.0

func resume_game() -> void:
	state = GameState.PLAYING
	game_paused.emit(false)
	Engine.time_scale = 1.0

func end_game() -> void:
	state = GameState.GAME_OVER
	Engine.time_scale = 1.0
	if score > high_score:
		high_score = score
		_save_high_score()
	game_over.emit(score)

func add_score(points: int) -> void:
	score += points
	score_changed.emit(score)

func _load_high_score() -> void:
	var cfg = ConfigFile.new()
	if cfg.load("user://settings.cfg") == OK:
		high_score = cfg.get_value("stats", "high_score", 0)

func _save_high_score() -> void:
	var cfg = ConfigFile.new()
	cfg.set_value("stats", "high_score", high_score)
	cfg.save("user://settings.cfg")
