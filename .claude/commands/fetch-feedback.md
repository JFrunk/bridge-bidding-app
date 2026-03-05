---
description: Retrieve and analyze user feedback from production
---

---
description: Retrieve and analyze user feedback from production
---

Retrieve and analyze user feedback from production: $ARGUMENTS

Time window or filter: $ARGUMENTS (default: last 7 days)

---

## Step 1: Retrieve Feedback Files

Parse `$ARGUMENTS` for time window. Default to 7 days if not specified.

```bash
# List recent feedback files (adjust -mtime for days)
ssh hetzner-bridge "find /opt/bridge-bidding-app/backend/user_feedback/ -mtime -7 -name '*.json' -type f | sort -r"
```

Common filters:
- `last 3 days` / `recent` -> `-mtime -3`
- `last week` / `7 days` -> `-mtime -7`
- `last month` / `30 days` -> `-mtime -30`
- `today` -> `-mtime -1`
- `all` -> no `-mtime` filter

---

## Step 2: Read Feedback Content

```bash
# Read all feedback from the time window
ssh hetzner-bridge "find /opt/bridge-bidding-app/backend/user_feedback/ -mtime -7 -name '*.json' -type f -exec cat {} \;"
```

For individual files:
```bash
ssh hetzner-bridge "cat /opt/bridge-bidding-app/backend/user_feedback/<filename>.json"
```

---

## Step 3: Analyze and Categorize

For each feedback item, extract:
- **Type:** issue / suggestion / question
- **Game phase:** bidding / playing / other
- **Context:** freeplay / practice / learning
- **Description:** User's actual words

**Feedback JSON structure:**
```json
{
  "timestamp": "ISO8601",
  "feedback_type": "issue|suggestion|question",
  "description": "User text",
  "context": "freeplay",
  "context_data": {
    "game_phase": "bidding|playing",
    "auction": [],
    "vulnerability": "None|NS|EW|Both",
    "dealer": "N|E|S|W",
    "hand": [],
    "hand_points": null,
    "all_hands": {},
    "console_logs": [],
    "user_actions": []
  }
}
```

---

## Step 4: Present Summary

Format output as:

```
## User Feedback Summary (last N days)

**Total:** X feedback items

### By Type
- Issues: N
- Suggestions: N
- Questions: N

### By Game Phase
- Bidding: N
- Playing: N
- Other: N

### Items (most recent first)

**[DATE] [TYPE]** — "[description]"
- Phase: bidding | Context: freeplay
- Hand: [cards if available] | HCP: [points]
- Auction: [bids if available]
- Action needed: [yes/no with brief recommendation]

---

### Patterns & Recommendations
- [Recurring themes, common complaints, actionable items]
```

---

## Step 5: Cross-Reference (Optional)

If feedback describes specific bugs:
1. Check error logs for matching timestamps: `python3 backend/analyze_errors.py --recent 20`
2. Look for related patterns in codebase using `/check-scope`
3. Create review request files if hands need investigation

---

## Success Criteria

- [ ] Feedback retrieved from PRODUCTION server (not local)
- [ ] All items within time window included
- [ ] Categorized by type and game phase
- [ ] Patterns identified across feedback items
- [ ] Actionable items highlighted with recommendations
