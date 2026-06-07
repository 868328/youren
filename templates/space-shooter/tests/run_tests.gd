#!/usr/bin/env godot --headless --script
## Test runner
## Scans tests/ for test_*.gd files and runs them
##
## Usage:
##   godot --path /path/to/project --script tests/run_tests.gd

extends SceneTree

func _init() -> void:
	print("🧪 Space Shooter — Running unit tests...")
	# Don't load AutoLoad-dependent test scripts during _init() (deadlock risk)
	# Use call_deferred to run after SceneTree initialization
	call_deferred("_run_all_tests")

func _run_all_tests() -> void:
	print("🧪 Running tests...\n")

	var test_dir = DirAccess.open("res://tests/")
	if not test_dir:
		push_error("❌ Test directory not found (res://tests/)")
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
			print("▶ Running: ", file_name)
			var script = load(path)
			if script:
				var instance = script.new()
				if instance.has_method("run_tests"):
					instance.run_tests()
					results.append({"file": file_name, "ok": true})
					passed += 1
				else:
					failed += 1
					push_error("❌ Missing run_tests() method: ", file_name)
					results.append({"file": file_name, "ok": false, "error": "Missing run_tests()"})
			else:
				failed += 1
				push_error("❌ Failed to load: ", file_name)
				results.append({"file": file_name, "ok": false, "error": "Script load failed"})
		file_name = test_dir.get_next()
	test_dir.list_dir_end()

	var out = PackedStringArray()
	var sep = "=".repeat(50)
	out.append(sep)
	out.append("📊 Test Summary:")
	for r in results:
		if r.ok:
			var line = "   ✅ %s" % r.file
			print(line)
			out.append(line)
		else:
			var line = "   ❌ %s — %s" % [r.file, r.get("error", "FAILED")]
			push_error(line)
			out.append(line)
	var final_line = "📊 Results: %d passed, %d failed" % [passed, failed]
	print(final_line)
	out.append(final_line)
	print(sep)
	out.append(sep)
	
	# Write results to file for reading from WSL
	var text = "\n".join(out)
	var f = FileAccess.open("res://_test_results.txt", FileAccess.WRITE)
	if f:
		f.store_string(text)
		f.close()
	quit(0 if failed == 0 else 1)
