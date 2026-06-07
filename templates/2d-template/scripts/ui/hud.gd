extends CanvasLayer
## HUD 界面：显示分数、暂停按钮

@onready var score_label: Label = $ScoreLabel
@onready var pause_button: Button = $PauseButton
@onready var game_over_panel: Panel = $GameOverPanel

func _ready() -> void:
	GameManager.score_changed.connect(_on_score_changed)
	GameManager.game_over.connect(_on_game_over)
	game_over_panel.hide()

func _on_score_changed(score: int) -> void:
	score_label.text = "分数: %d" % score

func _on_game_over(_final_score: int) -> void:
	game_over_panel.show()
	score_label.text = "最终分数: %d\n最高分: %d" % [GameManager.score, GameManager.high_score]

func _on_pause_button_pressed() -> void:
	if GameManager.state == GameManager.GameState.PLAYING:
		GameManager.pause_game()
	elif GameManager.state == GameManager.GameState.PAUSED:
		GameManager.resume_game()
