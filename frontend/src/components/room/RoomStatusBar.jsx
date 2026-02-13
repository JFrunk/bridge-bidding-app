/**
 * RoomStatusBar - Minimalist 40px Team Practice Bar
 *
 * P0: Fixed at top, high-contrast, large text for accessibility
 * P1: Shows Drill Focus when convention is selected
 *
 * Layout:
 * - Left: Room Code (high-contrast green) + Drill Focus badge
 * - Center: Status (Waiting / Connected / Your Turn / Partner's Turn)
 * - Right: Leave Session button
 */

import React from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './RoomStatusBar.css';

// Convention display names
const CONVENTION_NAMES = {
  'Stayman': 'Stayman',
  'JacobyTransfer': 'Jacoby Transfer',
  'Blackwood': 'Blackwood',
  'Preempt': 'Preempts',
  'Strong2C': 'Strong 2♣',
};

export default function RoomStatusBar() {
  const {
    roomCode,
    isHost,
    partnerConnected,
    isMyTurn,
    gamePhase,
    currentBidder,
    settings,
    leaveRoom,
    dealHands,
  } = useRoom();

  // Host can deal when partner connected and in waiting phase
  const canDeal = isHost && partnerConnected && gamePhase === 'waiting';

  const handleDeal = async () => {
    const result = await dealHands();
    if (!result.success) {
      console.error('Failed to deal:', result.error);
    }
  };

  // Get drill focus display name
  const drillFocus = settings?.convention_filter
    ? CONVENTION_NAMES[settings.convention_filter] || settings.convention_filter
    : null;

  // Determine status message and class
  const getStatus = () => {
    // Waiting for partner to join
    if (!partnerConnected) {
      return { text: 'Waiting for Partner...', cls: 'waiting' };
    }

    // Waiting phase (before deal)
    if (gamePhase === 'waiting') {
      return { text: 'Partner Connected', cls: 'connected' };
    }

    // Game complete
    if (gamePhase === 'complete') {
      return { text: 'Hand Complete', cls: 'connected' };
    }

    // Active bidding/playing
    if (isMyTurn) {
      return { text: 'Your Turn', cls: 'your-turn' };
    }

    // AI turn
    if (currentBidder === 'E' || currentBidder === 'W') {
      return { text: 'AI Thinking...', cls: 'partner-turn' };
    }

    // Partner's turn
    return { text: "Partner's Turn", cls: 'partner-turn' };
  };

  const status = getStatus();

  return (
    <>
      <div className="room-status-bar">
        {/* Left: Room Code + Drill Focus */}
        <div className="room-status-left">
          <span className="room-code-label">Room:</span>
          <span className="room-code-value">{roomCode}</span>
          {drillFocus && (
            <span className="drill-focus-badge" title="Convention Drill Focus">
              🎯 {drillFocus}
            </span>
          )}
        </div>

        {/* Center: Status */}
        <div className="room-status-center">
          <span className={`status-indicator ${status.cls}`}>
            {status.text}
          </span>
        </div>

        {/* Right: Deal + Leave buttons */}
        <div className="room-status-right">
          {canDeal && (
            <button
              className="btn-deal"
              onClick={handleDeal}
              title="Deal hands and start game"
            >
              Deal &amp; Start
            </button>
          )}
          <button
            className="btn-leave-session"
            onClick={leaveRoom}
            title="Leave session"
          >
            Leave
          </button>
        </div>
      </div>

      {/* Spacer to push content below fixed bar */}
      <div className="room-bar-spacer" />
    </>
  );
}

// Export spacer component for use when bar is shown elsewhere
export function RoomBarSpacer() {
  return <div className="room-bar-spacer" />;
}
