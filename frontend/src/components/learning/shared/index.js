/**
 * Learning Flows Shared Components
 * Barrel export for all shared components
 *
 * Usage:
 * import { FlowLayout, HandDisplay, ChoiceGrid } from '../shared';
 */

// Layout
export { default as FlowLayout } from './FlowLayout';

// Card/Hand display
export { default as HandDisplay } from './HandDisplay';
export { default as HandDiagram } from './HandDiagram';

// Bidding
export { default as BidTable } from './BidTable';
export { default as InlineBid } from './InlineBid';

// Interactive elements
export { default as ChoiceGrid } from './ChoiceGrid';
export { default as RangeSlider } from './RangeSlider';

// Feedback
export { default as ResultStrip } from './ResultStrip';
export { default as CompareTable } from './CompareTable';

// Scores and progress
export { default as ScoreRow } from './ScoreRow';
export { default as ProgressRing } from './ProgressRing';
export { default as SkillBar } from './SkillBar';
export { default as StreakCalendar } from './StreakCalendar';

// Buttons
export {
  default as Button,
  PrimaryButton,
  SecondaryButton,
  OnFeltButton
} from './Buttons';

// Re-export types for convenience
export * from '../types/hand-types';
export * from '../types/flow-types';
