# UI/UX Quick Start Card

**For rapid reference in future Claude Code sessions**

---

## 🎯 Before ANY UI Work

```
[ ] Read: .claude/UI_UX_DESIGN_STANDARDS.md
[ ] Check: docs/features/INTERFACE_IMPROVEMENTS_PLAN.md
[ ] Use: Existing component patterns
[ ] Test: All breakpoints (480, 768, 900, 1200px)
```

---

## 🎨 CSS Variables (ALWAYS USE THESE)

### Colors (NO hardcoded colors!)
```css
var(--color-success)    /* #4caf50 - Legal, making contract */
var(--color-danger)     /* #f44336 - Illegal, errors, down */
var(--color-info)       /* #61dafb - Highlights, info */
var(--color-warning)    /* #ff9800 - Warnings, suboptimal */
var(--bg-primary)       /* #1a1a1a - Main dark background */
var(--bg-secondary)     /* #2a2a2a - Cards, panels */
var(--text-primary)     /* #ffffff - Main text */
var(--text-secondary)   /* #aaaaaa - Secondary text */
```

### Spacing (8px grid)
```css
var(--space-2)    /* 8px - Card spacing */
var(--space-4)    /* 16px - Component padding */
var(--space-6)    /* 24px - Component margin */
```

### Typography
```css
var(--text-sm)     /* 14px - Secondary text */
var(--text-base)   /* 16px - Body text */
var(--text-lg)     /* 18px - Subheadings */
var(--text-xl)     /* 20px - Headings */
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile: 0-480px - Base styles */
@media (max-width: 768px) { /* Tablet */ }
@media (max-width: 900px) { /* Small desktop */ }
@media (min-width: 1201px) { /* Large desktop */ }
```

**Touch targets on mobile: Minimum 44x44px**

---

## 🧩 Existing Components (Reuse!)

Located in: `frontend/src/PlayComponents.js`

- `PlayableCard` - Interactive card
- `CurrentTrick` - Center play area
- `PlayTable` - Main layout
- `BiddingSummary` - Auction history
- `ContractDisplay` - Contract info
- `ScoreDisplay` - Final score

---

## ✅ Component Checklist

Before merging:
- [ ] Uses CSS variables (no hardcoded colors)
- [ ] Responsive at 480, 768, 900, 1200px
- [ ] ARIA labels added
- [ ] Keyboard navigable (tab, enter, space)
- [ ] Contrast ratio ≥ 4.5:1 (WCAG AA)
- [ ] Loading state implemented
- [ ] Error messages are educational
- [ ] Respects prefers-reduced-motion
- [ ] Touch targets ≥44px mobile

---

## 🎓 Design Philosophy

**Primary User:** Bridge learners (not experts)

**Every UI decision must answer:**
> "Does this help someone **learn bridge** better?"

**Principles:**
1. Teach, don't just play
2. Progressive disclosure
3. Immediate feedback
4. Consistency over novelty
5. Accessibility first
6. Mobile-first responsive

---

## 🚫 Red Flags

- Hardcoded colors/spacing
- Skipping responsive testing
- No accessibility labels
- Technical error messages
- Missing loading states
- Random sizing values

---

## ✨ Green Flags

- Using CSS variables
- Testing all breakpoints
- ARIA labels present
- Educational error messages
- Smooth, accessible animations
- Following existing patterns

---

## 🔗 Full Documentation

- **Complete Standards:** `.claude/UI_UX_DESIGN_STANDARDS.md`
- **Implementation Plan:** `docs/features/INTERFACE_IMPROVEMENTS_PLAN.md`
- **How It Works:** `.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md`

---

## 💬 Sample Prompt

```
"Add a hint button to the play interface following our UI/UX standards.
It should use the established color palette, spacing system, and
include proper accessibility features."
```

---

**Remember:** Consistency > Novelty. We're building for learners, not showing off design skills.
