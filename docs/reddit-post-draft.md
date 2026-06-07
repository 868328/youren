# r/godot 帖子草稿

## 标题选项

**A（直接型）：**
> Youren — Open-Source AI Toolkit for Godot: Your LLM Writes GDScript, Builds & Runs Tests Locally

**B（吸引型）：**
> I built an open-source bridge that lets AI write Godot games directly — no cloud, no API costs, 29 unit tests pass

**C（社区风格）：**
> Making Godot games with AI assistance: Youren lets LLMs write GDScript, run headless tests, and export .exe — all locally

**推荐：B** — 吸引眼球，突出差异化

---

## 帖子正文

```
I've been working on an open-source tool called Youren (游刃) that bridges AI with Godot for local game development.

👉 https://github.com/868328/youren

What it does:

WSL/Linux ──JSON Bridge──> agent.py (Windows) ──> Godot 4.x

You write game code with an LLM, it saves to the project directory, 
Godot compiles, runs 29 automated tests, and exports the build — 
all locally, no API calls, no data leaving your machine.

The space shooter template includes:
- 3 enemy types (basic, fast, tank) with wave progression
- Auto-saved high scores
- Star background with nebula effects
- 29 GDScript unit tests covering game manager, enemy spawning, and damage systems
- One-click build scripts (build.sh + build.bat)

Why I built this:
Most AI game dev tools are cloud SaaS — pay per call, data goes to third parties. 
I wanted something that runs entirely on my RTX 5090 laptop with zero ongoing costs.

Tech stack:
- Godot 4.6 (GDScript) 
- Python agent for Windows ↔ WSL bridge
- MIT License

GitHub: https://github.com/868328/youren

Would love to hear feedback from the community! What would you add? 🎮
```

---

## 发帖建议

| 事项 | 建议 |
|------|------|
| **发送时间** | 晚上 9-11 点（美东时间）→ 欧洲刚起床 + 美国刚下班 |
| **带上素材** | 15-30 秒录屏效果远超纯文字 |
| **准备接反馈** | 有人可能会问"跟 LangChain 有什么区别"、"能用 OpenAI 吗" |
| **Flair** | `Showcase` 或 `Project` |

---

## 可能的 Q&A 预备

**Q: Why WSL? Why not just run on Windows directly?**
A: Most LLM tooling (OpenClaw, Ollama) is more mature on Linux. WSL gives us the best of both worlds.

**Q: Can I use this with ChatGPT / Claude / any LLM?**
A: Yes! Youren is LLM-agnostic — it just needs a file bridge. Any AI that can write files works.

**Q: Is this just a Godot wrapper around an existing framework?**
A: No — the WSL↔Windows bridge and the agent.py protocol are original work. The game templates are for demonstration.

**Q: Why not use --headless?**
A: Godot console + --headless hangs on Windows. Console version works fine without it.

---

## 发布后跟进

- [ ] 30分钟后检查评论，回复问题
- [ ] 如果有人感兴趣，跨贴到 Godot Forum
- [ ] 记录 star 数和反馈
