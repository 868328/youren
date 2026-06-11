#!/bin/bash
# 每周需求探寻扫描
# 由 cron 触发

cd "$(dirname "$0")"

# 扫描
python3 scanner.py --keywords "godot,indie game,gamedev" --sources github,bilibili >> data/scan_log.txt 2>&1

# 生成报告
python3 scanner.py --report >> data/scan_log.txt 2>&1

# 清理过期
python3 scanner.py --cleanup >> data/scan_log.txt 2>&1
