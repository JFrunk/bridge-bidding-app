/**
 * useHandReview - Custom hook for hand review state management
 *
 * Consolidates all state, data fetching, and computed values
 * used by the hand review page. Extracted from HandReviewModal/HandReviewPage.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { normalizeSuit, extractTrumpStrain } from './constants';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export function useHandReview(handId) {
  const [handData, setHandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [replayPosition, setReplayPosition] = useState(0);

  // Fetch hand details
  useEffect(() => {
    const fetchHandDetail = async () => {
      if (!handId) return;

      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`${API_BASE}/api/hand-detail?hand_id=${handId}`);
        if (!response.ok) throw new Error('Failed to load hand');
        const data = await response.json();
        setHandData(data);
        setReplayPosition(0); // Reset position when loading new hand
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHandDetail();
  }, [handId]);

  // Group plays into tricks
  const tricks = useMemo(() => {
    if (!handData?.play_history) return [];
    const result = [];
    for (let i = 0; i < handData.play_history.length; i += 4) {
      result.push(handData.play_history.slice(i, i + 4));
    }
    return result;
  }, [handData?.play_history]);

  // Get user-controlled positions
  const userControlledPositions = useMemo(() => {
    return handData?.user_controlled_positions || ['S'];
  }, [handData?.user_controlled_positions]);

  // Map decisions by trick number AND position for accurate lookup
  const decisionsByTrickAndPosition = useMemo(() => {
    const map = {};
    if (handData?.play_quality_summary?.all_decisions) {
      handData.play_quality_summary.all_decisions.forEach(d => {
        if (d.position && userControlledPositions.includes(d.position)) {
          const key = `${d.trick_number}_${d.position}`;
          map[key] = d;
        }
      });
    }
    return map;
  }, [handData?.play_quality_summary?.all_decisions, userControlledPositions]);

  // Get trump strain from contract
  const trumpStrain = useMemo(() => {
    return extractTrumpStrain(handData?.contract);
  }, [handData?.contract]);

  // Reconstruct original deal from play_history when deal_data is empty
  // This handles hands where original_deal wasn't preserved at save time
  const fullDeal = useMemo(() => {
    const deal = handData?.deal;
    const ph = handData?.play_history;

    // Check if deal has actual card data
    const hasCards = deal && Object.keys(deal).length > 0 &&
      ['N', 'E', 'S', 'W'].some(pos => deal[pos]?.hand?.length > 0);

    if (hasCards) return deal;

    // Reconstruct from play_history: group all 52 plays by position
    if (!ph || ph.length === 0) return null;

    const reconstructed = { N: { hand: [] }, E: { hand: [] }, S: { hand: [] }, W: { hand: [] } };
    ph.forEach(play => {
      const pos = play.player || play.position;
      if (reconstructed[pos]) {
        reconstructed[pos].hand.push({
          rank: play.rank || play.r,
          suit: normalizeSuit(play.suit || play.s)
        });
      }
    });
    return reconstructed;
  }, [handData?.deal, handData?.play_history]);

  // Compute remaining hands at current replay position
  const remainingHands = useMemo(() => {
    if (!fullDeal || !handData?.play_history) return null;

    const hands = {
      N: [...(fullDeal.N?.hand || [])],
      E: [...(fullDeal.E?.hand || [])],
      S: [...(fullDeal.S?.hand || [])],
      W: [...(fullDeal.W?.hand || [])]
    };

    // Remove cards that have been played up to replayPosition
    const playsToRemove = handData.play_history.slice(0, replayPosition);
    playsToRemove.forEach(play => {
      const pos = play.player || play.position;
      const playRank = play.rank || play.r;
      const playSuit = normalizeSuit(play.suit || play.s);

      if (hands[pos]) {
        const idx = hands[pos].findIndex(c => {
          const cardRank = c.rank || c.r;
          const cardSuit = normalizeSuit(c.suit || c.s);
          return cardRank === playRank && cardSuit === playSuit;
        });
        if (idx !== -1) {
          hands[pos].splice(idx, 1);
        }
      }
    });

    return hands;
  }, [fullDeal, handData?.play_history, replayPosition]);

  // Get current trick cards for replay
  const currentReplayTrick = useMemo(() => {
    if (!handData?.play_history || replayPosition === 0) return [];
    const lastPlayedIdx = replayPosition - 1;
    const trickStartIdx = Math.floor(lastPlayedIdx / 4) * 4;
    const cardsInTrick = (lastPlayedIdx % 4) + 1;
    return handData.play_history.slice(trickStartIdx, trickStartIdx + cardsInTrick);
  }, [handData?.play_history, replayPosition]);

  // Get the current trick number for replay
  const currentReplayTrickNumber = replayPosition === 0 ? 1 : Math.floor((replayPosition - 1) / 4) + 1;

  // Get leader for current replay trick
  const currentReplayLeader = useMemo(() => {
    if (!handData?.play_history || replayPosition === 0) return null;
    const lastPlayedIdx = replayPosition - 1;
    const trickStartIdx = Math.floor(lastPlayedIdx / 4) * 4;
    if (trickStartIdx < handData.play_history.length) {
      return handData.play_history[trickStartIdx]?.player || handData.play_history[trickStartIdx]?.position;
    }
    return null;
  }, [handData?.play_history, replayPosition]);

  // Get decision for current card being viewed in replay
  const currentReplayDecision = useMemo(() => {
    if (!handData?.play_history || replayPosition === 0) return null;

    const lastPlayedIdx = replayPosition - 1;
    const lastPlay = handData.play_history[lastPlayedIdx];
    if (!lastPlay) return null;

    const trickNum = Math.floor(lastPlayedIdx / 4) + 1;
    const position = lastPlay.player || lastPlay.position;

    // Only show decision/info if this position was controlled by user
    if (!userControlledPositions.includes(position)) return null;

    // Look up by trick_position key for precise matching
    const key = `${trickNum}_${position}`;
    const storedDecision = decisionsByTrickAndPosition[key];

    if (storedDecision) return storedDecision;

    // If no stored decision but this is a user-controlled position,
    // create a minimal info object so we can still show the play
    const cardRank = lastPlay.rank || lastPlay.r;
    const cardSuit = normalizeSuit(lastPlay.suit || lastPlay.s);
    return {
      position: position,
      trick_number: trickNum,
      user_card: `${cardRank}${cardSuit}`,
      rating: null,
      score: null,
      feedback: null,
      is_basic_info: true
    };
  }, [handData?.play_history, replayPosition, userControlledPositions, decisionsByTrickAndPosition]);

  // Total plays for navigation
  const totalPlays = handData?.play_history?.length || 0;

  // Determine user's role
  const userRole = useMemo(() => {
    if (!handData) return 'Unknown';
    if (handData.user_role) return handData.user_role;
    const declarer = handData.contract_declarer;
    if (declarer === 'S' || declarer === 'N') return 'Declarer';
    return 'Defender';
  }, [handData]);

  const isUserDefender = userRole === 'Defender';

  // Convert score from declarer's perspective to NS (user's) perspective
  const getScoreForUser = useCallback(() => {
    const score = handData?.hand_score || 0;
    const declarer = handData?.contract_declarer;
    if (declarer === 'E' || declarer === 'W') {
      return -score;
    }
    return score;
  }, [handData?.hand_score, handData?.contract_declarer]);

  // Get result display from user's perspective
  const getResultForUser = useCallback(() => {
    const tricksTaken = handData?.tricks_taken;
    const tricksNeeded = handData?.tricks_needed;
    const made = handData?.made;

    if (tricksTaken === undefined || tricksNeeded === undefined) {
      if (isUserDefender) {
        return made ? { text: 'Opponents Made', isGood: false } : { text: 'Set Contract', isGood: true };
      } else {
        return made ? { text: 'Made', isGood: true } : { text: 'Down', isGood: false };
      }
    }

    if (isUserDefender) {
      if (made) {
        const over = tricksTaken - tricksNeeded;
        if (over > 0) {
          return { text: `Opponents Made +${over}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: false };
        }
        return { text: 'Opponents Made', detail: `(${tricksTaken}/${tricksNeeded})`, isGood: false };
      } else {
        const down = tricksNeeded - tricksTaken;
        return { text: `Set ${down}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: true };
      }
    } else {
      if (made) {
        const over = tricksTaken - tricksNeeded;
        if (over > 0) {
          return { text: `Made +${over}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: true };
        }
        return { text: 'Made', detail: `(${tricksTaken}/${tricksNeeded})`, isGood: true };
      } else {
        const down = tricksNeeded - tricksTaken;
        return { text: `Down ${down}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: false };
      }
    }
  }, [handData?.tricks_taken, handData?.tricks_needed, handData?.made, isUserDefender]);

  // Navigation functions
  const goToStart = useCallback(() => setReplayPosition(0), []);
  const goToEnd = useCallback(() => setReplayPosition(totalPlays), [totalPlays]);
  const goNext = useCallback(() => {
    if (replayPosition < totalPlays) setReplayPosition(p => p + 1);
  }, [replayPosition, totalPlays]);
  const goPrev = useCallback(() => {
    if (replayPosition > 0) setReplayPosition(p => p - 1);
  }, [replayPosition]);

  return {
    // Data
    handData,
    loading,
    error,

    // Replay state
    replayPosition,
    setReplayPosition,
    totalPlays,
    tricks,

    // Computed values
    trumpStrain,
    remainingHands,
    currentReplayTrick,
    currentReplayTrickNumber,
    currentReplayLeader,
    currentReplayDecision,
    userControlledPositions,

    // User perspective
    userRole,
    isUserDefender,
    getScoreForUser,
    getResultForUser,

    // Navigation
    goToStart,
    goToEnd,
    goNext,
    goPrev
  };
}
