# Architectural Decision System - User Guide

**For:** Project Owner / User
**Purpose:** Understand your role in the architectural decision process
**Last Updated:** 2025-10-12

---

## Your Role in 60 Seconds

**Claude Code will present HIGH-RISK architectural decisions to you for approval.**

When you see this, Claude has already:
1. Detected a significant architectural change
2. Evaluated 3+ alternatives
3. Scored them objectively
4. Created an ADR document
5. Identified the best option

**Your job:** Review and approve (or suggest changes).

---

## What You'll See from Claude

### Example Message:

```
I've detected HIGH-RISK architectural changes for implementing play-only mode.

RECOMMENDATION: Session-based state management (Score: 8.35/10)

KEY BENEFITS:
- Solves documented past issue (global state conflicts)
- Prevents future conflicts
- Enables multi-user support
- Testable architecture

TRADE-OFFS:
- Requires 20 hours implementation (vs. 2 hours for quick fix)
- Touches many files (server.py + all API endpoints)
- More complex initially

ALTERNATIVES CONSIDERED:
- Option B: Add flag to global state (Score: 4.8/10) - quick but creates technical debt
- Option C: Hybrid approach (Score: 6.05/10) - inconsistent architecture

I've created ADR-0002 documenting this decision (see docs/architecture/decisions/).

Shall I proceed with session-based state management (Option A)?
```

---

## How to Review

### Step 1: Read the ADR (2-3 minutes)

```bash
# ADR location will be shown in Claude's message
cat docs/architecture/decisions/ADR-NNNN-title.md
```

**Look for:**
- **Problem Statement:** Do you agree this needs solving?
- **Alternatives:** Are there 3+ options with scores?
- **Chosen Option:** Is the rationale clear?
- **Trade-offs:** Are they acceptable?

### Step 2: Check the Scoring (1 minute)

**Decision Matrix:**
- Maintainability (25%): Will this be easy to change later?
- Testability (20%): Can we test it properly?
- Future-proofing (20%): Does it scale/extend well?
- Implementation Effort (15%): Is timeline realistic?
- Risk (10%): What could go wrong?
- Performance (10%): Speed/resource impact?

**Does the scoring match YOUR priorities?**
- If you value speed over maintainability, scores might differ
- If you're planning to pivot soon, future-proofing matters less

### Step 3: Ask Questions (if needed)

**Good questions:**
- "Why did Option B score lower on maintainability?"
- "What specifically breaks if we go with Option C?"
- "Can we do Option A in phases to reduce risk?"
- "What's the rollback plan if this doesn't work?"

---

## Your Response Options

### ✅ Approve as-is
**Say:** "Yes, proceed" or "Approved" or "Go ahead"

Claude will:
- Implement the recommended solution
- Update ADR status to "Accepted"
- Begin work immediately

---

### 🔄 Choose Different Option
**Say:** "No, use Option B instead" or "I prefer Option C"

Claude will:
- Switch to your preferred alternative
- Update ADR with your reasoning
- Implement that option instead

**When to do this:**
- You have different priorities (speed vs. quality)
- You have context Claude doesn't (upcoming changes)
- You see a risk Claude missed

---

### ❓ Request More Information
**Say:** "Tell me more about..." or "What happens if..." or "Can you explain..."

Claude will:
- Provide detailed explanation
- Run additional analysis if needed
- Present updated recommendation

**Good follow-ups:**
- "Show me exactly what files change"
- "What's the migration path for existing code?"
- "How does this compare to industry standards?"

---

### ⏸️ Defer Decision
**Say:** "Let me think about it" or "I need time to review"

Claude will:
- Wait for your response
- Not proceed with implementation
- Can resume other work on unrelated items

**When to do this:**
- Decision is complex and you need time
- You want to research alternatives
- You need to consult someone else

---

### ⚖️ Adjust Priorities
**Say:** "This isn't HIGH-RISK" or "The scoring doesn't match my priorities"

Claude will:
- Adjust the framework
- Update trigger list or decision matrix weights
- Document the change

**When to do this:**
- Trigger detection is too sensitive/not sensitive enough
- Scoring criteria don't match project goals
- Process feels too heavy/light

---

## Decision Authority Quick Reference

| Score | Your Approval Needed? | Default Action |
|-------|----------------------|----------------|
| ≥ 8.5 | Optional (Claude notifies after) | Claude proceeds + creates ADR |
| 7.0-8.4 | Required (before implementation) | Claude waits for your approval |
| < 7.0 | Required + discussion | Claude discusses alternatives |

**You can override:** If you trust Claude's judgment on a specific domain, you can say:
- "For dependency choices, Claude decide"
- "For test infrastructure, proceed with score ≥ 7.0"

---

## Monitoring the System

### Weekly Check (5 minutes)

```bash
# See what ADRs were created this week
ls -lt docs/architecture/decisions/ADR-*.md | head -5

# Read the latest
cat docs/architecture/decisions/ADR-0003-example.md
```

**Look for:**
- Are decisions well-reasoned?
- Are trade-offs acceptable?
- Is velocity improving or suffering?

### Monthly Review (15 minutes)

```bash
# Generate compliance report
python3 .claude/scripts/architectural_compliance_report.py --html -o compliance_report.html
open compliance_report.html
```

**Track:**
- Architectural health score (target: ≥ 85/100)
- God classes (target: 0)
- Global state instances (target: < 5)
- ADRs created (expect: 1-2 per month)

**Questions to ask:**
- Is the system helping or hindering?
- Are we avoiding past mistakes?
- Should we adjust the process?

---

## Common Scenarios

### Scenario 1: Claude Proposes Something You Disagree With

**Example:** Claude recommends complex solution (score 8.5), you prefer simple solution (score 6.5)

**Your response:**
```
I prefer Option B (simple solution) even though it scored lower.
Here's why: We're planning to rewrite this module in 3 months anyway,
so I'd rather have something quick now. Please proceed with Option B
and note in the ADR that this is a temporary solution.
```

**Claude will:**
- Implement Option B
- Update ADR with your reasoning
- Mark as "Temporary" with planned replacement date

---

### Scenario 2: Emergency - Claude Skipped Review

**Example:** Production was down, Claude fixed it without review

**What Claude will do:**
```
EMERGENCY FIX COMPLETED

Issue: Production outage - all users affected
Fix: Reverted deployment, rolled back database migration
Status: System restored, users can access again

I've skipped the normal architectural review due to emergency.
I will create ADR-NNNN-emergency-rollback.md within 24 hours
documenting what happened and why.

Post-incident review scheduled for next week.
```

**Your response:**
- Review the emergency ADR when ready
- Participate in post-incident review
- Help identify how to prevent similar emergencies

---

### Scenario 3: Claude is Being Too Cautious

**Example:** Every small change triggers HIGH-RISK review

**Your response:**
```
The trigger detection seems too sensitive. Creating a new
config file shouldn't require full architectural review.

Can we adjust the triggers to be less sensitive for:
- Config files
- Test infrastructure
- Documentation structure

Keep HIGH-RISK for:
- API changes
- Data structures
- State management
```

**Claude will:**
- Update `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md`
- Adjust trigger sensitivity
- Create ADR documenting the change

---

## Red Flags to Watch For

### 🚩 Process is Being Ignored
**Signs:**
- No ADRs created in 2+ months
- Claude isn't mentioning architectural reviews
- Changes happening without documented decisions

**Action:** Ask Claude "Are you following the architectural review process?"

---

### 🚩 Process is Too Heavy
**Signs:**
- Development velocity slowing significantly
- Claude spending hours on reviews for simple changes
- Frustration with "process overhead"

**Action:** "Let's review and simplify the process. What's taking too long?"

---

### 🚩 Decisions are Low Quality
**Signs:**
- Refactoring required soon after decisions
- Technical debt accumulating
- Same mistakes repeating

**Action:** "Let's review recent ADRs and see what we're missing."

---

### 🚩 No Feedback Loop
**Signs:**
- Process never improves
- Same issues keep occurring
- No learning from mistakes

**Action:** "Let's do a monthly review of the ADR process itself."

---

## Emergency Contact

### If System Isn't Working

1. **Check Integration:**
   ```bash
   # Verify files exist
   ls .claude/ARCHITECTURAL_DECISION_FRAMEWORK.md
   ls docs/architecture/decisions/

   # Check baseline metrics
   cat .claude/baseline_metrics_2025-10-12.txt
   ```

2. **Review with Claude:**
   Say: "Let's review the architectural decision system. Is it working?"

3. **Adjust or Pause:**
   - "Let's simplify this to just HIGH-RISK decisions"
   - "Pause the process for 2 weeks while we reassess"
   - "I want to be involved in ALL architectural decisions"

---

## Success Indicators

**After 1 month, you should see:**
- [ ] 1-3 ADRs created
- [ ] Zero emergency "we need to refactor this" situations
- [ ] Thoughtful, well-reasoned architectural decisions
- [ ] Clear documentation of WHY decisions were made

**After 3 months, you should see:**
- [ ] 3-10 ADRs created
- [ ] Improved architectural health score (from baseline)
- [ ] Fewer global state issues
- [ ] No major refactoring required due to poor decisions

**After 6 months, you should see:**
- [ ] Measurable velocity improvement
- [ ] Technical debt decreasing
- [ ] Architectural health score ≥ 85/100
- [ ] Clear patterns emerging (library choices, design patterns, etc.)

---

## Quick Command Reference

```bash
# List all ADRs
ls docs/architecture/decisions/ADR-*.md

# Read latest ADR
cat docs/architecture/decisions/ADR-00* | tail -1

# Generate compliance report
python3 .claude/scripts/architectural_compliance_report.py --verbose

# HTML compliance report
python3 .claude/scripts/architectural_compliance_report.py --html -o report.html

# Check what triggers would fire
python3 .claude/scripts/check_architectural_triggers.py --verbose

# View framework
cat .claude/ARCHITECTURAL_DECISION_FRAMEWORK.md

# View baseline metrics
cat .claude/baseline_metrics_2025-10-12.txt
```

---

## FAQs

**Q: How often will Claude ask for my approval?**
A: Expect 1-2 HIGH-RISK decisions per month. MEDIUM/LOW proceed without approval.

**Q: What if I'm unavailable for 24+ hours?**
A: If score ≥ 8.0 and no security risk, Claude can proceed and notify you when you return.

**Q: Can I give Claude blanket approval for certain types of decisions?**
A: Yes! Say "For [category], Claude decide if score ≥ X.X"

**Q: What if Claude's recommendation is wrong?**
A: Override it! Your judgment and context matter. Claude will learn from your feedback.

**Q: How much time should I budget for reviews?**
A: 5-10 minutes for most decisions. Complex ones might be 20-30 minutes.

**Q: Can we skip the process for urgent work?**
A: Yes, emergency protocol allows skipping with retroactive ADR within 24 hours.

**Q: What if the process isn't helping?**
A: Tell Claude! The process should serve the project, not vice versa. It can be adjusted or paused.

---

**Remember:** You're the decision maker. Claude provides analysis and recommendations, but you have final say on all architectural decisions.

The system exists to:
1. **Inform** your decisions with systematic analysis
2. **Document** the reasoning for future reference
3. **Prevent** repeating past mistakes

It should **help**, not **hinder**.

---

**Questions?** Ask Claude: "How does the architectural decision system work?"

**Status:** Active
**Owner:** You (with Claude as analyst)
**Last Updated:** 2025-10-12
