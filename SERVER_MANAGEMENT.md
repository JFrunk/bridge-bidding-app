# Server Management Quick Reference

## Quick Start

### Restart Both Servers
```bash
/restart
```
Or manually:
```bash
./.claude/scripts/restart_servers.sh
```

---

## Server URLs

- **Backend:** http://localhost:5001
- **Frontend:** http://localhost:3000

---

## Manual Start/Stop

### Start Servers

**Backend:**
```bash
cd backend
source venv/bin/activate
python3 server.py
```

**Frontend:**
```bash
cd frontend
npm start
```

### Stop Servers

**Kill by port:**
```bash
lsof -ti:5001 -ti:3000 | xargs kill -9
```

**Kill by process name:**
```bash
pkill -f "python.*server.py"
pkill -f "node.*react-scripts"
```

**Kill by PID (if using background mode):**
```bash
kill -9 $(cat backend_server.pid) $(cat frontend_server.pid)
```

---

## Logs

When running in background mode (via `/restart`):

- **Backend logs:** `backend_server.log`
- **Frontend logs:** `frontend_server.log`

**View logs in real-time:**
```bash
tail -f backend_server.log
tail -f frontend_server.log
```

---

## Process Information

**Check what's running on ports:**
```bash
lsof -i:5001
lsof -i:3000
```

**Find server PIDs:**
```bash
cat backend_server.pid
cat frontend_server.pid
```

---

## Troubleshooting

### Port Already in Use

If you get "address already in use" errors:

```bash
# Find and kill process on port 5001
lsof -ti:5001 | xargs kill -9

# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Frontend Won't Start

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Backend Won't Start

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

### Check Server Status

```bash
# Backend
curl http://localhost:5001/

# Frontend
curl http://localhost:3000/
```

Both should return HTML if running.

---

## Development Workflow

1. **Start servers:** `/restart` or `./.claude/scripts/restart_servers.sh`
2. **Make code changes**
3. **Frontend auto-reloads** (no restart needed)
4. **Backend requires restart** after Python changes
5. **View logs** if issues occur
6. **Stop servers** when done developing

---

## Related Files

- **Restart script:** `.claude/scripts/restart_servers.sh`
- **Restart command:** `.claude/commands/restart.md`
- **Backend code:** `backend/server.py`
- **Frontend code:** `frontend/src/`
