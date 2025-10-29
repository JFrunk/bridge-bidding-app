# Slash Commands Guide

**Created:** 2025-10-29
**Total Commands:** 11 (1 existing + 10 new)

This guide explains all available slash commands in Claude Code for this project.

---

## How to Use Slash Commands

1. Type `/` in Claude Code
2. Browse available commands in the menu
3. Select command or type its name
4. Provide arguments if needed (e.g., `/project:analyze-hand hand_2025-10-28.json`)

**Pro tip:** Tab-complete command names and file paths!

---

## Quality Assurance Commands

### `/project:quality-baseline`

**Purpose:** Run comprehensive baseline quality score testing

**When to use:**
- Before starting work on bidding/play logic
- After completing bidding/play changes
- Establishing performance benchmarks

**What it does:**
1. Checks current branch
2. Runs bidding quality score (500 hands, ~15 min)
3. Runs play quality score (500 hands, Level 8, ~30 min)
4. Saves baselines to `quality_scores/` directory
5. Updates README with baseline entry

**Output:** Baseline files with timestamps and summary scores

**Example:**
```
/project:quality-baseline
```

**Time:** ~45 minutes (bidding + play)

---

### `/project:compare-quality [baseline] [new]`

**Purpose:** Compare quality scores before and after changes

**When to use:**
- After making bidding/play logic changes
- Before committing to verify no regressions
- To quantify improvement from fixes

**What it does:**
1. Lists available baseline files
2. Runs comparison scripts
3. Identifies regressions (blocking, warnings, OK)
4. Displays delta table
5. Recommends: COMMIT, ITERATE, or ROLLBACK

**Blocking criteria:**
- ⛔ Legality < 100%
- ⛔ Composite drops >2%
- ⚠️  Appropriateness drops >5%

**Example:**
```
/project:compare-quality baseline_before.json baseline_after.json

# Or let Claude find files:
/project:compare-quality
```

**Time:** 1-2 minutes

---

### `/project:quick-test [category]`

**Purpose:** Fast feedback loop during development

**When to use:**
- After small code changes (want instant feedback)
- During active iteration
- Before running full test suite

**Options:**
- **Unit tests only:** 30 seconds
- **Unit + Integration:** 2 minutes
- **Specific test file:** Variable
- **Quick bidding score:** 5 minutes (100 hands)
- **Quick play score:** 10 minutes (100 hands, Level 8)

**What it does:**
- Runs fast tests for immediate feedback
- Shows pass/fail status
- Recommends full suite before commit

**Example:**
```
/project:quick-test
/project:quick-test unit
/project:quick-test integration
```

**Time:** 30 seconds - 10 minutes

---

## Development Workflow Commands

### `/project:plan-feature [description]`

**Purpose:** Plan feature implementation before coding

**When to use:**
- Starting any new feature
- Complex changes requiring design
- When architectural decisions needed

**What it does:**
1. **Research** - Understand requirements, explore codebase
2. **Design** - Create architecture diagram, list components
3. **Present** - Show plan with alternatives and risks
4. **Wait for approval** - No code written until approved
5. **Implementation** - Proceed with approved plan

**Output:** Comprehensive plan with:
- Architecture diagram
- Components to create/modify
- Step-by-step breakdown
- Testing strategy
- Documentation plan
- Risk assessment
- Time estimate
- Alternatives considered

**Example:**
```
/project:plan-feature Add export of game history to CSV format
```

**Time:** 15-30 minutes (planning only, no coding)

---

### `/project:start-tdd-feature [description]`

**Purpose:** Start new feature using test-driven development

**When to use:**
- Implementing planned features
- Want TDD workflow enforced
- Need test coverage from start

**What it does:**
1. **Phase 1: Research & Plan** (think hard, no code yet)
2. **Phase 2: Write Tests First** (MANDATORY - tests committed before implementation)
3. **Phase 3: Implement** (make tests pass)
4. **Phase 4: Verify & Document** (full suite, quality baselines, docs)

**Enforces:**
- ✅ Tests written BEFORE implementation
- ✅ Tests committed separately
- ✅ Tests fail initially (prove they test the feature)
- ✅ Quality baselines if applicable
- ✅ Documentation updated

**Example:**
```
/project:start-tdd-feature Add 2NT Jacoby convention support
```

**Time:** Variable (feature-dependent)

---

### `/project:fix-with-tests [bug description]`

**Purpose:** Fix bug using test-driven approach

**When to use:**
- Fixing any bug
- Want regression test created
- Need to prove bug is fixed

**What it does:**
1. **Phase 1: Understand** - Reproduce, identify root cause
2. **Phase 2: Write Regression Test** - Test that FAILS due to bug
3. **Phase 3: Implement Fix** - Make test pass
4. **Phase 4: Systematic Verification** - Search for similar bugs
5. **Phase 5: Document** - Create bug fix docs

**Enforces:**
- ✅ Regression test committed BEFORE fix
- ✅ Test proves bug exists (fails before fix)
- ✅ Test proves bug is fixed (passes after fix)
- ✅ Similar bugs found and fixed (systematic)
- ✅ Documentation created

**Example:**
```
/project:fix-with-tests West bids 3♣ with only 7 HCP (should pass)
```

**Time:** Variable (bug-dependent)

---

### `/project:debug-systematic [issue]`

**Purpose:** Debug complex issue using systematic 4-step analysis

**When to use:**
- Complex bugs affecting multiple components
- Need to understand full scope before fixing
- Want to prevent similar issues

**What it does:**
1. **Identify Root Cause** - Technical explanation (not symptoms)
2. **Search for Patterns** - Find all similar code (2 minutes)
3. **Assess Scope** - List affected files, design solution strategy
4. **Present Analysis** - Show user BEFORE implementing

**Enforces:**
- ✅ Root cause identified
- ✅ Codebase searched for similar patterns
- ✅ All affected files listed
- ✅ Solution designed (local vs architectural)
- ✅ User approval before implementation

**Example:**
```
/project:debug-systematic Dashboard shows stale data when reopened
```

**Time:** 15-30 minutes (analysis), then implementation

---

## Code Quality Commands

### `/project:review-code [target]`

**Purpose:** Comprehensive code review with quality checklist

**When to use:**
- Before committing
- Before creating PR
- Periodic quality checks

**What it reviews:**
1. **Code Quality** - Focused functions, clear names, no duplication
2. **Testing** - Coverage, independence, edge cases
3. **Documentation** - Docstrings, feature docs, CLAUDE.md
4. **Quality Baselines** - No regressions (if applicable)
5. **UI/UX Standards** - Design system, responsive, accessibility
6. **Security** - Input validation, no exposed secrets
7. **Git** - Commit messages, no conflicts

**Output:** Review summary with:
- ✅ Strengths
- ⚠️  Issues found (with severity)
- 📋 Checklist status
- 🎯 Recommendations
- Approval status (approved/comments/changes requested)

**Example:**
```
/project:review-code backend/engine/ai/conventions/blackwood.py
/project:review-code recent changes
/project:review-code frontend/src/components/
```

**Time:** 5-15 minutes (file-dependent)

---

### `/project:analyze-hand [hand_id]`

**Purpose:** Deep analysis of specific hand for bidding AND play issues

**When to use:**
- Investigating reported bidding errors
- Analyzing play quality issues
- Understanding why AI made specific decisions

**What it analyzes:**
- ✅ **Bidding:** Appropriateness (HCP vs bids), convention correctness, SAYC violations
- ✅ **Play:** Card selection quality, trump management, missed opportunities
- ✅ **Scope:** Systematic check for similar issues

**What it does:**
1. Loads hand from `backend/review_requests/`
2. Displays all 4 hands, auction, play sequence
3. Analyzes bidding appropriateness
4. Analyzes play decisions (if available)
5. Identifies specific errors with SAYC rules
6. Explains what SHOULD have happened
7. Uses systematic analysis to find similar issues
8. Recommends fix approach (isolated vs systemic)

**Output:** Comprehensive analysis with:
- Hand state (all 4 positions)
- Auction with explanations
- Issues found (bidding + play)
- Scope analysis (similar patterns)
- Recommended fix

**Example:**
```
/project:analyze-hand hand_2025-10-28_21-46-15.json
/project:analyze-hand backend/review_requests/hand_2025-10-27_13-35-31.json
```

**Time:** 5-10 minutes

---

## Deployment Commands

### `/project:deploy-production`

**Purpose:** Safe production deployment with comprehensive checks

**When to use:**
- Ready to deploy to live production (Render)
- All features tested and approved
- Quality baselines passing

**What it does:**
1. **Safety Checks** (7 steps):
   - Verify development branch
   - Check for uncommitted changes
   - Review recent commits
   - Run full test suite
   - Run bidding quality baseline (500 hands)
   - Run play quality baseline (500 hands)
   - Verify no TODO/FIXME markers

2. **Deployment** (7 steps):
   - Checkout main
   - Merge development
   - Check for database migrations
   - Push to trigger Render deploy
   - Monitor deployment
   - Checkout development

3. **Verification** (2 steps):
   - Test production functionality
   - Monitor error logs

**Blocking conditions:**
- ❌ Any safety check fails
- ❌ Tests failing
- ❌ Quality score regressions
- ❌ Uncommitted changes

**Includes rollback procedure** if deployment fails

**Example:**
```
/project:deploy-production
```

**Time:** ~60 minutes (mostly quality baselines)

---

## Existing Commands

### `/project:check-scope`

**Purpose:** Systematically check if issue affects other parts of codebase

**When to use:**
- After identifying root cause of issue
- Before implementing fix

**What it does:**
1. Pattern search (grep/glob for similar code)
2. Impact analysis (list all affected components)
3. Solution scope (determine if fix should be broad)
4. Present findings (show full scope before implementing)

**Example:**
```
/project:check-scope
```

**Time:** 5-10 minutes

---

## Command Summary Table

| Command | Primary Use | Time | Enforces |
|---------|-------------|------|----------|
| `/project:quality-baseline` | Establish quality metrics | 45 min | Baseline capture |
| `/project:compare-quality` | Detect regressions | 2 min | No blocking regressions |
| `/project:quick-test` | Fast iteration | 30s-10min | Passing tests |
| `/project:plan-feature` | Design before code | 15-30 min | User approval |
| `/project:start-tdd-feature` | TDD for features | Variable | Tests first |
| `/project:fix-with-tests` | TDD for bugs | Variable | Regression tests |
| `/project:debug-systematic` | Systematic debugging | 15-30 min | Full scope analysis |
| `/project:review-code` | Quality assurance | 5-15 min | Standards compliance |
| `/project:analyze-hand` | Hand investigation | 5-10 min | Bidding + play |
| `/project:deploy-production` | Safe deployment | 60 min | All checks pass |
| `/project:check-scope` | Scope analysis | 5-10 min | Systematic check |

---

## Recommended Workflows

### Starting New Feature
```
1. /project:plan-feature [description]
2. Review plan, get approval
3. /project:start-tdd-feature [description]
4. /project:quick-test (iterate)
5. /project:review-code [files]
6. /project:quality-baseline (if bidding/play logic)
7. Commit
```

### Fixing Bug
```
1. /project:debug-systematic [issue]
2. Review analysis, approve approach
3. /project:fix-with-tests [bug]
4. /project:quick-test (verify fix)
5. /project:compare-quality (if bidding/play logic)
6. /project:review-code [files]
7. Commit
```

### Deploying to Production
```
1. /project:quality-baseline (establish current state)
2. Make changes
3. /project:quick-test (during development)
4. /project:compare-quality (before commit)
5. /project:review-code recent changes
6. Commit
7. /project:deploy-production
```

### Investigating Hand Issue
```
1. /project:analyze-hand [hand_id]
2. Review findings
3. If systemic: /project:debug-systematic [issue]
4. If isolated: /project:fix-with-tests [bug]
5. Verify fix with quality baseline
```

---

## Tips for Maximum Effectiveness

1. **Use tab-completion** - Press Tab to complete command names and file paths

2. **Chain commands** - Run related commands in sequence:
   ```
   /project:fix-with-tests [bug]
   /project:quick-test
   /project:review-code [file]
   ```

3. **Let Claude choose files** - Some commands can auto-detect:
   ```
   /project:compare-quality
   # Claude will list available files and ask which to compare
   ```

4. **Review before approving** - Commands with approval gates prevent premature coding:
   - `/project:plan-feature` - Waits for plan approval
   - `/project:debug-systematic` - Waits for analysis approval

5. **Use quick-test during iteration** - Fast feedback (30s) beats waiting for full suite (5+ min)

6. **Run quality baselines before AND after** - Proves no regression

7. **Always use systematic analysis** - Finds 80% of related bugs you'd otherwise miss

8. **Read the command output** - Commands explain what they're doing and why

---

## Command Development

Want to add more commands? Commands are markdown files in `.claude/commands/`:

```bash
# Create new command
cat > .claude/commands/my-command.md << 'EOF'
# Your command instructions here
# Use $ARGUMENTS to accept parameters
EOF

# Available as /project:my-command after restart
```

**Command best practices:**
- Clear step-by-step instructions
- Include safety checks
- Reference CLAUDE.md or CODING_GUIDELINES.md
- Define success criteria
- Add approval gates for high-risk operations
- Provide examples

---

## Troubleshooting

**Command not appearing in menu:**
- Restart Claude Code to reload commands
- Check filename has `.md` extension
- Check file is in `.claude/commands/` directory

**Command fails:**
- Read error message carefully
- Check you're in project root directory
- Verify required files exist (e.g., baseline files for compare-quality)
- Try with simpler arguments first

**Want to modify command:**
- Edit `.md` file in `.claude/commands/`
- Restart Claude Code to reload
- Or just tell Claude: "Modify /project:analyze-hand to also check for..."

---

## Next Steps

1. **Try a command** - Start with `/project:quick-test` to get familiar
2. **Review CLAUDE.md** - Understand the full project context
3. **Read CODING_GUIDELINES.md** - Learn systematic analysis protocol
4. **Use planning-first** - Try `/project:plan-feature` for next feature
5. **Establish baselines** - Run `/project:quality-baseline` to capture current state

---

**Questions?** Just ask Claude! These commands are designed to be self-explanatory and helpful.
