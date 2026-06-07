#!/usr/bin/env godot --headless --script
## Test runner
## 遍历 tests/ 下所有 *_test.gd 并运行
## 用法: godot --headless --path /path/to/project --script tests/run_tests.gd

extends SceneTree

func _init() -> void:
	print("🧪 运行测试...\n")
	
	var test_dir = DirAccess.open("res://tests/")
	if not test_dir:
		push_error("测试目录不存在")
		quit(1)
		return
	
	var passed = 0
	var failed = 0
	
	test_dir.list_dir_begin()
	var file_name = test_dir.get_next()
	while file_name != "":
		if file_name.ends_with("_test.gd") or file_name.ends_with("test.gd"):
			if file_name == "run_tests.gd":
				file_name = test_dir.get_next()
				continue
			var path = "res://tests/" + file_name
			print("运行: ", file_name)
			var script = load(path)
			if script:
				var instance = script.new()
				if instance.has_method("run_tests"):
					instance.run_tests()
					passed += 1
				else:
					failed += 1
					push_error("缺少 run_tests() 方法: ", file_name)
			else:
				failed += 1
				push_error("加载失败: ", file_name)
		file_name = test_dir.get_next()
	test_dir.list_dir_end()
	
	print("\n📊 结果: %d 通过, %d 失败" % [passed, failed])
	quit(0 if failed == 0 else 1)
