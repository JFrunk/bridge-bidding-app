/**
 * RoomStatusBar - Persistent status bar during team practice
 *
 * Shows:
 * - Room code
 * - Partner connection status
 * - Turn indicator
 * - Leave room button
 */

import React from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './RoomStatusBar.css';

export default function RoomStatusBar() {
  const {
    roomCode,
    isHost,
    myPosition,
    partnerConnected,
    isMyTurn,
    gamePhase,
    currentBidder,
    leaveRoom,
  } = useRoom();

  // Get turn status message
  const getTurnStatus = () => {
    if (gamePhase === 'waiting') {
      return partnerConnected ? 'Ready to start' : 'Waiting for partner';
    }

    if (gamePhase === 'complete') {
      return 'Hand complete';
    }

    if (isMyTurn) {
      return 'Your turn';
    }

    // Determine who we're waiting for
    if (currentBidder === 'E' || currentBidder === 'W') {
      return 'AI thinking...';
    }

    return "Partner's turn";
  };

  // Get turn indicator class
  const getTurnClass = () => {
    if (gamePhase === 'waiting') {
      return partnerConnected ? 'status-ready' : 'status-waiting';
    }
    if (isMyTurn) {
      return 'status-your-turn';
    }
    return 'status-waiting';
  };

  return (
    <div className="room-status-bar">
      <div className="room-status-left">
        <span className="room-badge">
          Team Practice
        </span>
        <span className="room-code-mini">
          {roomCode}
        </span>
      </div>

      <div className="room-status-center">
        <span className={`turn-indicator ${getTurnClass()}`}>
          {getTurnStatus()}
        </span>
      </div>

      <div className="room-status-right">
        <span className="position-badge">
          {isHost ? 'South (Host)' : 'North'}
        </span>
        <span className={`partner-status ${partnerConnected ? 'connected' : 'disconnected'}`}>
          Partner: {partnerConnected ? 'Connected' : 'Disconnected'}
        </span>
        <button
          className="btn-leave-room"
          onClick={leaveRoom}
          title="Leave room"
        >
          Leave
        </button>
      </div>
    </div>
  );
}
