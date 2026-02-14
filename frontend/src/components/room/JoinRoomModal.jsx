/**
 * RoomModal - Modal for creating or joining a partner practice room
 *
 * Redesigned UX:
 * - Join code input is visible immediately (no click-through)
 * - Create Room is a prominent button
 * - Auto-close when partner joins
 */

import React, { useState, useEffect, useRef } from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './JoinRoomModal.css';

export default function JoinRoomModal({ isOpen, onClose, onJoined }) {
  const {
    createRoom,
    joinRoom,
    dealHands,
    error,
    clearError,
    partnerConnected,
    isHost,
    inRoom,
    gamePhase
  } = useRoom();

  const [roomCode, setRoomCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState(null);
  const [createdRoomCode, setCreatedRoomCode] = useState(null);
  const [waitingForPartner, setWaitingForPartner] = useState(false);
  const hasAutoDealt = useRef(false);

  // Auto-deal and transition when partner connects
  useEffect(() => {
    if (waitingForPartner && partnerConnected && isHost && !hasAutoDealt.current) {
      hasAutoDealt.current = true;

      // Auto-deal a hand
      dealHands().then((result) => {
        if (result.success) {
          // Close modal and go to game
          onJoined?.();
          onClose();
        }
      });
    }
  }, [waitingForPartner, partnerConnected, isHost, dealHands, onJoined, onClose]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setRoomCode('');
      setLocalError(null);
      setCreatedRoomCode(null);
      setWaitingForPartner(false);
      hasAutoDealt.current = false;
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCreateRoom = async () => {
    setIsLoading(true);
    setLocalError(null);
    clearError();

    const result = await createRoom();
    setIsLoading(false);

    if (result.success) {
      setCreatedRoomCode(result.roomCode);
      setWaitingForPartner(true);
    } else {
      setLocalError(result.error || 'Failed to create room');
    }
  };

  const handleJoinRoom = async (e) => {
    e?.preventDefault();

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
    setCreatedRoomCode(null);
    setWaitingForPartner(false);
    hasAutoDealt.current = false;
    clearError();
    onClose();
  };

  const handleStartPlaying = () => {
    onJoined?.();
    onClose();
  };

  const displayError = localError || error;

  // Room created successfully - show code to share and wait for partner
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

          {/* Share buttons */}
          <div className="share-buttons">
            <span className="share-label">Share via:</span>
            <a
              href={`mailto:?subject=Join my Bridge game!&body=Join me for Bridge practice! Enter code ${createdRoomCode} at ${window.location.origin}`}
              className="share-btn share-email"
              title="Share via Email"
            >
              ✉️ Email
            </a>
            <a
              href={`https://wa.me/?text=${encodeURIComponent(`Join me for Bridge practice! Code: ${createdRoomCode}\n${window.location.origin}`)}`}
              className="share-btn share-whatsapp"
              target="_blank"
              rel="noopener noreferrer"
              title="Share via WhatsApp"
            >
              💬 WhatsApp
            </a>
            <a
              href={`sms:?body=${encodeURIComponent(`Join me for Bridge practice! Code: ${createdRoomCode} - ${window.location.origin}`)}`}
              className="share-btn share-sms"
              title="Share via Text"
            >
              📱 Text
            </a>
          </div>

          <div className="waiting-message">
            {partnerConnected ? (
              <>
                <span className="connected-icon">✓</span>
                <p>Partner connected! Starting game...</p>
              </>
            ) : (
              <>
                <div className="waiting-spinner"></div>
                <p>Waiting for partner to join...</p>
              </>
            )}
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn-join"
              onClick={handleStartPlaying}
            >
              {partnerConnected ? 'Go to Game' : 'Go to Lobby'}
            </button>
          </div>

          <div className="modal-footer">
            <p>You'll play as South (host), your partner plays North</p>
          </div>
        </div>
      </div>
    );
  }

  // Main view - Create Room + Join Room with inline code input
  return (
    <div className="join-room-modal-overlay" onClick={handleClose}>
      <div className="join-room-modal modal-combined" onClick={(e) => e.stopPropagation()}>
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

        {/* Create Room Section */}
        <div className="room-section create-section">
          <button
            className="create-room-btn"
            onClick={handleCreateRoom}
            disabled={isLoading}
          >
            <span className="btn-icon">🏠</span>
            <span className="btn-text">
              <span className="btn-title">Create Room</span>
              <span className="btn-desc">Start a new room and invite your partner</span>
            </span>
          </button>
        </div>

        <div className="section-divider">
          <span>or</span>
        </div>

        {/* Join Room Section - Code input visible immediately */}
        <div className="room-section join-section">
          <div className="join-section-header">
            <span className="join-icon">🚪</span>
            <span className="join-title">Join Room</span>
          </div>

          <form onSubmit={handleJoinRoom} className="join-inline-form">
            <input
              type="text"
              value={roomCode}
              onChange={(e) => {
                setRoomCode(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''));
                setLocalError(null);
              }}
              placeholder="Enter 6-digit code"
              maxLength={6}
              className="room-code-input-inline"
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="submit"
              className="join-btn-inline"
              disabled={isLoading || roomCode.length < 6}
            >
              {isLoading ? '...' : 'Join'}
            </button>
          </form>
        </div>

        <div className="modal-footer">
          <p>Both players bid; East-West are AI opponents</p>
        </div>
      </div>
    </div>
  );
}
