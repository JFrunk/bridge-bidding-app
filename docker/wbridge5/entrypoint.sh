#!/bin/bash
Xvfb :99 -screen 0 1024x768x16 &
export DISPLAY=:99
sleep 2
echo ">>> Starting WBridge5 Oracle Service..."
python wrapper_service.py
