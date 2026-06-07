extends "res://scripts/game_manager.gd"
## GameManager 单元测试
## 运行方法: godot --headless --script tests/test_game_manager.gd

func test_score_management() -> void:
	var mgr = GameManager.new()
	mgr.add_score(10)
	assert(mgr.score == 10, "初始加分失败")
	mgr.add_score(25)
	assert(mgr.score == 35, "累加失败")
	print("✅ test_score_management 通过")

func test_game_state_transitions() -> void:
	var mgr = GameManager.new()
	assert(mgr.state == GameManager.GameState.MENU, "初始状态应为 MENU")
	mgr.start_game()
	assert(mgr.state == GameManager.GameState.PLAYING, "start_game 后应为 PLAYING")
	mgr.pause_game()
	assert(mgr.state == GameManager.GameState.PAUSED, "pause 后应为 PAUSED")
	mgr.resume_game()
	assert(mgr.state == GameManager.GameState.PLAYING, "resume 后应为 PLAYING")
	mgr.end_game()
	assert(mgr.state == GameManager.GameState.GAME_OVER, "end 后应为 GAME_OVER")
	print("✅ test_game_state_transitions 通过")

func run_tests() -> void:
	test_score_management()
	test_game_state_transitions()
	print("\n🎉 所有测试通过")
