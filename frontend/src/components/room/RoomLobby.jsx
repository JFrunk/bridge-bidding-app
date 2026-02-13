/**
 * RoomLobby - Team Practice Entry Point (Standardized Table)
 *
 * P0: Only shows Create/Join options BEFORE entering a room.
 * Once in a room, returns null - RoomStatusBar + standard table take over.
 *
 * This prevents "double lobby" effect. Guest enters code → standard table view.
 */

import React, { useState } from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './RoomLobby.css';

export default function RoomLobby({ onBack }) {
  const {
    inRoom,
    error,
    clearError,
    createRoom,
    joinRoom,
  } = useRoom();

  // Local state for join form
  const [joinCode, setJoinCode] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showJoinForm, setShowJoinForm] = useState(false);

  // STANDARDIZED TABLE: Once in room, don't render lobby UI
  // RoomStatusBar + standard game view handle everything
  if (inRoom) {
    return null;
  }

  // Handle room creation
  const handleCreate = async () => {
    setIsCreating(true);
    clearError();
    const result = await createRoom({
      deal_type: 'random',
      convention_filter: null,
      ai_difficulty: 'advanced',
    });
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

  // Only show create/join options when NOT in a room
  return (
    <div className="room-lobby">
      <div className="room-lobby-header">
        <h2>Team Practice</h2>
        <p>Play with a partner against AI opponents</p>
      </div>

      {error && (
        <div className="room-error">
          {error}
          <button onClick={clearError} className="error-dismiss">×</button>
        </div>
      )}

      {!showJoinForm ? (
        <div className="room-options">
          <div className="room-option-card">
            <h3>Create a Room</h3>
            <p>Start a new practice session and invite your partner</p>
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
        ← Back to Menu
      </button>
    </div>
  );
}
