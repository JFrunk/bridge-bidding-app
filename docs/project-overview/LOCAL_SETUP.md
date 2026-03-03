# Local Development Setup

**Last Updated:** 2026-03-02

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **PostgreSQL** — recommended: [Postgres.app](https://postgresapp.com/) for macOS

---

## 1. Clone the Repository

```bash
git clone https://github.com/JFrunk/bridge-bidding-app.git
cd bridge-bidding-app
```

---

## 2. PostgreSQL Setup

### Install PostgreSQL

**macOS (Postgres.app — recommended):**
1. Download from https://postgresapp.com/
2. Move to Applications and launch
3. Click "Initialize" to create a default server
4. The app runs on port 5432 by default

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

### Create the Database

Find your `psql` binary and create the database:

```bash
# Postgres.app — psql is inside the app bundle
/Applications/Postgres.app/Contents/Versions/18/bin/psql -c "CREATE DATABASE bridge_app;"

# Homebrew — psql is on PATH
psql -c "CREATE DATABASE bridge_app;"
```

### Find Your Database URL

The `DATABASE_URL` format is: `postgresql://<user>@localhost:5432/bridge_app`

To find your PostgreSQL username:

```bash
# Postgres.app — defaults to your macOS username
whoami
# Example output: simonroy
# → DATABASE_URL=postgresql://simonroy@localhost:5432/bridge_app

# Homebrew — also defaults to macOS username, or check with:
psql -c "SELECT current_user;"
```

To verify the database exists and you can connect:

```bash
# List all databases (use your psql path)
psql -l
# or
/Applications/Postgres.app/Contents/Versions/18/bin/psql -l

# Look for "bridge_app" in the output
```

---

## 3. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment

Create `backend/.env` with your database connection:

```bash
# Copy the example and add DATABASE_URL
cp .env.example .env
```

Add this line to `backend/.env`:

```
DATABASE_URL=postgresql://<your-username>@localhost:5432/bridge_app
```

Replace `<your-username>` with your PostgreSQL username (usually your macOS username — run `whoami` to check).

### Initialize Database Tables

```bash
source venv/bin/activate
python3 database/init_all_tables.py
```

### Start the Backend

```bash
source venv/bin/activate
python server.py
```

The Flask server starts on **http://localhost:5001**.

---

## 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The React dev server starts on **http://localhost:3000** and proxies API requests to port 5001.

---

## 5. Verify Everything Works

Open http://localhost:3000 in your browser. You should see the app load and be able to deal a hand.

Quick API check from the terminal:

```bash
curl -s http://localhost:5001/api/deal-hands | head -c 100
```

---

## Running Both Servers

### Manual Start

```bash
# Terminal 1 — Backend
cd backend && source venv/bin/activate && python server.py

# Terminal 2 — Frontend
cd frontend && npm start
```

### Using the Restart Script

```bash
# From project root
./.claude/scripts/restart_servers.sh
```

This stops any existing servers and starts both in the background. Logs go to `backend_server.log` and `frontend_server.log`.

---

## Common Issues

### `ModuleNotFoundError: No module named 'dotenv'`
The virtualenv wasn't activated. Run `source venv/bin/activate` before starting the server.

### `RuntimeError: DATABASE_URL environment variable is required`
Create `backend/.env` with your `DATABASE_URL`. See step 3 above.

### `psql: command not found`
Postgres.app doesn't add `psql` to PATH by default. Use the full path:
```bash
/Applications/Postgres.app/Contents/Versions/18/bin/psql
```
Or add to your shell profile:
```bash
export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
```

### DDS crashes on macOS (Apple Silicon)
The `endplay` library's DDS solver only works on x86_64 Linux. On macOS M1/M2/M3, use AI difficulty level 8 (Minimax) instead of 9-10 (DDS). The server auto-detects this — no action needed.

---

## Database Migrations

When pulling new code that includes migrations in `backend/migrations/`:

```bash
# Apply to local database
/Applications/Postgres.app/Contents/Versions/18/bin/psql -d bridge_app -f backend/migrations/<migration_file>.sql

# Or if psql is on PATH
psql -d bridge_app -f backend/migrations/<migration_file>.sql
```

See [DEPLOY_GUIDE.md](../../.claude/DEPLOY_GUIDE.md) for production migration procedures.
