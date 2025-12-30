import React, { useState } from 'react';
import './BiddingWorkspace.css';

/**
 * BiddingWorkspace - Tab navigation for bidding practice modes
 *
 * Sub-modes:
 * - Random: Deal random hands for general practice (default, renders tab bar only)
 * - Conventions: Visual grid of conventions organized by level
 * - History: Replay hands from current session
 *
 * The actual bidding UI (hand, table, box) is rendered by App.js below this component.
 * This component just provides the tab navigation and mode-specific panels.
 */
export function BiddingWorkspace({
  activeTab = 'random',
  onTabChange,
  onDealHand,
  onLoadScenario,
  onReplayHand,
  scenarios,
  sessionHands
}) {
  const [selectedTab, setSelectedTab] = useState(activeTab);

  const handleTabChange = (tab) => {
    setSelectedTab(tab);
    if (onTabChange) {
      onTabChange(tab);
    }
    // Auto-deal when switching to random tab
    if (tab === 'random' && onDealHand) {
      // Don't auto-deal, let user click the button
    }
  };

  const handleConventionSelect = (conventionName) => {
    if (onLoadScenario) {
      onLoadScenario(conventionName);
    }
    // Switch to random tab to show the bidding UI
    setSelectedTab('random');
    if (onTabChange) {
      onTabChange('random');
    }
  };

  const handleHistoryReplay = (handData) => {
    if (onReplayHand) {
      onReplayHand(handData);
    }
    // Switch to random tab to show the bidding UI
    setSelectedTab('random');
    if (onTabChange) {
      onTabChange('random');
    }
  };

  const tabs = [
    { id: 'random', label: 'Random', icon: '🎲' },
    { id: 'conventions', label: 'Conventions', icon: '🎯' },
    { id: 'history', label: 'History', icon: '📋' }
  ];

  return (
    <div className="bidding-workspace">
      {/* Tab Navigation */}
      <div className="workspace-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`workspace-tab ${selectedTab === tab.id ? 'active' : ''}`}
            onClick={() => handleTabChange(tab.id)}
            data-testid={`bid-tab-${tab.id}`}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content - Only show panels for non-random tabs */}
      {selectedTab === 'random' && (
        <div className="tab-panel random-panel">
          <div className="panel-header">
            <p className="panel-description">
              Practice bidding with randomly dealt hands. Get instant feedback on every bid.
            </p>
            <button
              className="primary-action-button"
              onClick={onDealHand}
              data-testid="deal-random-hand"
            >
              Deal New Hand
            </button>
          </div>
          {/* The bidding UI (hand, table, box) is rendered by App.js below this component */}
        </div>
      )}

      {selectedTab === 'conventions' && (
        <div className="tab-panel conventions-panel">
          <div className="panel-header">
            <p className="panel-description">
              Select a convention to practice with hands designed to trigger that bidding sequence.
            </p>
          </div>
          <ConventionGrid
            scenarios={scenarios}
            onSelectConvention={handleConventionSelect}
          />
        </div>
      )}

      {selectedTab === 'history' && (
        <div className="tab-panel history-panel">
          <div className="panel-header">
            <p className="panel-description">
              Replay hands from this session to practice the same scenarios again.
            </p>
          </div>
          <SessionHistory
            hands={sessionHands}
            onReplayHand={handleHistoryReplay}
          />
        </div>
      )}
    </div>
  );
}

/**
 * ConventionGrid - Visual grid of conventions organized by level (3-column layout)
 */
function ConventionGrid({ scenarios, onSelectConvention }) {
  // Group scenarios by level
  const grouped = {
    Essential: scenarios?.Essential || [],
    Intermediate: scenarios?.Intermediate || [],
    Advanced: scenarios?.Advanced || []
  };

  const levelColors = {
    Essential: '#51cf66',
    Intermediate: '#fcc419',
    Advanced: '#ff6b6b'
  };

  const levelDescriptions = {
    Essential: 'Core conventions every player should know',
    Intermediate: 'Build on basics with more sophisticated tools',
    Advanced: 'Complex conventions for experienced players'
  };

  if (!scenarios) {
    return <div className="convention-grid-loading">Loading conventions...</div>;
  }

  return (
    <div className="convention-grid">
      {Object.entries(grouped).map(([level, conventions]) => (
        <div key={level} className="convention-column">
          <div
            className="column-header"
            style={{ borderBottomColor: levelColors[level] }}
          >
            <h3>{level}</h3>
            <p className="level-description">{levelDescriptions[level]}</p>
          </div>
          <div className="convention-cards">
            {conventions.map((convention) => (
              <button
                key={convention.name}
                className="convention-card"
                onClick={() => onSelectConvention(convention.name)}
                data-testid={`convention-${convention.name}`}
              >
                <span className="convention-name">{convention.name}</span>
                {convention.description && (
                  <span className="convention-desc">{convention.description}</span>
                )}
              </button>
            ))}
            {conventions.length === 0 && (
              <p className="no-conventions">No conventions available</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * SessionHistory - List of hands from current session with summaries
 */
function SessionHistory({ hands, onReplayHand }) {
  if (!hands || hands.length === 0) {
    return (
      <div className="session-history-empty">
        <p>No hands played in this session yet.</p>
        <p className="hint">Deal a hand to start practicing!</p>
      </div>
    );
  }

  return (
    <div className="session-history">
      <div className="history-list">
        {hands.map((hand, index) => (
          <div key={hand.id || index} className="history-item">
            <div className="history-info">
              <span className="history-number">#{hands.length - index}</span>
              <span className="history-hcp">{hand.hcp} HCP</span>
              {hand.contract && (
                <span className="history-contract">{hand.contract}</span>
              )}
              {hand.result !== undefined && (
                <span className={`history-result ${hand.result >= 0 ? 'made' : 'down'}`}>
                  {hand.result >= 0 ? `+${hand.result}` : hand.result}
                </span>
              )}
            </div>
            <button
              className="replay-button"
              onClick={() => onReplayHand(hand)}
              data-testid={`replay-hand-${index}`}
            >
              Replay
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default BiddingWorkspace;
