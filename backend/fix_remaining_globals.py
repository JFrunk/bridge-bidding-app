#!/usr/bin/env python3
"""
Fix all remaining global state references in server.py
"""

import re

print("Reading server.py...")
with open('server.py', 'r') as f:
    content = f.read()

print(f"Original size: {len(content)} characters")

# Count before
before_count = len(re.findall(r'current_play_state|current_deal|current_vulnerability|current_session|current_ai_difficulty|current_hand_start_time', content))
print(f"Global references before: {before_count}")

# Remove global declarations (already have state = get_state())
content = re.sub(r'\n\s+global current_play_state\n', '\n', content)
content = re.sub(r'\n\s+global current_[a-z_]+\n', '\n', content)

# Replace all occurrences systematically
replacements = [
    # Play state
    (r'\bcurrent_play_state\.', 'state.play_state.'),
    (r'\bif not current_play_state:', 'if not state.play_state:'),
    (r'\bif current_play_state:', 'if state.play_state:'),
    (r'\bcurrent_play_state\b', 'state.play_state'),

    # Deal
    (r'\bcurrent_deal\[', 'state.deal['),
    (r'\bcurrent_deal\.', 'state.deal.'),
    (r'\bcurrent_deal\b', 'state.deal'),

    # Vulnerability
    (r'\bcurrent_vulnerability\b', 'state.vulnerability'),

    # Session
    (r'\bcurrent_session\.', 'state.game_session.'),
    (r'\bif not current_session:', 'if not state.game_session:'),
    (r'\bif current_session:', 'if state.game_session:'),
    (r'\bcurrent_session\b', 'state.game_session'),

    # AI difficulty
    (r'\bcurrent_ai_difficulty\b', 'state.ai_difficulty'),

    # Hand start time
    (r'\bcurrent_hand_start_time\b', 'state.hand_start_time'),
]

for pattern, replacement in replacements:
    before = content
    content = re.sub(pattern, replacement, content)
    changes = len(before) - len(content)
    if before != content:
        count = len(re.findall(pattern, before))
        print(f"  ✓ Replaced {count} occurrences: {pattern[:30]}...")

# Count after
after_count = len(re.findall(r'current_play_state|current_deal|current_vulnerability|current_session|current_ai_difficulty|current_hand_start_time', content))
print(f"\nGlobal references after: {after_count}")
print(f"Replaced: {before_count - after_count} references")

if after_count > 0:
    print(f"\n⚠️  WARNING: {after_count} references remain!")
    # Find them
    remaining = re.findall(r'.{0,40}(current_[a-z_]+).{0,40}', content)
    print("\nRemaining references:")
    for i, match in enumerate(remaining[:10], 1):
        print(f"  {i}. ...{match}...")
else:
    print("\n✅ All global state references replaced!")

print("\nWriting updated server.py...")
with open('server.py', 'w') as f:
    f.write(content)

print("✅ Done!")
print(f"\nNew size: {len(content)} characters")
print("Difference:", len(content) - before_count, "characters")
