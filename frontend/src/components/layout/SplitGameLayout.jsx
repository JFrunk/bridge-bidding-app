/**
 * SplitGameLayout - Layout shell for game + sidebar
 *
 * Handles the mechanics of showing/hiding the Coach sidebar
 * without breaking the game board layout.
 *
 * Key design principles:
 * - Left panel shrinks to fit when sidebar is open
 * - Game table remains centered and visible
 * - No horizontal scrollbar when sidebar opens
 * - Bidding box stays in view
 */
import React from 'react';
import './SplitGameLayout.css';

const SplitGameLayout = ({
  children,           // Main game content (left panel)
  sidebar,            // Sidebar content (right panel)
  isSidebarOpen = false,
  sidebarWidth = 300, // Default sidebar width in pixels
  className = ''
}) => {
  return (
    <div className={`split-game-layout ${isSidebarOpen ? 'sidebar-open' : ''} ${className}`}>
      {/* LEFT PANEL: Game Content */}
      {/* Shrinks to fit when sidebar opens, centers content */}
      <div className="split-game-main">
        <div className="split-game-content">
          {children}
        </div>
      </div>

      {/* RIGHT PANEL: Sidebar */}
      {/* Fixed width, independent scroll, slides in/out */}
      {isSidebarOpen && sidebar && (
        <aside
          className="split-game-sidebar"
          style={{ '--sidebar-width': `${sidebarWidth}px` }}
        >
          {sidebar}
        </aside>
      )}
    </div>
  );
};

export default SplitGameLayout;
