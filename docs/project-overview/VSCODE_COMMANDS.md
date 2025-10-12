# VS Code Commands Reference

Quick reference for all available tasks in your Bridge Bidding App.

---

## 🎯 How to Use

1. Press **`Cmd+Shift+P`** (macOS) or **`Ctrl+Shift+P`** (Windows/Linux)
2. Type: **`Tasks: Run Task`**
3. Select from the list below

---

## 📋 Available Commands

### 🎴 Bidding Development
For working on the bidding phase of the app.

| Command | What It Does |
|---------|--------------|
| **Start Backend Bidding 🐍** | Starts Flask backend with debug mode |
| **Start Frontend Bidding 🖥️** | Starts React frontend dev server |
| **Start Bidding Project (All) 🎴** | Starts BOTH backend + frontend together |

**Use these when:** You're developing or testing bidding functionality.

---

### 🎮 Gameplay Development
For working on the card play phase of the app.

| Command | What It Does |
|---------|--------------|
| **Start Gameplay Backend 🎮** | Starts Python backend server for gameplay |
| **Start Gameplay Frontend 🎯** | Starts React frontend for gameplay |
| **Start Gameplay Testing 🎲** | Starts BOTH backend + frontend together |

**Use these when:** You're developing or testing card play functionality.

---

### 🧪 Testing Commands
For running automated tests.

| Command | What It Does |
|---------|--------------|
| **Test Standalone Play 🧪** | Runs standalone play test suite |
| **Test Contract Parser 📋** | Tests contract parsing utilities |
| **Test Play Helpers 🛠️** | Tests hand creation helpers |

**Use these when:** You want to verify the modular play system works.

---

## 🚀 Quick Start Workflows

### Workflow 1: Test Full Gameplay
```
1. Cmd+Shift+P
2. Type: "Start Gameplay Testing"
3. Select: "Start Gameplay Testing 🎲"
4. Wait for both servers to start
5. Open browser to http://localhost:3000
6. Start testing!
```

### Workflow 2: Test Bidding Only
```
1. Cmd+Shift+P
2. Type: "Start Bidding"
3. Select: "Start Bidding Project (All) 🎴"
4. Open browser to http://localhost:3000
5. Test bidding phase
```

### Workflow 3: Run Backend Tests
```
1. Cmd+Shift+P
2. Type: "Test Standalone"
3. Select: "Test Standalone Play 🧪"
4. View results in terminal
```

---

## 📊 Command Comparison

| Scenario | Use This Command |
|----------|------------------|
| Testing complete gameplay (bid + play) | **Start Gameplay Testing 🎲** |
| Developing bidding logic | **Start Bidding Project (All) 🎴** |
| Testing play module only | **Test Standalone Play 🧪** |
| Quick backend test | **Test Contract Parser 📋** |

---

## 💡 Pro Tips

### Tip 1: Use Keyboard Shortcuts
Instead of typing "Tasks: Run Task" every time:
1. Run a task once
2. Use **`Cmd+Shift+P`** → **`Tasks: Rerun Last Task`**
3. Or set custom keyboard shortcut in settings

### Tip 2: Terminal Management
Tasks are organized into groups:
- **bidding** group - All bidding tasks
- **gameplay** group - All gameplay tasks
- **testing** group - All test tasks

This keeps your terminals organized in separate panels.

### Tip 3: Background vs Foreground
- Frontend tasks run in **background** mode (continue to next task)
- Backend tasks run in **foreground** mode (wait for manual stop)
- Combined tasks run both simultaneously

### Tip 4: Stopping Tasks
To stop a running task:
1. Click on the terminal panel
2. Press **`Cmd+C`** (macOS) or **`Ctrl+C`** (Windows/Linux)
3. Or click the trash icon in terminal tab

---

## 🔧 Customization

Want to modify these tasks? Edit:
```
.vscode/tasks.json
```

### Example: Change Port
```json
{
  "label": "Start Gameplay Backend 🎮",
  "command": "cd backend && python3 server.py --port 5002"
}
```

### Example: Add New Task
```json
{
  "label": "Your Task Name 🎯",
  "type": "shell",
  "command": "your command here",
  "presentation": {
    "reveal": "always",
    "panel": "dedicated",
    "group": "your-group"
  },
  "problemMatcher": []
}
```

---

## 🐛 Troubleshooting

### "Task not found"
- Reload VS Code: `Cmd+Shift+P` → `Developer: Reload Window`
- Check `.vscode/tasks.json` syntax

### "Port already in use"
- Stop any running servers
- Check for zombie processes: `lsof -ti:5001 | xargs kill -9`

### "Command not found"
- Ensure you're in the project root directory
- Check that paths in tasks.json are correct
- Verify virtual environment exists (backend/venv)

### Frontend doesn't open browser
- Manually open http://localhost:3000
- Check that npm is installed: `npm --version`

---

## 📖 Related Documentation

- **[QUICK_TEST_CHECKLIST.md](QUICK_TEST_CHECKLIST.md)** - Quick testing guide
- **[GAMEPLAY_TESTING_GUIDE.md](GAMEPLAY_TESTING_GUIDE.md)** - Detailed gameplay testing
- **[STANDALONE_PLAY_GUIDE.md](STANDALONE_PLAY_GUIDE.md)** - Modular play architecture

---

## ✅ Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│  Press: Cmd+Shift+P                             │
│  Type:  Tasks: Run Task                         │
├─────────────────────────────────────────────────┤
│  BIDDING:                                       │
│    • Start Backend Bidding 🐍                   │
│    • Start Frontend Bidding 🖥️                  │
│    • Start Bidding Project (All) 🎴             │
├─────────────────────────────────────────────────┤
│  GAMEPLAY:                                      │
│    • Start Gameplay Backend 🎮                  │
│    • Start Gameplay Frontend 🎯                 │
│    • Start Gameplay Testing 🎲 ⭐ RECOMMENDED   │
├─────────────────────────────────────────────────┤
│  TESTING:                                       │
│    • Test Standalone Play 🧪                    │
│    • Test Contract Parser 📋                    │
│    • Test Play Helpers 🛠️                       │
└─────────────────────────────────────────────────┘
```

---

**Happy Coding! 🚀**
