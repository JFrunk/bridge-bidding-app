/**
 * RoomLobby - Team Practice Lobby UI
 *
 * Provides interface for:
 * - Creating a new room (host view)
 * - Joining an existing room (join view)
 * - Room settings (convention filter, AI difficulty)
 * - Waiting for partner / starting game
 */

import React, { useState } from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './RoomLobby.css';

// Available conventions for filtering
const CONVENTIONS = [
  { id: 'Stayman', name: 'Stayman', description: 'Check for 4-card majors after 1NT' },
  { id: 'JacobyTransfer', name: 'Jacoby Transfer', description: 'Transfer to 5+ card major' },
  { id: 'Blackwood', name: 'Blackwood', description: 'Ask for aces before slam' },
  { id: 'Preempt', name: 'Preempt', description: 'Weak two/three bids' },
  { id: 'Strong2C', name: 'Strong 2C', description: 'Game-forcing opening' },
];

// AI difficulty levels
const AI_LEVELS = [
  { id: 'beginner', name: 'Beginner', description: 'Simple play, makes mistakes' },
  { id: 'intermediate', name: 'Intermediate', description: 'Reasonable play' },
  { id: 'advanced', name: 'Advanced', description: 'Strong play, uses strategy' },
  { id: 'expert', name: 'Expert', description: 'Near-optimal double-dummy play' },
];

export default function RoomLobby({ onBack }) {
  const {
    roomCode,
    isHost,
    partnerConnected,
    inRoom,
    settings,
    error,
    clearError,
    createRoom,
    joinRoom,
    leaveRoom,
    updateSettings,
    dealHands,
  } = useRoom();

  // Local state for join form
  const [joinCode, setJoinCode] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showJoinForm, setShowJoinForm] = useState(false);

  // Local settings state (before applying)
  const [localSettings, setLocalSettings] = useState({
    deal_type: 'random',
    convention_filter: null,
    ai_difficulty: 'advanced',
  });

  // Handle room creation
  const handleCreate = async () => {
    setIsCreating(true);
    clearError();
    const result = await createRoom(localSettings);
    setIsCreating(false);

    if (!result.success) {
      console.error('Failed to create room:', result.error);
    }
  };

  // Handle joining a room
  const handleJoin = async (e) => {
    e.preventDefault();
    if (!joinCode.trim()) return;

    setIsJoining(true);
    clearError();
    const result = await joinRoom(joinCode.trim());
    setIsJoining(false);

    if (!result.success) {
      console.error('Failed to join room:', result.error);
    }
  };

  // Handle leaving room
  const handleLeave = () => {
    leaveRoom();
    if (onBack) onBack();
  };

  // Handle starting the game
  const handleStartGame = async () => {
    const result = await dealHands();
    if (!result.success) {
      console.error('Failed to start game:', result.error);
    }
  };

  // Handle settings change
  const handleSettingsChange = async (key, value) => {
    const newSettings = { ...localSettings, [key]: value };
    setLocalSettings(newSettings);

    // If in room and host, also update server
    if (inRoom && isHost) {
      await updateSettings({ [key]: value });
    }
  };

  // If not in a room, show create/join options
  if (!inRoom) {
    return (
      <div className="room-lobby">
        <div className="room-lobby-header">
          <h2>Team Practice</h2>
          <p>Play with a partner against AI opponents</p>
        </div>

        {error && (
          <div className="room-error">
            {error}
            <button onClick={clearError} className="error-dismiss">x</button>
          </div>
        )}

        {!showJoinForm ? (
          <div className="room-options">
            <div className="room-option-card">
              <h3>Create a Room</h3>
              <p>Start a new practice session and invite your partner</p>

              {/* Settings Preview */}
              <div className="settings-preview">
                <div className="setting-row">
                  <label>Deal Type:</label>
                  <select
                    value={localSettings.deal_type}
                    onChange={(e) => handleSettingsChange('deal_type', e.target.value)}
                  >
                    <option value="random">Random</option>
                    <option value="convention">Convention Practice</option>
                  </select>
                </div>

                {localSettings.deal_type === 'convention' && (
                  <div className="setting-row">
                    <label>Convention:</label>
                    <select
                      value={localSettings.convention_filter || ''}
                      onChange={(e) => handleSettingsChange('convention_filter', e.target.value || null)}
                    >
                      <option value="">Select...</option>
                      {CONVENTIONS.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="setting-row">
                  <label>AI Level:</label>
                  <select
                    value={localSettings.ai_difficulty}
                    onChange={(e) => handleSettingsChange('ai_difficulty', e.target.value)}
                  >
                    {AI_LEVELS.map(level => (
                      <option key={level.id} value={level.id}>{level.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                className="btn-primary btn-large"
                onClick={handleCreate}
                disabled={isCreating}
              >
                {isCreating ? 'Creating...' : 'Create Room'}
              </button>
            </div>

            <div className="room-divider">
              <span>or</span>
            </div>

            <div className="room-option-card">
              <h3>Join a Room</h3>
              <p>Enter a room code to join your partner</p>
              <button
                className="btn-secondary btn-large"
                onClick={() => setShowJoinForm(true)}
              >
                Enter Room Code
              </button>
            </div>
          </div>
        ) : (
          <div className="join-form-container">
            <form onSubmit={handleJoin} className="join-form">
              <h3>Enter Room Code</h3>
              <input
                type="text"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                placeholder="ABC123"
                maxLength={6}
                className="room-code-input"
                autoFocus
              />
              <div className="join-form-buttons">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setShowJoinForm(false);
                    setJoinCode('');
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isJoining || joinCode.length < 6}
                >
                  {isJoining ? 'Joining...' : 'Join'}
                </button>
              </div>
            </form>
          </div>
        )}

        <button className="btn-back" onClick={onBack}>
          Back to Menu
        </button>
      </div>
    );
  }

  // In a room - show room status
  return (
    <div className="room-lobby">
      <div className="room-lobby-header">
        <h2>Team Practice Room</h2>
        <div className="room-code-display">
          <span className="room-code-label">Room Code:</span>
          <span className="room-code-value">{roomCode}</span>
          <button
            className="btn-copy"
            onClick={() => navigator.clipboard.writeText(roomCode)}
            title="Copy room code"
          >
            Copy
          </button>
        </div>
      </div>

      {error && (
        <div className="room-error">
          {error}
          <button onClick={clearError} className="error-dismiss">x</button>
        </div>
      )}

      <div className="room-status">
        <div className="player-status">
          <div className="player-slot host">
            <span className="player-label">South (Host)</span>
            <span className="player-indicator connected">You</span>
          </div>
          <div className="player-slot guest">
            <span className="player-label">North (Partner)</span>
            <span className={`player-indicator ${partnerConnected ? 'connected' : 'waiting'}`}>
              {partnerConnected ? 'Connected' : 'Waiting...'}
            </span>
          </div>
          <div className="player-slot ai">
            <span className="player-label">East & West</span>
            <span className="player-indicator ai">AI ({settings.ai_difficulty})</span>
          </div>
        </div>
      </div>

      {/* Host-only settings */}
      {isHost && (
        <div className="room-settings">
          <h3>Practice Settings</h3>
          <div className="settings-grid">
            <div className="setting-row">
              <label>Deal Type:</label>
              <select
                value={settings.deal_type}
                onChange={(e) => handleSettingsChange('deal_type', e.target.value)}
              >
                <option value="random">Random</option>
                <option value="convention">Convention Practice</option>
              </select>
            </div>

            {settings.deal_type === 'convention' && (
              <div className="setting-row">
                <label>Convention:</label>
                <select
                  value={settings.convention_filter || ''}
                  onChange={(e) => handleSettingsChange('convention_filter', e.target.value || null)}
                >
                  <option value="">Select convention...</option>
                  {CONVENTIONS.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="setting-row">
              <label>AI Difficulty:</label>
              <select
                value={settings.ai_difficulty}
                onChange={(e) => handleSettingsChange('ai_difficulty', e.target.value)}
              >
                {AI_LEVELS.map(level => (
                  <option key={level.id} value={level.id}>{level.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Guest view of settings */}
      {!isHost && (
        <div className="room-settings guest-view">
          <h3>Practice Settings</h3>
          <p className="settings-note">Settings are controlled by the host</p>
          <div className="settings-display">
            <span>Deal: {settings.deal_type === 'convention' ? settings.convention_filter : 'Random'}</span>
            <span>AI: {AI_LEVELS.find(l => l.id === settings.ai_difficulty)?.name}</span>
          </div>
        </div>
      )}

      <div className="room-actions">
        {isHost && (
          <button
            className="btn-primary btn-large"
            onClick={handleStartGame}
            disabled={!partnerConnected}
            title={!partnerConnected ? 'Wait for partner to join' : 'Deal hands and start bidding'}
          >
            {partnerConnected ? 'Deal & Start' : 'Waiting for Partner...'}
          </button>
        )}

        {!isHost && !partnerConnected && (
          <div className="waiting-message">
            Waiting for host to start the game...
          </div>
        )}

        <button className="btn-secondary" onClick={handleLeave}>
          Leave Room
        </button>
      </div>
    </div>
  );
}
