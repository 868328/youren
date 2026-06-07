#!/usr/bin/env godot --headless --script
## 测试运行器
## 遍历 tests/ 下所有 _test.gd 文件并运行
##
## 用法:
##   godot --headless --path /path/to/project --script tests/run_tests.gd
##
## 从 templates/2d-template/tests/ 适配而来

extends SceneTree

func _init() -> void:
	print("🧪 打飞机 单元测试 — 准备中...")
	# SceneTree._init() 期间不要加载依赖 AutoLoad 的脚本（会死锁）
	# 用 call_deferred 等初始化完成再跑
	call_deferred("_run_all_tests")

func _run_all_tests() -> void:
	print("🧪 运行测试...\n")

	var test_dir = DirAccess.open("res://tests/")
	if not test_dir:
		push_error("❌ 测试目录不存在 (res://tests/)")
		quit(1)
		return

	var passed = 0
	var failed = 0
	var results = []

	test_dir.list_dir_begin()
	var file_name = test_dir.get_next()
	while file_name != "":
		if file_name.begins_with("test_") and file_name.ends_with(".gd"):
			if file_name == "run_tests.gd":
				file_name = test_dir.get_next()
				continue
			var path = "res://tests/" + file_name
			print("▶ 运行: ", file_name)
			var script = load(path)
			if script:
				var instance = script.new()
				if instance.has_method("run_tests"):
					var old_stdout = print
					instance.run_tests()
					results.append({"file": file_name, "ok": true})
					passed += 1
				else:
					failed += 1
					push_error("❌ 缺少 run_tests() 方法: ", file_name)
					results.append({"file": file_name, "ok": false, "error": "缺少 run_tests()"})
			else:
				failed += 1
				push_error("❌ 加载失败: ", file_name)
				results.append({"file": file_name, "ok": false, "error": "脚本加载失败"})
		file_name = test_dir.get_next()
	test_dir.list_dir_end()

	var out = PackedStringArray()
	var sep = "=".repeat(50)
	out.append(sep)
	out.append("📊 测试汇总:")
	for r in results:
		if r.ok:
			var line = "   ✅ %s" % r.file
			print(line)
			out.append(line)
		else:
			var line = "   ❌ %s — %s" % [r.file, r.get("error", "失败")]
			push_error(line)
			out.append(line)
	var final_line = "📊 结果: %d 通过, %d 失败" % [passed, failed]
	print(final_line)
	out.append(final_line)
	print(sep)
	out.append(sep)
	
	# 写入结果文件到项目根目录（WSL 可直接读取）
	var text = "\n".join(out)
	var f = FileAccess.open("res://_test_results.txt", FileAccess.WRITE)
	if f:
		f.store_string(text)
		f.close()
	quit(0 if failed == 0 else 1)
