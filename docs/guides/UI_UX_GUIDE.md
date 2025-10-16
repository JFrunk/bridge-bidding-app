# UI/UX Design Standards - Quick Reference

**For developers and designers working on the Bridge Bidding App interface**

---

## 🚀 Quick Start

### Before ANY UI Work:

1. **Read:** [`.claude/UI_UX_DESIGN_STANDARDS.md`](.claude/UI_UX_DESIGN_STANDARDS.md)
2. **Check:** [`docs/features/INTERFACE_IMPROVEMENTS_PLAN.md`](docs/features/INTERFACE_IMPROVEMENTS_PLAN.md)
3. **Use:** Existing components in `frontend/src/PlayComponents.js`

---

## 🎯 Core Principle

> **"Does this help someone learn bridge better?"**

Every UI decision must answer this question. Our primary users are bridge learners, not experts.

---

## 🎨 CSS Variables (Use These, Never Hardcode)

```css
/* Colors */
var(--color-success)    /* #4caf50 - Legal, making contract */
var(--color-danger)     /* #f44336 - Illegal, errors, down */
var(--color-info)       /* #61dafb - Highlights, info */
var(--bg-primary)       /* #1a1a1a - Main background */
var(--bg-secondary)     /* #2a2a2a - Cards, panels */

/* Spacing (8px grid) */
var(--space-2)    /* 8px */
var(--space-4)    /* 16px */
var(--space-6)    /* 24px */

/* Typography */
var(--text-sm)     /* 14px - Secondary text */
var(--text-base)   /* 16px - Body text */
var(--text-lg)     /* 18px - Subheadings */
```

---

## 📱 Responsive Breakpoints

```css
@media (max-width: 480px)  { /* Small mobile */ }
@media (max-width: 768px)  { /* Mobile */ }
@media (max-width: 900px)  { /* Tablet */ }
@media (min-width: 1201px) { /* Large desktop */ }
```

**Touch targets on mobile: Minimum 44x44px**

---

## ✅ Pre-Flight Checklist

Before implementing any UI:

- [ ] Read UI_UX_DESIGN_STANDARDS.md
- [ ] Using CSS variables (no hardcoded colors)
- [ ] Responsive at all breakpoints
- [ ] ARIA labels added
- [ ] Keyboard navigable
- [ ] Loading states included
- [ ] Error messages are educational
- [ ] Touch targets ≥44px mobile

---

## 📚 Complete Documentation

| Document | Purpose |
|----------|---------|
| [UI_UX_DESIGN_STANDARDS.md](.claude/UI_UX_DESIGN_STANDARDS.md) | **Complete standards** (13,000+ words) |
| [INTERFACE_IMPROVEMENTS_PLAN.md](docs/features/INTERFACE_IMPROVEMENTS_PLAN.md) | **4-phase roadmap** (8,000+ words) |
| [HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md](.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md) | **Auto-loading system** explained |
| [UI_QUICK_START.md](.claude/UI_QUICK_START.md) | **Quick reference** card |
| [UI_UX_STANDARDS_IMPLEMENTATION_COMPLETE.md](UI_UX_STANDARDS_IMPLEMENTATION_COMPLETE.md) | **Implementation summary** |

---

## 🏆 Based on Best Practices From:

- **Funbridge** - Post-hand analysis, mistake identification
- **BBO (Bridge Base Online)** - Multiple practice modes
- **SharkBridge** - Teacher-focused tools
- **Jack Bridge** - Transparent AI, multiple systems

---

## 🎮 Existing Components (Reuse!)

Located in: `frontend/src/PlayComponents.js`

- `PlayableCard` - Interactive card with all states
- `CurrentTrick` - Center play area with winner highlight
- `PlayTable` - Complete play layout
- `BiddingSummary` - Auction history display
- `ContractDisplay` - Contract information
- `ScoreDisplay` - Final score modal

---

## 🚫 Common Mistakes to Avoid

❌ Hardcoding colors instead of using CSS variables
❌ Skipping responsive testing
❌ Ignoring accessibility requirements
❌ Creating UI without checking standards first
❌ Technical error messages instead of educational ones
❌ Random spacing values (not from 8px grid)

---

## ✨ Success Indicators

✅ All components use CSS variables
✅ Spacing follows 8px grid
✅ Works perfectly on mobile
✅ Keyboard navigation works
✅ Error messages teach, not frustrate
✅ Consistent patterns throughout

---

## 🎓 Design Philosophy

1. **Teach, Don't Just Play** - Every interaction is a learning opportunity
2. **Progressive Disclosure** - Start simple, reveal complexity gradually
3. **Immediate Feedback** - Confirm every action visually
4. **Consistency Over Novelty** - Predictable behavior builds confidence
5. **Accessibility First** - Works for everyone
6. **Mobile-First Responsive** - Majority use phones/tablets

---

## 💬 Sample Prompt for Claude Code

```
"Add a hint button to the play interface following our UI/UX standards.
Use the established color palette (var(--color-info)), spacing system,
and include proper accessibility features (ARIA labels, keyboard nav)."
```

---

## 🔗 For More Details

- **Full Standards:** [`.claude/UI_UX_DESIGN_STANDARDS.md`](.claude/UI_UX_DESIGN_STANDARDS.md) (⭐ MUST READ)
- **Documentation Index:** [`docs/project-overview/DOCUMENTATION_INDEX.md`](docs/project-overview/DOCUMENTATION_INDEX.md)
- **Current Components:** [`frontend/src/PlayComponents.js`](frontend/src/PlayComponents.js)

---

## 📝 How This Works

### Auto-Loading System

1. Claude Code starts new session
2. Automatically loads [`.claude/PROJECT_CONTEXT.md`](.claude/PROJECT_CONTEXT.md)
3. Sees "UI/UX DESIGN STANDARDS" section
4. References [`UI_UX_DESIGN_STANDARDS.md`](.claude/UI_UX_DESIGN_STANDARDS.md) for UI work
5. Implements using established patterns

**No manual reminders needed!**

---

## 🎯 Next Steps

### For New Developers:
1. Read [UI_UX_DESIGN_STANDARDS.md](.claude/UI_UX_DESIGN_STANDARDS.md) (30 min)
2. Review [INTERFACE_IMPROVEMENTS_PLAN.md](docs/features/INTERFACE_IMPROVEMENTS_PLAN.md) (15 min)
3. Explore existing components in `frontend/src/PlayComponents.js` (15 min)
4. Start implementing!

### For Starting Phase 1:
See [INTERFACE_IMPROVEMENTS_PLAN.md](docs/features/INTERFACE_IMPROVEMENTS_PLAN.md) Section: Phase 1
- Turn indicators with legal play highlighting
- Contract goal tracker with progress
- Basic hint system
- Enhanced bidding display
- Educational error messages

---

**Remember:** Consistency > Novelty. We're building for learners, not showing off design skills.

---

**Questions?** See [HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md](.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md)

**Last Updated:** 2025-10-12
