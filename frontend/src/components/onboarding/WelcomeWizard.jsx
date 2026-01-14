/**
 * WelcomeWizard - First-run experience level selection
 *
 * Shows only on first visit (no experienceLevel set).
 * Routes users to appropriate starting point based on selection:
 * - Beginner → Learning Mode (guided lessons)
 * - Rusty → Bidding practice (jump into random hands)
 * - Experienced → Mode Selector (full access, choose their path)
 *
 * Experience Levels:
 * - Beginner (level 0): Only Level 0 unlocked, starts in Learning Mode
 * - Rusty (level 1): Levels 0-1 unlocked, starts in Bidding practice
 * - Expert (level 99): All levels unlocked, goes to Mode Selector
 */

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../ui/dialog';
import './WelcomeWizard.css';

const EXPERIENCE_OPTIONS = [
  {
    id: 'beginner',
    level: 0,
    unlockAll: false,
    route: 'learning',  // Go to Learning Mode
    emoji: '🌱',
    title: 'New to Bridge',
    description: 'I\'m just starting to learn bridge and want to build my skills from the ground up.',
    benefit: 'Start with guided lessons on the basics'
  },
  {
    id: 'rusty',
    level: 1,
    unlockAll: false,
    route: 'bid',  // Go directly to bidding practice
    emoji: '🔄',
    title: 'Rusty Player',
    description: 'I know the basics but haven\'t played in a while. I need a refresher.',
    benefit: 'Jump straight into bidding practice'
  },
  {
    id: 'expert',
    level: 99,
    unlockAll: true,
    route: 'modeSelector',  // Go to Mode Selector (full access)
    emoji: '🎯',
    title: 'Experienced Player',
    description: 'I\'m comfortable with bridge and want access to all content.',
    benefit: 'Choose your own path with full access'
  }
];

export const WelcomeWizard = ({ isOpen, onSelectExperience }) => {
  const handleSelect = (option) => {
    onSelectExperience({
      experienceLevel: option.level,
      areAllLevelsUnlocked: option.unlockAll,
      experienceId: option.id,
      route: option.route  // Include routing destination
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent
        className="welcome-wizard-dialog w-full max-w-[480px] p-6"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader className="text-center mb-6">
          <DialogTitle className="text-2xl font-bold text-gray-900">
            Welcome to My Bridge Buddy!
          </DialogTitle>
          <DialogDescription className="text-base text-gray-600 mt-2">
            Tell us about your bridge experience so we can personalize your journey.
          </DialogDescription>
        </DialogHeader>

        <div className="experience-options">
          {EXPERIENCE_OPTIONS.map((option) => (
            <button
              key={option.id}
              className="experience-card"
              onClick={() => handleSelect(option)}
              data-testid={`experience-${option.id}`}
            >
              <div className="experience-emoji">{option.emoji}</div>
              <div className="experience-content">
                <h3 className="experience-title">{option.title}</h3>
                <p className="experience-description">{option.description}</p>
                <p className="experience-benefit">{option.benefit}</p>
              </div>
              <div className="experience-arrow">→</div>
            </button>
          ))}
        </div>

        <p className="wizard-footer">
          You can change this anytime in Settings.
        </p>
      </DialogContent>
    </Dialog>
  );
};

export default WelcomeWizard;
