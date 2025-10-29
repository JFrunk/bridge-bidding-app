#!/usr/bin/env python3
"""
Script to update rebids.py to use make_bid() wrapper for all non-Pass returns
"""
import re

# Read the file
with open('backend/engine/rebids.py', 'r') as f:
    content = f.read()

# Pattern to match return statements that are NOT Pass
# We want to transform: return ("BID", "explanation")
# Into: result = make_bid("BID", "explanation")
#       if result: return result

# Skip lines that are already using make_bid or are Pass
lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]

    # Check if this line contains a return that's NOT Pass and NOT already wrapped
    if 'return (' in line and '"Pass"' not in line and 'result = make_bid' not in line and 'def make_bid' not in line:
        # Extract the return statement
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent

        # Use regex to extract the bid and explanation
        match = re.search(r'return\s+\(([^)]+)\)', line)
        if match:
            args = match.group(1)
            # Replace the return with result = make_bid(...)
            new_lines.append(f'{indent_str}result = make_bid({args})')
            new_lines.append(f'{indent_str}if result: return result')
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

    i += 1

# Write back
with open('backend/engine/rebids.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("Updated rebids.py - wrapped all non-Pass returns with make_bid()")
