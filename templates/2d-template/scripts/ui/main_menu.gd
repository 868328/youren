extends CanvasLayer
## 主菜单界面

@onready var start_button: Button = $StartButton
@onready var quit_button: Button = $QuitButton
@onready var high_score_label: Label = $HighScoreLabel

func _ready() -> void:
	high_score_label.text = "最高分: %d" % GameManager.high_score
	start_button.grab_focus()

func _on_start_button_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_quit_button_pressed() -> void:
	get_tree().quit()
