---
description: Restart backend and frontend development servers
---

Execute the restart script to stop and start both development servers:

```bash
./.claude/scripts/restart_servers.sh
```

This will:
1. Stop existing processes on ports 5001 and 3000
2. Kill any Python server.py and React dev server processes
3. Start backend Flask server in background (port 5001)
4. Start frontend React dev server in background (port 3000)
5. Verify both servers are running

Logs are saved to:
- `backend_server.log`
- `frontend_server.log`

Process IDs:
- `backend_server.pid`
- `frontend_server.pid`
