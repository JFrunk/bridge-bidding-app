import React from 'react';
import './TopNavigation.css';

/**
 * TopNavigation - Persistent navigation bar with text-only tabs
 *
 * UI Redesign v2: Clean text tabs, header-green background, no icons.
 */

// Check if running on localhost
const isLocalhost = typeof window !== 'undefined' && (
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1'
);

const modules = [
  { id: 'learning', label: 'LEARN', description: 'Structured curriculum' },
  { id: 'bid', label: 'BID', description: 'Bidding practice' },
  { id: 'play', label: 'PLAY', description: 'Card play practice' },
  { id: 'progress', label: 'PROGRESS', description: 'View analytics' },
  // LAB tab only visible on localhost
  ...(isLocalhost ? [{ id: 'lab', label: 'LAB', description: 'Learning flows preview' }] : [])
];

function TopNavigation({ currentModule, onModuleSelect, showTitle = true, children }) {
  return (
    <nav className="top-navigation" role="navigation" aria-label="Main navigation">
      <div className="top-nav-content">
        {/* Brand Title - Left aligned */}
        {showTitle && (
          <div className="nav-brand">
            <h1 className="nav-app-title">My Bridge Buddy</h1>
          </div>
        )}

        {/* Text-only navigation tabs - Center */}
        <div className="nav-tabs">
          {modules.map((module) => (
            <button
              key={module.id}
              className={`nav-tab ${currentModule === module.id ? 'active' : ''}`}
              onClick={() => onModuleSelect(module.id)}
              aria-label={module.description}
              aria-current={currentModule === module.id ? 'page' : undefined}
            >
              {module.label}
            </button>
          ))}
        </div>

        {/* Right section - utility buttons and user menu */}
        <div className="nav-right-section">
          {children}
        </div>
      </div>
    </nav>
  );
}

export default TopNavigation;
