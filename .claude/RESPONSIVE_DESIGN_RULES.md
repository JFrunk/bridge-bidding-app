# Responsive Design Rules - Quick Reference

**Date Created:** October 13, 2025
**Status:** MANDATORY for all new components

## The Golden Rule

🚨 **ALL NEW COMPONENTS MUST BE RESPONSIVE BY DEFAULT** 🚨

No desktop-only designs. No fixed sizing. Always mobile-first.

---

## Quick Copy-Paste Patterns

### Buttons
```jsx
// Mobile: 36×36px, Desktop: 48×40px
className="w-9 h-9 sm:w-12 sm:h-10 text-sm sm:text-base"
```

### Containers
```jsx
// Mobile: 12px padding, Desktop: 16px padding
className="p-3 sm:p-4 gap-2 sm:gap-4"
```

### Headings
```jsx
// Mobile: 20px, Desktop: 24px
className="text-xl sm:text-2xl font-bold"
```

### Body Text
```jsx
// Mobile: 14px, Desktop: 16px
className="text-sm sm:text-base"
```

### Grid Layouts
```jsx
// Mobile: 1 column, Tablet: 2, Desktop: 3
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
```

### Flex Stacking
```jsx
// Mobile: vertical, Desktop: horizontal
className="flex flex-col sm:flex-row gap-3 sm:gap-4"
```

### Modal/Dialog
```jsx
// Mobile: full width minus margin, Desktop: max 600px
className="w-full max-w-[95%] sm:max-w-xl p-4 sm:p-6"
```

---

## Tailwind Breakpoints

| Prefix | Min Width | Device Type | Use For |
|--------|-----------|-------------|---------|
| (none) | 0px | Mobile | Base styles |
| `sm:` | 640px | Large phones/small tablets | First breakpoint |
| `md:` | 768px | Tablets | Medium devices |
| `lg:` | 1024px | Desktops | Large screens |
| `xl:` | 1280px | Large desktops | Optional enhancements |

---

## Pre-Submission Checklist

Before creating ANY new component:

- [ ] All sizes use responsive variants (not fixed)
- [ ] Tested mentally at 375px, 768px, 1280px
- [ ] No horizontal scroll on mobile
- [ ] Touch targets min 36px on mobile
- [ ] Text readable on small screens
- [ ] Buttons fit in viewport
- [ ] Images scale properly

---

## Examples in Codebase

**Copy from these files:**
- `frontend/src/components/bridge/BiddingBox.jsx` - Responsive button grid
- `frontend/src/App.css` - Media query examples
- `frontend/src/components/learning/LearningDashboard.css` - Mobile stacking

---

## Common Mistakes to Avoid

### ❌ DON'T DO THIS:
```jsx
// Fixed sizing - not responsive!
<button className="w-12 h-10">Click</button>
<div className="p-4 gap-4">
  <span className="text-base">Text</span>
</div>
```

### ✅ DO THIS INSTEAD:
```jsx
// Responsive sizing
<button className="w-9 h-9 sm:w-12 sm:h-10">Click</button>
<div className="p-3 sm:p-4 gap-2 sm:gap-4">
  <span className="text-sm sm:text-base">Text</span>
</div>
```

---

## Testing Your Component

Ask yourself these questions:

1. **iPhone SE (375px):** Can I tap all buttons? Is text readable?
2. **iPad (768px):** Does layout make sense? No wasted space?
3. **Desktop (1280px):** Full features visible? Not too spread out?

If answer is "no" to any - add more responsive breakpoints.

---

## Why This Matters

- **52% of users** access web apps on mobile
- **Bridge players are often seniors** - may use tablets
- **Responsive design is expected** - not a nice-to-have
- **All critical components already responsive** - maintain the standard

---

## When You're Stuck

**Pattern not listed here?**

1. Check existing responsive components (BiddingBox, etc.)
2. Use mobile-first approach: start with smallest size
3. Add breakpoints only where layout changes
4. Test at 375px, 768px, 1280px

**Still stuck?**

Ask: "How should I make [component] responsive following our standards?"

---

**Remember:** Responsive by default. Mobile-first. Always test.

---

**Last Updated:** October 13, 2025
**See Also:** `.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md`
