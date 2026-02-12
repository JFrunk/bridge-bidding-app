/**
 * RoomWaitingState - Displayed when guest joins but host hasn't dealt yet
 *
 * Maintains stable 35vh reserved height to prevent layout shift when hands appear.
 */

import React from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './RoomWaitingState.css';

export default function RoomWaitingState() {
  const { roomCode, isHost, partnerConnected, gamePhase } = useRoom();

  // Only show for guest waiting for deal
  if (isHost || gamePhase !== 'waiting') {
    return null;
  }

  return (
    <div className="room-waiting-state">
      <div className="waiting-content">
        <div className="waiting-icon">
          <span className="pulse-ring"></span>
          <span className="icon-inner">👥</span>
        </div>

        <h2 className="waiting-title">Waiting for Host to Deal...</h2>

        <p className="waiting-message">
          {partnerConnected
            ? "You're connected! The host will deal the cards shortly."
            : "Connecting to room..."
          }
        </p>

        <div className="room-info">
          <span className="room-code-label">Room Code:</span>
          <span className="room-code-value">{roomCode}</span>
        </div>

        <div className="position-info">
          <div className="position-badge">
            <span className="position-label">Your Position:</span>
            <span className="position-value">North</span>
          </div>
          <div className="partner-badge">
            <span className="partner-label">Partner (Host):</span>
            <span className="partner-value">South</span>
          </div>
        </div>

        <p className="hint-text">
          Your hand will appear at the bottom of the screen when the host deals.
        </p>
      </div>

      {/* Reserved space for hand - maintains 35vh minimum */}
      <div className="hand-placeholder">
        <div className="placeholder-cards">
          {[...Array(13)].map((_, i) => (
            <div key={i} className="placeholder-card" style={{ '--delay': `${i * 0.05}s` }} />
          ))}
        </div>
        <span className="placeholder-label">Your hand will appear here</span>
      </div>
    </div>
  );
}
