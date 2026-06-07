extends CanvasLayer
## In-game HUD — score, lives, game over

@onready var score_label: Label = $ScoreLabel
@onready var lives_label: Label = $LivesLabel
@onready var game_over_panel: Panel = $GameOverPanel
@onready var final_score_label: Label = $GameOverPanel/FinalScoreLabel
@onready var high_score_label: Label = $GameOverPanel/HighScoreLabel
@onready var restart_button: Button = $GameOverPanel/RestartButton
@onready var menu_button: Button = $GameOverPanel/MenuButton

func _ready() -> void:
	GameManager.score_changed.connect(_on_score_changed)
	GameManager.lives_changed.connect(_on_lives_changed)
	GameManager.game_over.connect(_on_game_over)
	game_over_panel.hide()

func _on_score_changed(score: int) -> void:
	score_label.text = "Score: %d" % score

func _on_lives_changed(lives: int) -> void:
	var hearts := ""
	for i in max(lives, 0):
		hearts += "❤️"
	lives_label.text = "Lives: " + hearts

func _on_game_over(final_score: int) -> void:
	game_over_panel.show()
	final_score_label.text = "Score: %d" % final_score
	high_score_label.text = "Best: %d" % GameManager.high_score
	restart_button.grab_focus()

func _on_restart_button_pressed() -> void:
	get_tree().reload_current_scene()
	GameManager.start_game()

func _on_menu_button_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
