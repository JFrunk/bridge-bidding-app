/**
 * RoomModal - Modal for creating or joining a partner practice room
 */

import React, { useState } from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './JoinRoomModal.css';

export default function JoinRoomModal({ isOpen, onClose, onJoined }) {
  const { createRoom, joinRoom, error, clearError } = useRoom();
  const [mode, setMode] = useState(null); // null = choose, 'create', 'join'
  const [roomCode, setRoomCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState(null);
  const [createdRoomCode, setCreatedRoomCode] = useState(null);

  if (!isOpen) return null;

  const handleCreateRoom = async () => {
    setIsLoading(true);
    setLocalError(null);
    clearError();

    const result = await createRoom();
    setIsLoading(false);

    if (result.success) {
      setCreatedRoomCode(result.roomCode);
    } else {
      setLocalError(result.error || 'Failed to create room');
    }
  };

  const handleJoinRoom = async (e) => {
    e.preventDefault();

    if (!roomCode.trim() || roomCode.length < 6) {
      setLocalError('Please enter a 6-character room code');
      return;
    }

    setIsLoading(true);
    setLocalError(null);
    clearError();

    const result = await joinRoom(roomCode.trim());
    setIsLoading(false);

    if (result.success) {
      setRoomCode('');
      onJoined?.();
      onClose();
    } else {
      setLocalError(result.error || 'Failed to join room');
    }
  };

  const handleClose = () => {
    setRoomCode('');
    setLocalError(null);
    setMode(null);
    setCreatedRoomCode(null);
    clearError();
    onClose();
  };

  const handleBack = () => {
    setMode(null);
    setLocalError(null);
    setCreatedRoomCode(null);
    clearError();
  };

  const handleStartPlaying = () => {
    onJoined?.();
    onClose();
  };

  const displayError = localError || error;

  // Room created successfully - show code to share
  if (createdRoomCode) {
    return (
      <div className="join-room-modal-overlay" onClick={handleClose}>
        <div className="join-room-modal" onClick={(e) => e.stopPropagation()}>
          <button className="modal-close-btn" onClick={handleClose}>
            &times;
          </button>

          <div className="modal-header">
            <span className="modal-icon">🎉</span>
            <h2>Room Created!</h2>
            <p>Share this code with your partner</p>
          </div>

          <div className="room-code-display">
            <span className="room-code-value">{createdRoomCode}</span>
            <button
              className="copy-btn"
              onClick={() => {
                navigator.clipboard.writeText(createdRoomCode);
              }}
              title="Copy to clipboard"
            >
              📋
            </button>
          </div>

          <div className="waiting-message">
            <div className="waiting-spinner"></div>
            <p>Waiting for partner to join...</p>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn-join"
              onClick={handleStartPlaying}
            >
              Go to Lobby
            </button>
          </div>

          <div className="modal-footer">
            <p>You'll play as South (host), your partner plays North</p>
          </div>
        </div>
      </div>
    );
  }

  // Choose mode (Create or Join)
  if (mode === null) {
    return (
      <div className="join-room-modal-overlay" onClick={handleClose}>
        <div className="join-room-modal" onClick={(e) => e.stopPropagation()}>
          <button className="modal-close-btn" onClick={handleClose}>
            &times;
          </button>

          <div className="modal-header">
            <span className="modal-icon">👥</span>
            <h2>Partner Practice</h2>
            <p>Play with a human partner against AI opponents</p>
          </div>

          {displayError && (
            <div className="modal-error">
              {displayError}
            </div>
          )}

          <div className="mode-buttons">
            <button
              className="mode-btn mode-btn-create"
              onClick={() => {
                setMode('create');
                handleCreateRoom();
              }}
              disabled={isLoading}
            >
              <span className="mode-icon">🏠</span>
              <span className="mode-title">Create Room</span>
              <span className="mode-desc">Start a new room and invite your partner</span>
            </button>

            <button
              className="mode-btn mode-btn-join"
              onClick={() => setMode('join')}
              disabled={isLoading}
            >
              <span className="mode-icon">🚪</span>
              <span className="mode-title">Join Room</span>
              <span className="mode-desc">Enter a code from your partner</span>
            </button>
          </div>

          <div className="modal-footer">
            <p>Both players bid; East-West are AI opponents</p>
          </div>
        </div>
      </div>
    );
  }

  // Join mode - enter room code
  return (
    <div className="join-room-modal-overlay" onClick={handleClose}>
      <div className="join-room-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={handleClose}>
          &times;
        </button>

        <button className="modal-back-btn" onClick={handleBack}>
          ← Back
        </button>

        <div className="modal-header">
          <span className="modal-icon">🚪</span>
          <h2>Join Room</h2>
          <p>Enter the room code shared by your partner</p>
        </div>

        {displayError && (
          <div className="modal-error">
            {displayError}
          </div>
        )}

        <form onSubmit={handleJoinRoom} className="join-form">
          <div className="room-code-input-wrapper">
            <input
              type="text"
              value={roomCode}
              onChange={(e) => {
                setRoomCode(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''));
                setLocalError(null);
              }}
              placeholder="ABC123"
              maxLength={6}
              className="room-code-input"
              autoFocus
              autoComplete="off"
              spellCheck="false"
            />
            <span className="input-hint">6-character code</span>
          </div>

          <div className="modal-actions">
            <button
              type="submit"
              className="btn-join"
              disabled={isLoading || roomCode.length < 6}
            >
              {isLoading ? 'Joining...' : 'Join Room'}
            </button>
          </div>
        </form>

        <div className="modal-footer">
          <p>You'll play as North, partnering with South (host)</p>
        </div>
      </div>
    </div>
  );
}
