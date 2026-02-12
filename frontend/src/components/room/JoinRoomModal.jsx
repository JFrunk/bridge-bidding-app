/**
 * JoinRoomModal - Modal for entering a room code to join partner practice
 */

import React, { useState } from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './JoinRoomModal.css';

export default function JoinRoomModal({ isOpen, onClose, onJoined }) {
  const { joinRoom, error, clearError } = useRoom();
  const [roomCode, setRoomCode] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [localError, setLocalError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!roomCode.trim() || roomCode.length < 6) {
      setLocalError('Please enter a 6-character room code');
      return;
    }

    setIsJoining(true);
    setLocalError(null);
    clearError();

    const result = await joinRoom(roomCode.trim());
    setIsJoining(false);

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
    clearError();
    onClose();
  };

  const displayError = localError || error;

  return (
    <div className="join-room-modal-overlay" onClick={handleClose}>
      <div className="join-room-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={handleClose}>
          &times;
        </button>

        <div className="modal-header">
          <span className="modal-icon">👥</span>
          <h2>Join Partner Practice</h2>
          <p>Enter the room code shared by your partner</p>
        </div>

        {displayError && (
          <div className="modal-error">
            {displayError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="join-form">
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
              type="button"
              className="btn-cancel"
              onClick={handleClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-join"
              disabled={isJoining || roomCode.length < 6}
            >
              {isJoining ? 'Joining...' : 'Join Room'}
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
