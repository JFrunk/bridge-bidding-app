# How to Ensure Claude Code Follows UI/UX Standards

**Purpose:** This guide explains how to ensure Claude Code consistently references and follows the UI/UX Design Standards across multiple chat sessions.

**Date:** 2025-10-12

---

## Why This Matters

Claude Code can lose context between sessions. We need a system to ensure UI/UX standards are **always** followed, even when:
- Starting a new chat session
- Working with a different Claude Code agent
- Coming back to the project after weeks/months
- Making any UI/UX changes

---

## How It Works: Auto-Loading Context

### 1. Files in `.claude/` Directory

**Claude Code automatically reads files in `.claude/` directory** at the start of each session.

Our setup:
```
.claude/
├── PROJECT_CONTEXT.md              ← Auto-loaded every session
├── UI_UX_DESIGN_STANDARDS.md       ← Referenced from PROJECT_CONTEXT
├── DOCUMENTATION_PRACTICES.md      ← Auto-loaded
├── ARCHITECTURAL_DECISION_FRAMEWORK.md
└── templates/
```

**Key:** The `.claude/PROJECT_CONTEXT.md` file is the **entry point** that tells Claude Code about all other standards.

---

## What We've Implemented

### ✅ Step 1: Created Authoritative UI/UX Standards Document

**File:** `.claude/UI_UX_DESIGN_STANDARDS.md`

**What it contains:**
- Complete design philosophy (learner-first)
- Competitive analysis insights (BBO, Funbridge, SharkBridge, Jack)
- Color palette (CSS variables)
- Spacing system (8px grid)
- Typography scale
- Component examples (copy-paste ready)
- Accessibility requirements
- Responsive design breakpoints
- Animation standards
- Code review checklist
- Educational UI patterns

**Why this works:**
- Single source of truth for ALL UI/UX decisions
- Comprehensive (no need to search elsewhere)
- Practical (code examples included)
- Enforces best practices from competitors

---

### ✅ Step 2: Updated PROJECT_CONTEXT.md

**File:** `.claude/PROJECT_CONTEXT.md`

**What we added:**
- New section: "UI/UX DESIGN STANDARDS"
- Explicit instructions to reference UI_UX_DESIGN_STANDARDS.md
- Checklist of when to consult standards
- Red flags / green flags for UI work
- Quick reference of key variables
- Component library overview

**Why this works:**
- PROJECT_CONTEXT.md is auto-loaded every session
- It explicitly points to UI/UX standards
- Provides quick reference without opening the full doc
- Creates mandatory checkpoint before UI work

---

### ✅ Step 3: Created Implementation Plan

**File:** `docs/features/INTERFACE_IMPROVEMENTS_PLAN.md`

**What it contains:**
- 4-phase roadmap for UI improvements
- Competitive feature analysis
- Detailed mockups and examples
- Technical architecture changes
- Backend API requirements
- Testing strategy

**Why this works:**
- Shows the "big picture" of UI improvements
- Prevents ad-hoc, inconsistent additions
- Provides context for individual UI decisions
- Links back to UI_UX_DESIGN_STANDARDS.md

---

## How to Use This System

### For You (The User)

#### When Starting a New Task:
1. Simply ask Claude Code to work on the UI feature
2. Claude Code will automatically:
   - Load PROJECT_CONTEXT.md
   - See the UI/UX standards reference
   - Consult UI_UX_DESIGN_STANDARDS.md
   - Follow the established patterns

#### When You Notice Standards Not Being Followed:
```
"Please review .claude/UI_UX_DESIGN_STANDARDS.md before proceeding.
Ensure you're following the color palette, spacing system, and
component patterns defined there."
```

#### When Requesting New UI Features:
```
"I'd like to add [feature]. Please check:
1. INTERFACE_IMPROVEMENTS_PLAN.md - Is this already planned?
2. UI_UX_DESIGN_STANDARDS.md - What patterns should you follow?
3. Implement using established standards."
```

---

### For Claude Code (Future Sessions)

When you (Claude Code) start a new session and see UI/UX work:

#### Automatic Checks:
1. ✅ PROJECT_CONTEXT.md is loaded automatically
2. ✅ See "UI/UX DESIGN STANDARDS" section
3. ✅ Note: Must reference UI_UX_DESIGN_STANDARDS.md

#### Before ANY UI Work:
```
[ ] Read .claude/UI_UX_DESIGN_STANDARDS.md
[ ] Check docs/features/INTERFACE_IMPROVEMENTS_PLAN.md
[ ] Identify which component pattern to use
[ ] Use CSS variables (no hardcoded values)
[ ] Follow accessibility requirements
[ ] Test at all responsive breakpoints
```

#### When Implementing:
- Copy component examples from UI_UX_DESIGN_STANDARDS.md
- Use color variables: `var(--color-success)`, not `#4caf50`
- Use spacing variables: `var(--space-4)`, not `16px`
- Use typography variables: `var(--text-lg)`, not `1.125rem`
- Follow the educational UI patterns (hints, errors, feedback)

#### When User Asks for UI Changes Without Mentioning Standards:
**Proactively reference standards:**
```
"Before implementing, I'll reference our UI/UX Design Standards to ensure
consistency with established patterns. I see we have a [Component Pattern]
that applies here..."
```

---

## Testing the System

### Test 1: New Chat Session (You Can Try This Now)

1. Close this chat
2. Start a new Claude Code session
3. Ask: "I want to add a hint button to the play interface. How should I style it?"

**Expected behavior:**
- Claude Code references PROJECT_CONTEXT.md (auto-loaded)
- Claude Code consults UI_UX_DESIGN_STANDARDS.md
- Claude Code suggests using color variables, spacing scale
- Claude Code provides code matching standards

---

### Test 2: Verify Auto-Loading

**Check PROJECT_CONTEXT.md is loaded:**
1. Start new session
2. Ask: "What documentation standards does this project follow?"
3. Claude should reference PROJECT_CONTEXT.md content

**Check UI/UX Standards are referenced:**
1. Ask: "What color should I use for error messages?"
2. Claude should say: "var(--color-danger): #f44336 from UI_UX_DESIGN_STANDARDS.md"

---

### Test 3: Enforcement

**When standards are violated:**
1. User asks: "Add a red error message with hardcoded #FF0000"
2. Claude should respond:
   ```
   "I should use the defined color variable instead:
   var(--color-danger) which is #f44336, as specified in
   UI_UX_DESIGN_STANDARDS.md. This ensures consistency."
   ```

---

## Maintenance

### When to Update UI_UX_DESIGN_STANDARDS.md:

✅ **DO update when:**
- Adding new component patterns
- Establishing new design conventions
- Learning from user feedback
- Discovering better practices
- Extending color palette (rare)
- Adding new breakpoints (rare)

❌ **DON'T update for:**
- One-off special cases
- Project-specific hacks
- Temporary workarounds
- Experiments

### Update Process:
1. Make changes to `.claude/UI_UX_DESIGN_STANDARDS.md`
2. Update "Version History" section at bottom
3. Update "Last Updated" date at top
4. If major changes, inform all users
5. Consider updating INTERFACE_IMPROVEMENTS_PLAN.md if roadmap affected

---

## Troubleshooting

### Problem: Claude Code not following standards

**Diagnosis:**
- Ask Claude: "What UI/UX standards should you be following?"
- If Claude doesn't mention UI_UX_DESIGN_STANDARDS.md, context not loaded

**Solution:**
```
"Please read .claude/PROJECT_CONTEXT.md and .claude/UI_UX_DESIGN_STANDARDS.md
before proceeding with any UI work."
```

---

### Problem: Standards too restrictive

**Diagnosis:**
- User wants to do something not covered by standards
- Feels like standards are blocking innovation

**Solution:**
- Standards should be guidelines, not prison
- For new patterns: establish them, then document
- Update UI_UX_DESIGN_STANDARDS.md with new pattern
- Ensure new pattern aligns with core philosophy (learner-first)

---

### Problem: Standards outdated

**Diagnosis:**
- Technology changes (new CSS features, React updates)
- Competitive apps have better patterns
- User feedback suggests improvements

**Solution:**
- Review UI_UX_DESIGN_STANDARDS.md quarterly
- Compare with competitor apps annually
- Incorporate user feedback monthly
- Version the standards document

---

## Best Practices

### For Users:

1. **Trust the system** - Standards exist for consistency
2. **Reference standards in requests** - "Following UI standards, add X"
3. **Question inconsistencies** - If something doesn't match, ask why
4. **Suggest improvements** - Standards should evolve
5. **Review PR/commits** - Check standards are followed

### For Claude Code:

1. **Proactively reference standards** - Don't wait to be asked
2. **Explain choices** - "Using var(--color-success) per UI standards"
3. **Suggest improvements** - "This could be standardized for reuse"
4. **Be consistent** - Same patterns everywhere
5. **Update standards** - Document new patterns you establish

---

## Success Metrics

### You'll know this is working when:

✅ All UI components use CSS variables (no hardcoded colors)
✅ Spacing is consistent across the app (8px grid)
✅ New components match existing style
✅ Accessibility requirements met everywhere
✅ Responsive design works at all breakpoints
✅ Error messages are educational, not technical
✅ Components are reusable (low duplication)
✅ Code reviews pass quickly (standards followed)
✅ New developers onboard faster (clear patterns)
✅ Users have consistent experience

---

## Quick Reference: How to Ask Claude Code

### ✅ Good Prompts:

```
"Add a hint button following UI_UX_DESIGN_STANDARDS.md"

"Create a turn indicator component using the established patterns"

"Implement error handling with educational messages per our standards"

"Review the play interface for UI/UX standards compliance"

"What component pattern should I use for [feature]?"
```

### ❌ Avoid These:

```
"Add a red button" (no context about standards)

"Make it look nice" (too vague)

"Copy the style from [external site]" (ignores our standards)

"Just do whatever" (no guidance)
```

---

## Integration with Existing Workflows

### Documentation Workflow:
When updating UI → Update UI_UX_DESIGN_STANDARDS.md (if new pattern)

### Testing Workflow:
When testing UI → Check against UI/UX Code Review Checklist

### Code Review:
When reviewing code → Verify UI_UX_DESIGN_STANDARDS.md compliance

### Planning:
When planning features → Reference INTERFACE_IMPROVEMENTS_PLAN.md

---

## Files Overview

| File | Purpose | Auto-Loaded? | Update Frequency |
|------|---------|--------------|------------------|
| `.claude/PROJECT_CONTEXT.md` | Entry point, tells Claude about all standards | ✅ Yes | When adding new standard docs |
| `.claude/UI_UX_DESIGN_STANDARDS.md` | Complete UI/UX reference | No (referenced) | When establishing new patterns |
| `docs/features/INTERFACE_IMPROVEMENTS_PLAN.md` | Roadmap for UI improvements | No | When planning phases |
| `frontend/src/PlayComponents.js` | Existing UI components | No | During implementation |
| `frontend/src/PlayComponents.css` | Existing UI styles | No | During implementation |

---

## Conclusion

**The system is now in place.** Claude Code will:

1. ✅ Automatically load PROJECT_CONTEXT.md every session
2. ✅ See explicit instructions to reference UI/UX standards
3. ✅ Have comprehensive standards document to follow
4. ✅ Have implementation plan for context
5. ✅ Have component examples to copy

**Your job:** Just ask Claude Code to work on UI features. The system handles the rest.

**Claude Code's job:** Reference standards automatically, implement consistently, suggest improvements proactively.

---

## Next Steps

### Immediate (This Session):
- [x] Create UI_UX_DESIGN_STANDARDS.md
- [x] Update PROJECT_CONTEXT.md
- [x] Create INTERFACE_IMPROVEMENTS_PLAN.md
- [x] Create this guide

### Future Sessions:
- [ ] Test with simple UI task
- [ ] Verify standards are followed
- [ ] Update standards as needed
- [ ] Implement Phase 1 features per plan

---

**Questions?**

If Claude Code is not following standards:
1. Explicitly reference `.claude/UI_UX_DESIGN_STANDARDS.md` in your request
2. Ask Claude to review PROJECT_CONTEXT.md section on UI/UX
3. Copy relevant standard into the chat as a reminder

**The system works because:**
- Standards are comprehensive (no ambiguity)
- Standards are accessible (.claude/ directory)
- Standards are practical (code examples)
- Standards are enforced (PROJECT_CONTEXT.md references them)
- Standards are based on competitive analysis (proven patterns)

**Remember:** Consistency > Novelty. The goal is a learner-focused, predictable, accessible bridge app.
