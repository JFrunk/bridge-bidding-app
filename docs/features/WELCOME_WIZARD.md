# Welcome Wizard & Experience Level System

**Added:** 2026-01-07
**Status:** Active

## Overview

The Welcome Wizard provides a first-run experience that allows users to self-select their bridge experience level. This selection dynamically controls which Learning Mode levels are immediately accessible.

## User Experience Flow

1. **First Visit Detection**: On first app load, if no `experienceLevel` is stored in localStorage, the Welcome Wizard modal appears
2. **Experience Selection**: User chooses from 3 options:
   - **New to Bridge** (level 0): Only Level 0 unlocked
   - **Rusty Player** (level 1): Levels 0-1 unlocked
   - **Experienced Player** (level 99): All content unlocked
3. **Persistent Storage**: Choice saved to localStorage, wizard doesn't reappear
4. **Settings Access**: Users can change their selection anytime via Settings in Learning Mode

## Components

### WelcomeWizard (`components/onboarding/WelcomeWizard.jsx`)
- Modal dialog with 3 selection cards
- Cannot be dismissed without selection (blocks escape/outside click)
- Clean, welcoming design with emoji icons

### ExperienceSettings (`components/settings/ExperienceSettings.jsx`)
- Accessible via gear icon in Learning Mode header
- "Unlock All Content" toggle for immediate access override
- Experience level selection (when not using unlock all)

### UserContext (`contexts/UserContext.js`)
Extended with:
- `experienceLevel`: number (0, 1, or 99)
- `areAllLevelsUnlocked`: boolean override
- `setExperienceLevel()`: set both values
- `toggleUnlockAllLevels()`: toggle the override
- `isLevelUnlocked(levelNumber)`: check if a level should be accessible
- `shouldShowWelcomeWizard`: boolean for display logic

## Locking Logic

A level is unlocked if ANY of these conditions are true:
1. `areAllLevelsUnlocked` is true (user toggled "Unlock All")
2. `levelNumber <= experienceLevel` (within user's selected range)
3. Backend says unlocked (user completed previous level)

```javascript
const isUnlocked = isLevelUnlocked(level_number) || backendUnlocked;
```

## Storage

Experience settings stored in localStorage under key `bridge_experience_level`:
```json
{
  "level": 1,
  "unlockAll": false,
  "experienceId": "rusty",
  "setAt": "2026-01-07T12:00:00.000Z"
}
```

## Toast Notifications

When clicking a locked level, users see a toast:
> "Complete Level X to unlock, or adjust your Experience Level in settings."

Toast auto-dismisses after 4 seconds.

## Design Decisions

1. **No passwords for experience level**: Device-specific, not tied to account
2. **Kept on logout**: Experience level persists even when logging out
3. **Backend unlock preserved**: If user completes levels naturally, they stay unlocked
4. **Non-blocking design**: Wizard only appears in Learning Mode context
