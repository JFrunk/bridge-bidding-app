#!/bin/bash
# Script to automatically add session headers to all fetch calls in App.js

cd "$(dirname "$0")/src"

# Backup App.js
cp App.js App.js.backup_$(date +%Y%m%d_%H%M%S)

echo "Updating App.js with session headers..."

# Create a temporary Python script to do the replacements
python3 << 'PYTHON_SCRIPT'
import re

# Read the file
with open('App.js', 'r') as f:
    content = f.read()

# Pattern 1: Simple GET requests without any options
# fetch(`${API_URL}/api/endpoint`)
pattern1 = r"fetch\(\`\$\{API_URL\}(/api/[^`]+)\`\)"
replacement1 = r"fetch(`${API_URL}\1`, { headers: { ...getSessionHeaders() } })"
content = re.sub(pattern1, replacement1, content)

# Pattern 2: Requests with headers but no session headers
# headers: { 'Content-Type': 'application/json' }
pattern2 = r"headers:\s*\{\s*['\"]Content-Type['\"]\s*:\s*['\"]application/json['\"]\s*\}"
replacement2 = r"headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }"
content = re.sub(pattern2, replacement2, content)

# Pattern 3: Requests with just headers: {}
pattern3 = r"headers:\s*\{\s*\}"
replacement3 = r"headers: { ...getSessionHeaders() }"
content = re.sub(pattern3, replacement3, content)

# Write back
with open('App.js', 'w') as f:
    f.write(content)

print("✅ App.js updated successfully")

# Count changes
import_count = content.count('getSessionHeaders')
print(f"📊 Session headers added to {import_count - 1} locations")
PYTHON_SCRIPT

echo ""
echo "✅ Done! App.js has been updated."
echo "📦 Backup saved as App.js.backup_*"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff src/App.js"
echo "  2. Test the app: npm start"
echo "  3. Check browser console for session ID"
echo ""
