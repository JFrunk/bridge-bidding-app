/**
 * ReviewPage - Unified wrapper for Bidding Review and Play Review
 *
 * Provides a tabbed interface to switch between bidding walkthrough
 * and play-by-play review for the same hand.
 *
 * Fetches both datasets on mount. Tabs are disabled when data is unavailable.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getHandDetail, getBiddingHandDetail } from '../../services/analyticsService';
import BidReviewPage from './BidReviewPage';
import { HandReviewPage } from './hand-review';
import './hand-review/HandReviewPage.css';

/**
 * Derive the bidding hand ID from play hand data.
 * Play endpoint returns session_id + hand_number; bidding uses "session_id:hand_number".
 */
const deriveBiddingId = (playData) => {
  if (!playData?.session_id || playData.hand_number == null) return null;
  return `${playData.session_id}:${playData.hand_number}`;
};

/**
 * Derive the play hand ID from bidding hand data.
 * Bidding endpoint returns play_hand_id (session_hands.id) when available.
 */
const derivePlayId = (biddingData) => {
  return biddingData?.play_hand_id || null;
};

const ReviewPage = ({
  handId,
  initialMode = 'play',
  onBack,
  onPrevHand,
  onNextHand,
  currentIndex,
  totalHands,
  // Action buttons (post-hand flow)
  onPlayAnother,
  onReplay,
  onViewProgress,
  // Source context
  handReviewSource,
}) => {
  const [reviewMode, setReviewMode] = useState(initialMode);
  const [playAvailable, setPlayAvailable] = useState(initialMode === 'play');
  const [biddingAvailable, setBiddingAvailable] = useState(initialMode === 'bidding');
  const [playHandId, setPlayHandId] = useState(initialMode === 'play' ? handId : null);
  const [biddingHandId, setBiddingHandId] = useState(initialMode === 'bidding' ? handId : null);
  const [probing, setProbing] = useState(true);

  // Probe for the alternate dataset on mount
  useEffect(() => {
    let cancelled = false;

    const probeAlternate = async () => {
      try {
        if (initialMode === 'play') {
          // We have play handId — fetch play data to derive bidding ID
          const playData = await getHandDetail(handId);
          if (cancelled) return;

          const biddingId = deriveBiddingId(playData);
          if (biddingId) {
            try {
              await getBiddingHandDetail(biddingId);
              if (cancelled) return;
              setBiddingHandId(biddingId);
              setBiddingAvailable(true);
            } catch {
              // No bidding data — tab stays disabled
            }
          }
        } else {
          // We have bidding handId — fetch bidding data to derive play ID
          const biddingData = await getBiddingHandDetail(handId);
          if (cancelled) return;

          const altPlayId = derivePlayId(biddingData);
          if (altPlayId) {
            try {
              await getHandDetail(altPlayId);
              if (cancelled) return;
              setPlayHandId(altPlayId);
              setPlayAvailable(true);
            } catch {
              // No play data — tab stays disabled
            }
          }
        }
      } catch {
        // Primary data failed — shouldn't happen since parent had it
      } finally {
        if (!cancelled) setProbing(false);
      }
    };

    probeAlternate();
    return () => { cancelled = true; };
  }, [handId, initialMode]);

  // Keyboard shortcut: Tab key toggles mode
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Tab' && e.shiftKey) {
      e.preventDefault();
      setReviewMode(prev => {
        if (prev === 'bidding' && playAvailable) return 'play';
        if (prev === 'play' && biddingAvailable) return 'bidding';
        return prev;
      });
    }
  }, [playAvailable, biddingAvailable]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <>
      {/* Active review content — mode tabs rendered inside each page's header */}
      {reviewMode === 'play' && playHandId ? (
        <HandReviewPage
          handId={playHandId}
          onBack={onBack}
          onPrevHand={onPrevHand}
          onNextHand={onNextHand}
          currentIndex={currentIndex}
          totalHands={totalHands}
          onPlayAnother={onPlayAnother}
          onReplay={onReplay}
          onViewProgress={onViewProgress}
          reviewMode={reviewMode}
          onSetReviewMode={setReviewMode}
          biddingAvailable={biddingAvailable}
          playAvailable={playAvailable}
        />
      ) : reviewMode === 'bidding' && biddingHandId ? (
        <BidReviewPage
          handId={biddingHandId}
          onBack={onBack}
          onPrevHand={onPrevHand}
          onNextHand={onNextHand}
          currentIndex={currentIndex}
          totalHands={totalHands}
          reviewMode={reviewMode}
          onSetReviewMode={setReviewMode}
          biddingAvailable={biddingAvailable}
          playAvailable={playAvailable}
        />
      ) : (
        // Fallback — show whichever is available
        <div className="hand-review-page">
          <div className="loading-state">
            {probing ? 'Loading review...' : 'No review data available'}
          </div>
        </div>
      )}
    </>
  );
};

export default ReviewPage;
