/**
 * ExperienceSettings - Settings panel for experience level
 *
 * Allows users to:
 * - Toggle "Unlock All Content" override
 * - Change their experience level
 */

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { useUser } from '../../contexts/UserContext';
import './ExperienceSettings.css';

const EXPERIENCE_OPTIONS = [
  { id: 'beginner', level: 0, label: 'New to Bridge', description: 'Level 0 unlocked' },
  { id: 'intermediate', level: 1, label: 'Intermediate Player', description: 'Levels 0-1 unlocked' },
  { id: 'expert', level: 99, label: 'Experienced', description: 'All levels unlocked' }
];

export const ExperienceSettings = ({ isOpen, onClose }) => {
  const {
    experienceLevel,
    areAllLevelsUnlocked,
    setExperienceLevel,
    toggleUnlockAllLevels
  } = useUser();

  // Find current experience option
  const currentOption = EXPERIENCE_OPTIONS.find(opt => opt.level === experienceLevel) || EXPERIENCE_OPTIONS[0];

  const handleExperienceChange = (option) => {
    setExperienceLevel({
      experienceLevel: option.level,
      areAllLevelsUnlocked: option.level === 99,
      experienceId: option.id
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="experience-settings-dialog w-full max-w-[400px] p-5">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-gray-900">
            Learning Settings
          </DialogTitle>
          <DialogDescription className="text-sm text-gray-600">
            Customize which content is available in Learning Mode.
          </DialogDescription>
        </DialogHeader>

        <div className="settings-section">
          {/* Unlock All Toggle */}
          <div className="setting-item unlock-all-setting">
            <div className="setting-info">
              <label htmlFor="unlock-all" className="setting-label">
                Unlock All Content
              </label>
              <p className="setting-description">
                Access all learning levels regardless of experience level
              </p>
            </div>
            <button
              id="unlock-all"
              role="switch"
              aria-checked={areAllLevelsUnlocked}
              className={`toggle-switch ${areAllLevelsUnlocked ? 'active' : ''}`}
              onClick={toggleUnlockAllLevels}
            >
              <span className="toggle-thumb" />
            </button>
          </div>

          {/* Experience Level Selection */}
          {!areAllLevelsUnlocked && (
            <div className="setting-item experience-level-setting">
              <label className="setting-label">Experience Level</label>
              <p className="setting-description">
                Determines which levels are unlocked by default
              </p>
              <div className="experience-options-compact">
                {EXPERIENCE_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    className={`experience-option-btn ${currentOption.id === option.id ? 'selected' : ''}`}
                    onClick={() => handleExperienceChange(option)}
                  >
                    <span className="option-label">{option.label}</span>
                    <span className="option-description">{option.description}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="settings-footer">
          <Button onClick={onClose} variant="default" className="w-full">
            Done
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ExperienceSettings;
