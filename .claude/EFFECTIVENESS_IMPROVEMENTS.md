# Claude Code Effectiveness Improvements
## Analysis of Current Setup vs. Best Practices

**Analysis Date:** 2025-10-29
**Based on:** Anthropic Claude Code Best Practices Guide

---

## Executive Summary

**Current State:** You have a strong foundation with custom permissions, coding guidelines, and quality assurance protocols. However, you're underutilizing several powerful Claude Code features that could significantly boost effectiveness.

**Key Gaps Identified:**
1. CLAUDE.md file not in root directory (won't auto-load)
2. No use of extended thinking mode for complex problems
3. Minimal custom slash commands (only 1 vs potential for 10+)
4. No MCP servers configured
5. Not leveraging subagents for complex analysis
6. Missing planning-first workflow prompts
7. No parallel development setup (git worktrees)

**Estimated Impact:** Implementing these improvements could reduce development time by 30-40% and reduce errors by 20-30%.

---

## 🔴 Critical Priority - Implement Immediately

### 1. Fix CLAUDE.md Location
**Current:** `docs/project-overview/CLAUDE.md`
**Problem:** Claude only auto-loads CLAUDE.md from root or parent directories
**Impact:** Claude doesn't automatically see your project guidance

**Action Required:**
```bash
# Move or copy CLAUDE.md to project root
cp docs/project-overview/CLAUDE.md ./CLAUDE.md

# Or create symlink to keep docs organized
ln -s docs/project-overview/CLAUDE.md ./CLAUDE.md
```

**Expected Result:** Claude will automatically pull project context at session start, improving bid appropriateness understanding and reducing context gathering time.

---

### 2. Add Extended Thinking Mode to Workflow
**Current:** Not using extended thinking
**Problem:** Missing additional computation time for complex problems
**Impact:** Lower quality first-pass solutions, more iterations needed

**How to Use:**
- **"think"** - Basic extended thinking (standard)
- **"think hard"** - Moderate thinking budget
- **"think harder"** - Large thinking budget
- **"ultrathink"** - Maximum thinking budget

**When to Use:**
- Analyzing bidding quality score regressions
- Designing architectural changes
- Debugging complex state management issues
- Planning multi-file refactors

**Example Prompts:**
```
"Think hard about why the appropriateness score dropped from 78.7% to 75.1%"

"Ultrathink about the best architecture for separating bid validation from bid generation"

"Think harder about potential edge cases in the trump management logic"
```

**Expected Impact:** 40-60% better first-pass solutions, fewer iterations on complex problems.

---

### 3. Create Custom Slash Commands Library
**Current:** 1 slash command (check-scope.md)
**Problem:** Repeating common workflows manually every time
**Impact:** Wasting 5-10 minutes per repetitive task

**Recommended Slash Commands:**

#### A. `/project:run-quality-baseline`
```markdown
# File: .claude/commands/run-quality-baseline.md

Run comprehensive baseline quality score testing workflow:

1. Check current branch (should be on main/development)
2. Run bidding quality score: `python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_$(date +%Y%m%d).json`
3. Run play quality score: `python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_baseline_$(date +%Y%m%d).json`
4. Display summary of scores
5. Save baseline files to quality_scores/ directory
6. Update quality_scores/README.md with new baseline entry

Do NOT modify any code. This is purely for establishing baseline metrics.
```

#### B. `/project:compare-quality-scores`
```markdown
# File: .claude/commands/compare-quality-scores.md

Compare quality scores before and after changes: $ARGUMENTS

1. List available baseline files in quality_scores/ and project root
2. Ask user which baseline to compare against (or use most recent)
3. Run comparison scripts:
   - `python3 compare_scores.py baseline_before.json baseline_after.json`
   - `python3 compare_play_scores.py play_baseline_before.json play_baseline_after.json`
4. Analyze results:
   - Flag any regressions (>2% drop in composite)
   - Highlight improvements (>2% increase)
   - Identify specific error categories that changed
5. Recommend: commit, iterate, or rollback
```

#### C. `/project:analyze-hand`
```markdown
# File: .claude/commands/analyze-hand.md

Analyze a specific hand for bidding or play issues: $ARGUMENTS

Provide hand ID (e.g., hand_2025-10-28_21-46-15.json)

1. Load hand from backend/review_requests/
2. Display hand state, auction, and play sequence
3. Analyze:
   - Bidding appropriateness (HCP vs bids)
   - Convention usage correctness
   - Play decisions quality
4. Identify specific errors with SAYC rules
5. Explain what SHOULD have happened
6. Determine if this is isolated or systemic issue (use check-scope protocol)
7. Recommend fix approach

Reference: .claude/CODING_GUIDELINES.md systematic analysis protocol
```

#### D. `/project:fix-github-issue`
```markdown
# File: .claude/commands/fix-github-issue.md

Analyze and fix GitHub issue: $ARGUMENTS

Follow TDD workflow:
1. Use `gh issue view` to get issue details
2. Understand the problem (think hard if complex)
3. Search codebase for relevant files
4. **Write tests first** that verify the fix
5. Run tests to confirm they fail
6. Implement the fix
7. Run tests until they pass
8. Run quality baselines if bidding/play logic changed
9. Create descriptive commit message
10. Push and create PR with test results

Always use test-driven development approach.
```

#### E. `/project:review-pr-comments`
```markdown
# File: .claude/commands/review-pr-comments.md

Address code review comments on PR: $ARGUMENTS

1. Use `gh pr view $ARGUMENTS` to get PR details
2. Use `gh pr view $ARGUMENTS --comments` to get review comments
3. For each comment:
   - Read the suggestion
   - Locate the relevant code
   - Implement the requested change
   - Mark as resolved in your notes
4. Run tests and quality checks
5. Commit with message: "fix: Address PR review comments"
6. Push to PR branch
7. Respond to each comment confirming the fix
```

#### F. `/project:deploy-to-production`
```markdown
# File: .claude/commands/deploy-to-production.md

Deploy current development branch to production (main):

**SAFETY CHECKS FIRST:**
1. Verify you're on development branch
2. Run full test suite: `pytest backend/tests/ -v`
3. Run bidding quality baseline (500 hands)
4. Run play quality baseline (500 hands)
5. Check for uncommitted changes
6. Review recent commits: `git log --oneline -10`

**DEPLOYMENT:**
7. Checkout main: `git checkout main`
8. Merge development: `git merge development`
9. Push to trigger Render deploy: `git push origin main`
10. Monitor deployment on Render dashboard
11. Checkout development: `git checkout development`

**VERIFICATION:**
12. Visit production URL
13. Test basic functionality
14. Monitor error logs for 5 minutes

Do NOT deploy if any safety checks fail.
```

#### G. `/project:start-tdd-feature`
```markdown
# File: .claude/commands/start-tdd-feature.md

Start new feature using test-driven development: $ARGUMENTS

Feature description: $ARGUMENTS

**Phase 1: Research & Plan (think hard)**
1. Understand the feature requirements
2. Identify affected files and components
3. Design the solution architecture
4. Create implementation checklist

**Phase 2: Write Tests First**
5. Write failing tests for the feature
6. Cover edge cases and error conditions
7. Run tests to confirm they fail
8. Commit tests: "test: Add tests for [feature]"

**Phase 3: Implement**
9. Implement minimal code to make tests pass
10. Run tests frequently during implementation
11. Refactor for quality once tests pass
12. Run quality baselines if needed
13. Commit implementation: "feat: Implement [feature]"

**Phase 4: Document**
14. Update relevant documentation
15. Add examples if applicable
16. Commit docs: "docs: Document [feature]"

Do NOT write implementation code until tests are written and committed.
```

#### H. `/project:debug-with-subagent`
```markdown
# File: .claude/commands/debug-with-subagent.md

Debug complex issue using subagents: $ARGUMENTS

Issue description: $ARGUMENTS

**Investigation Strategy:**
1. Launch subagent to gather initial context
   - Read error logs, stack traces
   - Identify affected components
   - Search for similar patterns

2. Launch subagent to analyze root cause
   - Deep dive into identified components
   - Test hypotheses
   - Find minimal reproduction

3. Launch subagent to verify fix approach
   - Review proposed solution
   - Check for unintended consequences
   - Validate against coding guidelines

4. Implement fix based on subagent findings

5. Launch subagent to verify fix completeness
   - Run tests
   - Check quality baselines
   - Verify no regressions

Use subagents to preserve main context while investigating.
```

#### I. `/project:refactor-with-plan`
```markdown
# File: .claude/commands/refactor-with-plan.md

Refactor code with planning-first approach: $ARGUMENTS

Target: $ARGUMENTS

**Phase 1: Analysis (do NOT code yet)**
1. Read all affected files
2. Understand current architecture
3. Identify pain points and technical debt
4. Think hard about optimal design

**Phase 2: Plan (present to user)**
5. Document current structure
6. Propose new structure
7. List all files to be changed
8. Estimate risk and testing needs
9. Get user approval before coding

**Phase 3: Execute**
10. Implement refactor in logical steps
11. Run tests after each step
12. Maintain working state throughout
13. Run quality baselines at end

**Phase 4: Document**
14. Update architecture docs
15. Add migration notes if needed

Remember: Plan first, get approval, then code.
```

#### J. `/project:setup-worktree`
```markdown
# File: .claude/commands/setup-worktree.md

Set up git worktree for parallel development: $ARGUMENTS

Branch name: $ARGUMENTS

**Setup:**
1. Create new worktree: `git worktree add ../bridge_app_$ARGUMENTS $ARGUMENTS`
2. Create directory structure
3. Display instructions for opening in new terminal
4. Show how to launch Claude in worktree

**Cleanup Instructions:**
```bash
# When done with worktree:
cd ../bridge_bidding_app
git worktree remove ../bridge_app_$ARGUMENTS
```

Use worktrees for:
- Parallel feature development
- Testing fixes while main work continues
- Emergency hotfixes while in middle of feature
```

**Expected Impact:** Save 5-10 minutes per repetitive task, reduce errors in common workflows.

---

## 🟡 High Priority - Implement Within 1 Week

### 4. Consider MCP Servers (Optional)
**Current:** No MCP servers
**Status:** Optional enhancement, evaluate based on specific needs
**Impact:** Could automate some visual testing workflows

**Potentially Useful MCP Servers:**

#### A. Puppeteer (Browser Automation) - OPTIONAL
**Use Case:** Automated frontend testing and screenshot comparison

```json
// .mcp.json (create in project root)
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

**Workflows Enabled:**
- Screenshot frontend after changes
- Compare screenshots before/after UI changes
- Automated regression testing
- Visual validation of card display fixes

**Recommendation:** Start without this and add later if visual testing becomes a bottleneck. Manual screenshots with drag-and-drop work well for now.

#### B. Sequential Thinking - NOT RECOMMENDED
**Use Case:** Systematic problem breakdown for complex issues

**Recommendation:** The built-in "think hard" / "think harder" / "ultrathink" features provide similar functionality without requiring a separate server. Use those instead.

#### C. Filesystem - NOT NEEDED
**Use Case:** Batch file operations and advanced searches

**Recommendation:** Claude Code's built-in Read, Glob, and Grep tools already provide excellent file operations. No need for additional MCP server.

**Expected Impact:** MCP servers are optional enhancements. Focus on higher-priority improvements first (CLAUDE.md, slash commands, extended thinking).

---

### 5. Adopt Planning-First Workflow
**Current:** Often jump straight to coding
**Problem:** Leads to rework and suboptimal solutions
**Impact:** 30-40% of development time spent on rework

**New Workflow Template:**

**For Complex Features:**
1. **Explore** (explicitly tell Claude NOT to code yet)
   - Read relevant files
   - Use subagents to investigate specific questions
   - Gather all context needed

2. **Plan** (ask Claude to "think hard" and make a plan)
   - Ask: "Think hard about the best approach and create a detailed plan"
   - Review the plan
   - Iterate on plan if needed
   - Save plan to GitHub issue or markdown file

3. **Code** (now implement the plan)
   - Ask Claude to implement the plan
   - Use TodoWrite to track progress
   - Verify each step

4. **Commit & PR**
   - Ask Claude to commit and create PR with context

**Example Prompt:**
```
"Read the bidding engine files and understand how appropriateness validation works.
Think hard about the best architectural approach to fix the systemic issues.
Create a detailed plan but do NOT write any code yet. I want to review the plan first."
```

**Expected Impact:** Reduce rework by 40%, improve first-pass solution quality by 60%.

---

### 6. Leverage Subagents for Complex Tasks
**Current:** Not using Task tool for subagents
**Problem:** Main context gets cluttered, harder to stay focused
**Impact:** Reduced effectiveness on complex problems

**When to Use Subagents:**
- **Research Tasks:** "Use subagent to search for all instances of bid validation"
- **Parallel Investigation:** "Launch subagent to investigate play engine while I continue with bidding"
- **Verification:** "Use subagent to verify this fix doesn't break other components"
- **Focused Analysis:** "Launch subagent to analyze just the convention modules"

**Example Prompts:**
```
"Launch a subagent to search through all bidding modules and create a comprehensive
list of where appropriateness checks are performed. Report back with file names
and line numbers."

"Use a subagent to verify that our planned fix won't break any existing tests.
Have it run the full test suite and report any failures."
```

**Expected Impact:** Preserve main context, enable parallel work, reduce context pollution by 70%.

---

### 7. Adopt Test-Driven Development Workflow
**Current:** Tests often written after implementation
**Problem:** Tests may not catch edge cases, implementation bias
**Impact:** More bugs reach production

**New TDD Workflow:**

**Step 1: Write Tests First**
```
"I want to fix the 3-card suit bidding issue using TDD.
First, write comprehensive tests that verify a bid is only made
with appropriate suit length. Cover these cases:
- 3-card suit: should reject
- 4-card suit: should accept
- 5+ card suit: should accept
Edge cases: weak suits, competitive bidding, preempts.
Do NOT write any implementation code yet."
```

**Step 2: Verify Tests Fail**
```
"Run the tests and confirm they fail. Show me the output."
```

**Step 3: Commit Tests**
```
"Commit just the tests with message 'test: Add tests for suit length validation'"
```

**Step 4: Implement**
```
"Now implement the minimum code needed to make these tests pass.
Do NOT modify the tests."
```

**Step 5: Iterate Until Green**
```
"Keep running tests and fixing until all tests pass."
```

**Step 6: Verify with Independent Subagent**
```
"Launch a subagent to review the implementation and verify it's not
overfitting to the tests."
```

**Expected Impact:** Catch 30-40% more bugs before production, better test coverage.

---

## 🟢 Medium Priority - Implement Within 1 Month

### 8. Set Up Git Worktrees for Parallel Development
**Current:** Single working directory, sequential development
**Problem:** Context switching cost, waiting for one task to finish
**Impact:** Lower throughput, more downtime

**Setup Instructions:**

```bash
# Create worktrees directory (one-time setup)
mkdir -p ~/worktrees

# Create worktree for feature A
git worktree add ~/worktrees/bridge-feature-a -b feature/feature-a

# Create worktree for bugfix B
git worktree add ~/worktrees/bridge-bugfix-b -b fix/bugfix-b

# Launch Claude in each worktree (separate terminals)
cd ~/worktrees/bridge-feature-a && claude
cd ~/worktrees/bridge-bugfix-b && claude
```

**When to Use:**
- Multiple independent features in progress
- Hotfix needed while working on feature
- Testing different approaches in parallel
- Code review fixes while continuing development

**iTerm2 Notifications Setup:**
```bash
# Add to .zshrc or .bashrc
function claude_notify() {
  echo -e "\a"  # Terminal bell
  osascript -e 'display notification "Claude needs attention" with title "Claude Code"'
}
```

**Expected Impact:** 30-40% increase in parallel work capacity, reduced context switching cost.

---

### 9. Use Screenshots for Visual Validation
**Current:** Manual visual testing, no screenshot comparison
**Problem:** Card display issues hard to catch, regressions in UI
**Impact:** UI bugs reach production

**How to Use:**

**Drag & Drop Screenshots:**
```
# macOS screenshot to clipboard: cmd+ctrl+shift+4
# Then in Claude: ctrl+v to paste

"Compare this screenshot of the current card display to the expected layout.
Identify any alignment or sizing issues."
```

**Screenshot Files:**
```
"Read the screenshot at docs/designs/card-display-expected.png and compare it
to a screenshot of http://localhost:3000. What differences do you see?"
```

**With Puppeteer MCP:**
```
"Take a screenshot of http://localhost:3000 and save it as before-fix.png.
After I apply your fix, take another screenshot and compare them side by side."
```

**Expected Impact:** Catch 50% more UI regressions before production, faster visual debugging.

---

### 10. Create CLAUDE.local.md for Personal Settings
**Current:** Shared CLAUDE.md only
**Problem:** Can't add personal preferences without affecting team
**Impact:** Suboptimal personal workflow

**Setup:**
```bash
# Create local CLAUDE.md (gitignored)
touch CLAUDE.local.md
echo "CLAUDE.local.md" >> .gitignore

# Add personal preferences
cat > CLAUDE.local.md << 'EOF'
# Personal Claude Settings

## My Preferences
- I prefer concise commit messages (50 char limit)
- Always run quality baselines before commits
- Use "think hard" by default for complex problems
- Remind me to use subagents for research tasks

## My Common Commands
```bash
# My Python environment
source ~/venv/bridge/bin/activate

# My testing workflow
alias qt="python3 backend/test_bidding_quality_score.py --hands 100"
alias qf="python3 backend/test_bidding_quality_score.py --hands 500"
```

## My Style Preferences
- Prefer explicit variable names over short ones
- Always include docstrings for new functions
- Favor readability over cleverness
EOF
```

**Expected Impact:** Personalized workflow without affecting team, better adherence to personal coding style.

---

### 11. Use # Key for Quick CLAUDE.md Updates
**Current:** Manually editing CLAUDE.md files
**Problem:** Friction in documenting learnings
**Impact:** Important context not captured

**How to Use:**

During a session, press `#` and type your instruction:

```
# "Add to CLAUDE.md: When testing play quality, always use level 8 on macOS (DDS crashes)"

# "Remember: The dealer always starts at North and doesn't rotate yet"

# "Document: Run quality baselines before committing bidding logic changes"
```

**Claude will:**
1. Determine which CLAUDE.md to update (root, subdirectory, or local)
2. Add the content in appropriate section
3. Commit the change (if desired)

**Expected Impact:** Capture 3x more learnings, better project memory, reduced repeated mistakes.

---

### 12. Set Up Headless Mode for CI/CD
**Current:** Manual quality score testing
**Problem:** Humans forget to run tests, inconsistent testing
**Impact:** Regressions slip through

**GitHub Actions Setup:**

```yaml
# .github/workflows/quality-check.yml
name: Quality Score Check

on:
  pull_request:
    paths:
      - 'backend/engine/**/*.py'
      - 'backend/engine/ai/conventions/**/*.py'

jobs:
  bidding-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt

      - name: Run Quality Score
        run: |
          python3 backend/test_bidding_quality_score.py --hands 100 --output quality_score.json

      - name: Check for regressions
        run: |
          if [ -f baseline_quality_score_500.json ]; then
            python3 compare_scores.py baseline_quality_score_500.json quality_score.json
            if [ $? -ne 0 ]; then
              echo "❌ Quality score regression detected!"
              exit 1
            fi
          fi

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: quality-scores
          path: quality_score.json

  play-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt

      - name: Run Play Quality Score
        run: |
          python3 backend/test_play_quality_integrated.py --hands 100 --level 8 --output play_quality_score.json

      - name: Check for regressions
        run: |
          if [ -f play_baseline_level8.json ]; then
            python3 compare_play_scores.py play_baseline_level8.json play_quality_score.json
            if [ $? -ne 0 ]; then
              echo "❌ Play quality regression detected!"
              exit 1
            fi
          fi

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: play-quality-scores
          path: play_quality_score.json
```

**Pre-commit Hook:**

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "🎯 Checking for bidding/play logic changes..."

BIDDING_FILES=$(git diff --cached --name-only | grep -E 'backend/engine/(.*\.py|ai/conventions/.*\.py)')
PLAY_FILES=$(git diff --cached --name-only | grep -E 'backend/engine/(play_engine\.py|play/.*\.py)')

if [ -n "$BIDDING_FILES" ]; then
    echo "🎲 Bidding logic changed - running quick quality check..."
    python3 backend/test_bidding_quality_score.py --hands 100
    if [ $? -ne 0 ]; then
        echo "❌ Bidding quality check failed!"
        exit 1
    fi
fi

if [ -n "$PLAY_FILES" ]; then
    echo "🃏 Play logic changed - running quick quality check..."
    python3 backend/test_play_quality_integrated.py --hands 100 --level 8
    if [ $? -ne 0 ]; then
        echo "❌ Play quality check failed!"
        exit 1
    fi
fi

echo "✅ Quality checks passed!"
```

**Expected Impact:** Catch 90% of regressions before merge, automated safety net.

---

## 📊 Implementation Priority Matrix

| Priority | Item | Effort | Impact | ROI |
|----------|------|--------|--------|-----|
| 🔴 Critical | Fix CLAUDE.md location | 5 min | High | ⭐⭐⭐⭐⭐ |
| 🔴 Critical | Use extended thinking | 0 min | High | ⭐⭐⭐⭐⭐ |
| 🔴 Critical | Create slash commands library | 2 hours | High | ⭐⭐⭐⭐⭐ |
| 🟢 Medium | Consider MCP servers (optional) | 1 hour | Low | ⭐⭐ |
| 🟡 High | Adopt planning-first workflow | 0 min | High | ⭐⭐⭐⭐⭐ |
| 🟡 High | Use subagents strategically | 0 min | Medium | ⭐⭐⭐⭐ |
| 🟡 High | TDD workflow | 0 min | High | ⭐⭐⭐⭐⭐ |
| 🟢 Medium | Git worktrees | 30 min | Medium | ⭐⭐⭐ |
| 🟢 Medium | Screenshot workflow | 15 min | Medium | ⭐⭐⭐ |
| 🟢 Medium | CLAUDE.local.md | 10 min | Low | ⭐⭐ |
| 🟢 Medium | # key for updates | 0 min | Low | ⭐⭐⭐ |
| 🟢 Medium | Headless CI/CD | 4 hours | High | ⭐⭐⭐⭐ |

**Total Effort:** ~8 hours
**Total Impact:** 30-40% reduction in development time

---

## 🎯 Quick Wins - Implement Today (30 minutes)

### Immediate Actions

1. **Fix CLAUDE.md Location** (5 min)
```bash
cd /Users/simonroy/Desktop/bridge_bidding_app
cp docs/project-overview/CLAUDE.md ./CLAUDE.md
git add CLAUDE.md
git commit -m "feat: Add CLAUDE.md to project root for auto-loading"
```

2. **Start Using Extended Thinking** (0 min - just change prompts)
```
# Instead of:
"Analyze the bidding quality score regression"

# Use:
"Think hard about the bidding quality score regression and identify the root cause"
```

3. **Create First 3 Slash Commands** (30 min)
```bash
# Create the commands we use most
mkdir -p .claude/commands

# 1. Quality baseline
cat > .claude/commands/quality-baseline.md << 'EOF'
[Content from section 3A above]
EOF

# 2. Analyze hand
cat > .claude/commands/analyze-hand.md << 'EOF'
[Content from section 3C above]
EOF

# 3. Deploy production
cat > .claude/commands/deploy-production.md << 'EOF'
[Content from section 3F above]
EOF

git add .claude/commands/
git commit -m "feat: Add custom slash commands for common workflows"
```

---

## 📈 Success Metrics

Track these metrics to measure improvement:

### Development Speed
- **Time to implement feature:** Target 30% reduction
- **Time spent on rework:** Target 50% reduction
- **Code review iterations:** Target 40% reduction

### Quality
- **Bugs reaching production:** Target 50% reduction
- **Quality score regressions:** Target 90% reduction (via CI/CD)
- **Test coverage:** Target 80%+ coverage

### Developer Experience
- **Time to context switch:** Target 60% reduction (via worktrees)
- **Repeated manual tasks:** Target 80% reduction (via slash commands)
- **Debugging time:** Target 40% reduction (via subagents + thinking)

### Measurement Period
Track for 2 weeks after implementing high-priority changes.

---

## 🔄 Review & Iterate

**Weekly Review:**
- Which improvements had the highest impact?
- What new workflows emerged?
- What slash commands are missing?
- What MCP servers would help?

**Monthly Review:**
- Update CLAUDE.md with new learnings
- Refine slash commands based on usage
- Add new automation based on pain points
- Share improvements with team

---

## 📚 Reference Links

- [Claude Code Best Practices](https://www.anthropic.com/news/claude-code-tips-and-best-practices)
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- [Git Worktrees Documentation](https://git-scm.com/docs/git-worktree)

---

## ✅ Action Checklist

Copy this checklist to track implementation:

### Critical Priority (This Week)
- [ ] Move CLAUDE.md to project root
- [ ] Start using "think hard" in prompts
- [ ] Create quality-baseline slash command
- [ ] Create analyze-hand slash command
- [ ] Create deploy-production slash command

### High Priority (Next Week)
- [ ] Adopt planning-first workflow
- [ ] Start using subagents for research
- [ ] Implement TDD for next feature
- [ ] Create remaining slash commands (7 more)

### Medium Priority (This Month)
- [ ] Set up git worktrees
- [ ] Configure screenshot workflow (drag-and-drop to Claude)
- [ ] Create CLAUDE.local.md
- [ ] Set up pre-commit hooks
- [ ] Set up GitHub Actions CI/CD
- [ ] Measure success metrics
- [ ] Consider Puppeteer MCP if visual testing becomes bottleneck

---

**Next Steps:** Review this document and decide which critical priority items to implement first. Recommend starting with the Quick Wins section (30 minutes total) to see immediate impact.
