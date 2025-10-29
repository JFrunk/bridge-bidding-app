#!/bin/bash

# Restart Backend and Frontend Development Servers
# This script stops any running servers and starts fresh instances

set -e  # Exit on error

PROJECT_ROOT="/Users/simonroy/Desktop/bridge_bidding_app"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "🔄 Restarting Development Servers"
echo "=================================================="

# Step 1: Stop existing processes
echo ""
echo "1️⃣  Stopping existing processes..."

# Kill processes on ports 5001 and 3000
if lsof -ti:5001 -ti:3000 >/dev/null 2>&1; then
    echo "   • Killing processes on ports 5001 and 3000..."
    lsof -ti:5001 -ti:3000 | xargs kill -9 2>/dev/null || true
else
    echo "   • No processes found on ports 5001 or 3000"
fi

# Kill Python server processes
if pgrep -f "python.*server.py" >/dev/null 2>&1; then
    echo "   • Killing Python server processes..."
    pkill -f "python.*server.py" || true
else
    echo "   • No Python server processes found"
fi

# Kill React dev server processes
if pgrep -f "node.*react-scripts" >/dev/null 2>&1; then
    echo "   • Killing React dev server processes..."
    pkill -f "node.*react-scripts" || true
else
    echo "   • No React processes found"
fi

# Clean up old log files
rm -f backend_server.log frontend_server.log
rm -f backend_server.pid frontend_server.pid

sleep 2

# Step 2: Start backend server
echo ""
echo "2️⃣  Starting backend server..."
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
nohup python3 server.py > ../backend_server.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend_server.pid
echo "   ✅ Backend started (PID: $BACKEND_PID)"
echo "   📋 Logs: backend_server.log"

# Step 3: Start frontend server
echo ""
echo "3️⃣  Starting frontend server..."
cd "$PROJECT_ROOT/frontend"
nohup npm start > ../frontend_server.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend_server.pid
echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
echo "   📋 Logs: frontend_server.log"

# Step 4: Verify servers are running
echo ""
echo "4️⃣  Verifying servers (waiting 8 seconds for startup)..."
sleep 8

BACKEND_STATUS="❌ Not responding"
FRONTEND_STATUS="❌ Not responding"

if curl -s http://localhost:5001/ >/dev/null 2>&1; then
    BACKEND_STATUS="✅ Running"
fi

if curl -s http://localhost:3000/ >/dev/null 2>&1; then
    FRONTEND_STATUS="✅ Running"
fi

echo ""
echo "=================================================="
echo "📊 Server Status"
echo "=================================================="
echo "Backend (port 5001):  $BACKEND_STATUS"
echo "Frontend (port 3000): $FRONTEND_STATUS"
echo ""
echo "🌐 URLs:"
echo "   • Backend:  http://localhost:5001"
echo "   • Frontend: http://localhost:3000"
echo ""
echo "🛑 To stop servers:"
echo "   kill -9 $BACKEND_PID $FRONTEND_PID"
echo "   OR:"
echo "   lsof -ti:5001 -ti:3000 | xargs kill -9"
echo "=================================================="
