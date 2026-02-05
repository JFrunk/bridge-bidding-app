---
description: Analyze a specific hand for bidding or play issues
---

Analyze a specific hand for bidding or play issues: $ARGUMENTS

Provide hand ID (e.g., hand_2025-10-28_21-46-15.json) or path to hand file.

**Analysis Workflow:**

1. Load hand from backend/review_requests/ or provided path
2. Display hand state:
   - All 4 hands (North, East, South, West)
   - Complete auction sequence
   - Play sequence (if available)
   - Contract and result
3. **Bidding Analysis:**
   - Check each bid for appropriateness (HCP vs bid level)
   - Verify convention usage correctness (Stayman, Blackwood, etc.)
   - Identify SAYC rule violations
   - Check suit length requirements
4. **Play Analysis** (if play data available):
   - Evaluate card selection quality
   - Check trump management
   - Identify missed opportunities (finesses, entries)
   - Verify contract execution
5. Identify specific errors with line numbers and SAYC rules cited
6. Explain what SHOULD have happened (optimal bidding/play)
7. **Systematic Scope Check:**
   - Search codebase for similar patterns
   - Determine if this is isolated or systemic issue
   - Use check-scope protocol from CODING_GUIDELINES.md
8. Recommend fix approach:
   - If isolated: specific file/function to fix
   - If systemic: architectural fix needed

**Output Format:**
```
## Hand Analysis: [hand_id]

### Hand State
[Display all 4 hands]

### Auction
[Bid sequence with explanations]

### Issues Found
1. **Bidding Issue**: [description]
   - Location: [module/line]
   - Rule violated: [SAYC rule]
   - Should be: [correct action]

2. **Play Issue**: [description]
   - Location: [AI level/strategy]
   - Missed opportunity: [description]
   - Optimal play: [sequence]

### Scope Analysis
- Pattern found in: [N] files
- Similar issues: [list]

### Recommended Fix
[Specific or architectural approach]
```

Reference: .claude/CODING_GUIDELINES.md systematic analysis protocol
