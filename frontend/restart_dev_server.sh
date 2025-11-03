#!/bin/bash

echo "=== Restarting React Dev Server ==="

# Kill any running react-scripts processes
echo "1. Stopping existing dev servers..."
pkill -f react-scripts
sleep 2

# Clear all caches
echo "2. Clearing caches..."
rm -rf node_modules/.cache
rm -rf .cache
rm -rf build

# Restart the dev server
echo "3. Starting fresh dev server..."
npm start

echo "Done!"
