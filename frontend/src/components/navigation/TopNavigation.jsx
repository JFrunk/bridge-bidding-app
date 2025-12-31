import React from 'react';
import './TopNavigation.css';

/**
 * TopNavigation - Persistent navigation bar with 4 module icons
 *
 * Displays colored icons for Learn, Bid, Play, and Progress modules.
 * Shows active state for current module with filled background and indicator.
 */

const modules = [
  {
    id: 'learning',
    icon: '📚',
    label: 'Learn',
    description: 'Structured curriculum'
  },
  {
    id: 'bid',
    icon: '🎲',
    label: 'Bid',
    description: 'Bidding practice'
  },
  {
    id: 'play',
    icon: '♠',
    label: 'Play',
    description: 'Card play practice'
  },
  {
    id: 'progress',
    icon: '📊',
    label: 'Progress',
    description: 'View analytics'
  }
];

function TopNavigation({ currentModule, onModuleSelect, showTitle = true, children }) {
  return (
    <nav className="top-navigation" role="navigation" aria-label="Main navigation">
      <div className="top-nav-content">
        {/* Module Icons */}
        <div className="nav-modules">
          {modules.map((module) => (
            <button
              key={module.id}
              className={`nav-icon nav-icon-${module.id} ${currentModule === module.id ? 'active' : ''}`}
              onClick={() => onModuleSelect(module.id)}
              aria-label={`${module.label}: ${module.description}`}
              aria-current={currentModule === module.id ? 'page' : undefined}
              title={module.label}
            >
              <span className="nav-icon-emoji">{module.icon}</span>
              <span className="nav-icon-label">{module.label}</span>
            </button>
          ))}
        </div>

        {/* App Title */}
        {showTitle && (
          <div className="nav-title-section">
            <h1 className="nav-app-title">My Bridge Buddy</h1>
          </div>
        )}

        {/* Right section - utility buttons and user menu */}
        <div className="nav-right-section">
          {children}
        </div>
      </div>
    </nav>
  );
}

export default TopNavigation;
