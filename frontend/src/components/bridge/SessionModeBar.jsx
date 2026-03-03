import React from 'react';
import './SessionModeBar.css';

/**
 * SessionModeBar - Mode selector and session info per UI Redesign bid-mockup-v2.html
 *
 * Modes:
 * - Practice: Clean gameplay, no analysis, no coach panel
 * - Coached: Analysis strip visible, coach sidebar visible
 * - Quiz: Separate quiz experience (future implementation)
 *
 * Also displays: Vulnerability, Dealer, Deal source
 */
export function SessionModeBar({
  mode = 'coached',
  onModeChange,
  vulnerability = 'None',
  dealer = 'North',
  dealSource = 'random',
  onDealSourceChange,
  conventions = []
}) {
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const modes = [
    { id: 'practice', label: 'Practice', icon: '🃏' },
    { id: 'coached', label: 'Coached', icon: '🎓' },
    ...(isLocalhost ? [{ id: 'quiz', label: 'Quiz', icon: '❓' }] : [])
  ];

  // Format vulnerability display
  const vulnDisplay = {
    'None': 'None',
    'NS': 'N-S',
    'EW': 'E-W',
    'Both': 'Both',
    'N-S': 'N-S',
    'E-W': 'E-W'
  }[vulnerability] || vulnerability;

  // Determine if vulnerability affects user (NS)
  const isUserVuln = vulnerability === 'NS' || vulnerability === 'N-S' || vulnerability === 'Both';

  return (
    <div className="session-bar">
      {/* Mode Selector */}
      <div className="session-modes">
        {modes.map(m => (
          <button
            key={m.id}
            className={`session-mode ${mode === m.id ? 'active' : ''}`}
            onClick={() => onModeChange?.(m.id)}
            data-testid={`session-mode-${m.id}`}
          >
            <span className="mode-icon">{m.icon}</span>
            <span className="mode-label">{m.label}</span>
          </button>
        ))}
      </div>

      {/* Session Info */}
      <div className="session-info">
        <span className="session-item">
          Vuln: <span className={`vuln-value ${isUserVuln ? 'vuln-danger' : ''}`}>{vulnDisplay}</span>
        </span>
        <span className="session-item">
          Dealer: <span className="dealer-value">{dealer}</span>
        </span>
        <div className="deal-source-group">
          <button
            className={`deal-source ${dealSource === 'random' ? 'active' : ''}`}
            onClick={() => onDealSourceChange?.('random')}
          >
            🎲 Random
          </button>
          {conventions.length > 0 && (
            <select
              className="deal-source conventions-dropdown"
              value={dealSource !== 'random' ? dealSource : ''}
              onChange={(e) => onDealSourceChange?.(e.target.value || 'random')}
            >
              <option value="">📋 Conventions</option>
              {conventions.map(conv => (
                <option key={conv} value={conv}>{conv}</option>
              ))}
            </select>
          )}
        </div>
      </div>
    </div>
  );
}

export default SessionModeBar;
