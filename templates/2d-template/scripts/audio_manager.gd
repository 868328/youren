extends Node
## 音效管理
## AutoLoad 单例，通过 AudioStreamPlayer2D 播放

const SFX_DIR := "res://assets/audio/"

var _players: Array[AudioStreamPlayer2D] = []
var _music_player: AudioStreamPlayer

func _ready() -> void:
	# 准备 4 个音效通道
	for i in range(4):
		var p := AudioStreamPlayer2D.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	
	# 音乐播放器
	_music_player = AudioStreamPlayer.new()
	_music_player.bus = "Music"
	add_child(_music_player)

func play_sfx(name: String) -> void:
	var path := SFX_DIR + name + ".ogg"
	if not ResourceLoader.exists(path):
		push_warning("SFX not found: ", path)
		return
	for p in _players:
		if not p.playing:
			p.stream = load(path)
			p.play()
			return

func play_music(name: String, loop: bool = true) -> void:
	var path := SFX_DIR + name + ".ogg"
	if not ResourceLoader.exists(path):
		push_warning("Music not found: ", path)
		return
	_music_player.stream = load(path)
	_music_player.autoplay = loop
	if loop:
		_music_player.finished.connect(_music_player.play, CONNECT_ONE_SHOT)
	_music_player.play()

func stop_music() -> void:
	_music_player.stop()
