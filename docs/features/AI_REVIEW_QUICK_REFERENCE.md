# AI Review Feature - Quick Reference

## When to Use

### During Bidding Phase ✅
- Question about a bid
- Uncertain about best call
- Want to understand AI's reasoning
- Learn convention application

### During Playing Phase ✅ NEW!
- Question about card play
- Uncertain about best card
- Want to review play line
- Learn play techniques

## What Gets Captured

### Bidding Phase
```
✅ All 4 hands (original deal)
✅ Complete auction
✅ Vulnerability
✅ Your specific concern
```

### Playing Phase (NEW)
```
✅ All 4 hands (remaining cards)
✅ Complete auction
✅ Contract details
✅ All tricks played (with winner)
✅ Current trick state
✅ Tricks won by each side
✅ Opening leader & dummy
✅ Your specific concern
```

## How to Use

### Step 1: Click Button
```
Click "🤖 Request AI Review" button
(Available in both bidding and playing phases)
```

### Step 2: Enter Concern (Optional)
```
Bidding examples:
- "Why did North bid 3NT?"
- "Should South have bid 2♥ instead?"
- "Is this a Stayman situation?"

Playing examples:
- "Should declarer have finessed?"
- "Was the opening lead correct?"
- "How should I continue from here?"
```

### Step 3: Generate Prompt
```
Click "Save & Generate Prompt"
→ Data saved to backend/review_requests/
→ Prompt appears in modal
```

### Step 4: Copy & Analyze
```
Click "📋 Copy to Clipboard"
→ Paste into Claude Code
→ Get expert analysis
```

## Example Review Requests

### Example 1: Bidding Question
**When:** After auction completes, before play starts
**Concern:** "Is 3NT the right contract with only 24 HCP?"
**Captured:**
- All original hands
- Bidding sequence
- Vulnerability

### Example 2: Opening Lead
**When:** After opening lead, before 2nd card
**Concern:** "Why did partner lead a low spade?"
**Captured:**
- Contract: 4♥ by North
- Opening lead card
- All 4 hands
- Trick 1 (partial)

### Example 3: Mid-Game Decision
**When:** Middle of play, tough decision
**Concern:** "Should I finesse or play for the drop?"
**Captured:**
- All tricks played so far
- Remaining cards
- Current position
- Tricks won

### Example 4: Post-Mortem
**When:** After contract is defeated
**Concern:** "Where did I go wrong?"
**Captured:**
- Complete auction
- All 13 tricks
- Final result
- Full play history

## Generated Prompt Format

### For Bidding Phase
```
Please analyze the bidding in backend/review_requests/hand_TIMESTAMP.json
and identify any errors or questionable bids according to SAYC.

I'm particularly concerned about: [your concern]
```

### For Playing Phase
```
Please analyze the gameplay in backend/review_requests/hand_TIMESTAMP.json.
This includes both the auction and card play progress according to SAYC.

I'm particularly concerned about: [your concern]
```

## Review File Location

**Local Development:**
```
backend/review_requests/hand_YYYY-MM-DD_HH-MM-SS.json
```

**Production (Render):**
```
File not saved to disk (ephemeral storage)
Full data included in prompt instead
```

## Data Structure

### Top Level (Always Present)
```json
{
  "timestamp": "...",
  "game_phase": "bidding" or "playing",
  "all_hands": {...},
  "auction": [...],
  "vulnerability": "...",
  "dealer": "...",
  "user_position": "...",
  "user_concern": "..."
}
```

### Play Data (Only During Gameplay)
```json
{
  "play_data": {
    "contract": {...},
    "dummy": "N",
    "opening_leader": "W",
    "trick_history": [
      {
        "cards": [...],
        "leader": "W",
        "winner": "N"
      }
    ],
    "current_trick": [...],
    "tricks_won": {...},
    "tricks_taken_ns": 3,
    "tricks_taken_ew": 1,
    "is_complete": false
  }
}
```

## Tips for Best Results

### Writing Good Concerns

**❌ Too Vague**
- "Is this correct?"
- "What do you think?"
- "Help"

**✅ Specific Questions**
- "Should North have opened 1♠ or 1NT with this balanced 15 HCP?"
- "Was West's overcall at the 2-level too risky vulnerable?"
- "Should declarer have drawn trumps before establishing diamonds?"

### During Bidding
- Ask about specific bids, not the whole auction
- Mention convention uncertainty if relevant
- Include your reasoning if you have one

### During Playing
- Reference specific tricks or decisions
- Ask about alternative plays
- Question strategy, not just tactics

## Keyboard Shortcuts

None currently, but coming soon:
- `Ctrl+R` - Request review
- `Ctrl+C` - Copy prompt (when modal open)

## Troubleshooting

### "Hand not available" error
**Cause:** No deal has been made yet
**Fix:** Deal a hand first

### Prompt doesn't copy
**Cause:** Browser security restrictions
**Fix:** Manually select and copy the text

### Modal doesn't appear
**Cause:** JavaScript error
**Fix:** Check browser console, refresh page

### File not found
**Cause:** Running on Render (ephemeral storage)
**Fix:** Use the full data in the prompt instead

## What AI Can Analyze

### From Bidding Phase Reviews
- Bid selection (all 4 players)
- Convention application
- Point count calculations
- Hand evaluation
- Partnership bidding logic
- Vulnerability considerations
- Competitive bidding decisions

### From Playing Phase Reviews
- Opening lead selection
- Play sequencing
- Finesse decisions
- Trump management
- Suit establishment
- Entry management
- Defensive signals
- Counting cards
- Endplay possibilities

## Limitations

### What's NOT Captured
- ❌ Hand evaluation thoughts/notes
- ❌ Time taken for decisions
- ❌ Chat messages with partner
- ❌ UI state/settings

### What IS Captured
- ✅ All cards dealt
- ✅ All bids made
- ✅ All cards played
- ✅ All tricks won
- ✅ Current game state
- ✅ Your specific question

## Privacy & Storage

**Local Development:**
- Files saved in `backend/review_requests/`
- No expiration
- You control the files

**Production (Render):**
- Files NOT saved (ephemeral storage)
- Data embedded in prompt
- No persistent storage

**Data Shared:**
- Only hand data
- No personal information
- No account details
- No game history beyond current hand

## Advanced Usage

### Batch Analysis
Save multiple hands, then analyze all together:
```
"Please analyze these 3 hands and identify common mistakes:
- hand_2025-10-11_14-30-45.json
- hand_2025-10-11_14-35-12.json
- hand_2025-10-11_14-40-33.json"
```

### Comparative Analysis
Compare your play to expert play:
```
"Compare my play in hand_TIMESTAMP.json to the optimal play line"
```

### Pattern Recognition
Find recurring issues:
```
"Review my last 5 hands and identify common bidding errors"
```

## Future Enhancements

Coming soon:
- ⏳ One-click "Review This Trick" button
- ⏳ Visual trick history display
- ⏳ Automatic double-dummy analysis
- ⏳ Play-by-play breakdown
- ⏳ Alternative line visualization

## Quick Checklist

Before requesting review:
- [ ] Game is in progress (bidding or playing)
- [ ] You have a specific question or concern
- [ ] You're ready to learn from the analysis

After requesting review:
- [ ] Prompt generated successfully
- [ ] Prompt copied to clipboard
- [ ] Ready to paste into Claude Code
- [ ] Read and understand the analysis
- [ ] Apply learnings to future games

## Summary

**AI Review captures everything needed to analyze your bridge decisions:**
- ✅ In bidding: auction + hands
- ✅ In playing: auction + hands + tricks + contract
- ✅ Your specific concerns
- ✅ Complete game context

**Use it to:**
- Learn from mistakes
- Understand expert play
- Improve decision-making
- Build bridge knowledge

---

**Need Help?** Check the full documentation:
- [AI_REVIEW_FEATURE.md](AI_REVIEW_FEATURE.md) - Original feature docs
- [AI_REVIEW_GAMEPLAY_ENHANCEMENT.md](AI_REVIEW_GAMEPLAY_ENHANCEMENT.md) - Gameplay enhancement
- [GAMEPLAY_REVIEW_EXAMPLE.json](GAMEPLAY_REVIEW_EXAMPLE.json) - Example review data
