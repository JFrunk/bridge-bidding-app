/**
 * WelcomeWizard - First-run experience level selection
 *
 * Shows only on first visit (no experienceLevel set).
 * Allows users to self-select their bridge experience level
 * which determines which Learning Mode levels are unlocked.
 *
 * Experience Levels:
 * - Beginner (level 0): Only Level 0 unlocked
 * - Rusty (level 1): Levels 0-1 unlocked
 * - Expert (level 99): All levels unlocked
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
    emoji: '🌱',
    title: 'New to Bridge',
    description: 'I\'m just starting to learn bridge and want to build my skills from the ground up.',
    benefit: 'Start with the basics and unlock content as you progress'
  },
  {
    id: 'rusty',
    level: 1,
    unlockAll: false,
    emoji: '🔄',
    title: 'Rusty Player',
    description: 'I know the basics but haven\'t played in a while. I need a refresher.',
    benefit: 'Skip the fundamentals and start with opening bids'
  },
  {
    id: 'expert',
    level: 99,
    unlockAll: true,
    emoji: '🎯',
    title: 'Experienced Player',
    description: 'I\'m comfortable with bridge and want access to all content.',
    benefit: 'All learning content unlocked immediately'
  }
];

export const WelcomeWizard = ({ isOpen, onSelectExperience }) => {
  const handleSelect = (option) => {
    onSelectExperience({
      experienceLevel: option.level,
      areAllLevelsUnlocked: option.unlockAll,
      experienceId: option.id
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
            Welcome to Bridge Buddy!
          </DialogTitle>
          <DialogDescription className="text-base text-gray-600 mt-2">
            Customize your learning path by telling us about your experience.
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
