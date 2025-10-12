#!/bin/bash
echo "🎓 Bridge Convention Levels Viewer"
echo "=================================="
echo ""
echo "Starting Flask server..."
python3 server.py &
SERVER_PID=$!

sleep 2

echo ""
echo "✅ Server started on http://localhost:5001"
echo ""
echo "Opening test page in browser..."
open test_conventions.html

echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Wait for user interrupt
trap "kill $SERVER_PID 2>/dev/null; echo ''; echo 'Server stopped. Goodbye!'; exit" INT
wait
