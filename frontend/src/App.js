import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { flushSync } from 'react-dom';
import './App.css';
import { PlayTable, ScoreDisplay, getSuitOrder } from './PlayComponents';
import { BridgeCard } from './components/bridge/BridgeCard';
import { VerticalCard } from './components/bridge/VerticalCard';
import { BiddingBox as BiddingBoxComponent } from './components/bridge/BiddingBox';
import { ReviewModal } from './components/bridge/ReviewModal';
import { ConventionHelpModal } from './components/bridge/ConventionHelpModal';
import LearningDashboard from './components/learning/LearningDashboard';
import { SessionScorePanel } from './components/session/SessionScorePanel';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SimpleLogin } from './components/auth/SimpleLogin';
import DDSStatusIndicator from './components/DDSStatusIndicator';
import AIDifficultySelector from './components/AIDifficultySelector';
import { getSessionHeaders } from './utils/sessionHelper';

// API URL configuration - uses environment variable in production, localhost in development
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// --- UI Components ---
// Note: Card component migrated to BridgeCard (components/bridge/BridgeCard.jsx)
function HandAnalysis({ points, vulnerability }) {
  if (!points) return null;
  return ( <div className="hand-analysis"><h4>Hand Analysis (Vuln: {vulnerability})</h4><p><strong>HCP:</strong> {points.hcp} + <strong>Dist:</strong> {points.dist_points} = <strong>Total: {points.total_points}</strong></p><div className="suit-points"><div><span className="suit-black">♠</span> {points.suit_hcp['♠']} pts ({points.suit_lengths['♠']})</div><div><span className="suit-red">♥</span> {points.suit_hcp['♥']} pts ({points.suit_lengths['♥']})</div><div><span className="suit-red">♦</span> {points.suit_hcp['♦']} pts ({points.suit_lengths['♦']})</div><div><span className="suit-black">♣</span> {points.suit_hcp['♣']} pts ({points.suit_lengths['♣']})</div></div></div> );
}

function PlayerHand({ position, hand, points, vulnerability }) {
  if (!hand || !points || !Array.isArray(hand)) return null;
  // During bidding, no trump is set, so use no-trump order
  const suitOrder = getSuitOrder(null);
  if (!suitOrder || !Array.isArray(suitOrder)) return null;

  // Use VerticalCard component for East/West positions
  const isVertical = position === 'East' || position === 'West';
  const CardComponent = isVertical ? VerticalCard : BridgeCard;

  // For East/West: arrange hand analysis beside cards (West: left, East: right)
  if (isVertical) {
    // Debug logging
    console.log(`${position} hand:`, hand);
    console.log(`${position} total cards:`, hand?.length);

    return (
      <div className={`player-hand player-${position.toLowerCase()}`}>
        <h3>{position}</h3>
        <div className="vertical-hand-container">
          {/* West: analysis on left, cards on right */}
          {position === 'West' && <HandAnalysis points={points} vulnerability={vulnerability} />}

          <div className="hand-display">
            {suitOrder.map((suit, suitIndex) => {
              const suitCards = hand?.filter(card => card && card.suit === suit) || [];
              console.log(`${position} ${suit}:`, suitCards.length, 'cards', suitCards.map(c => c.rank).join(' '));
              return (
                <div key={suit} className="suit-group">
                  {suitCards.map((card, cardIndex) => {
                    // Calculate absolute card index across all suits
                    const cardsBeforeThisSuit = suitOrder.slice(0, suitIndex).reduce((total, s) => {
                      return total + (hand?.filter(c => c && c.suit === s).length || 0);
                    }, 0);
                    const absoluteIndex = cardsBeforeThisSuit + cardIndex;

                    // Apply 65% overlap for rotated cards: use marginLeft for horizontal stacking
                    // Since cards are rotated 90deg, horizontal negative margin creates vertical appearance
                    // 65% of 70px = 46px overlap, leaving 24px visible per card
                    const inlineStyle = absoluteIndex === 0 ? {} : { marginLeft: '-46px' };

                    return (
                      <CardComponent
                        key={`${suit}-${cardIndex}`}
                        rank={card.rank}
                        suit={card.suit}
                        style={inlineStyle}
                      />
                    );
                  })}
                </div>
              );
            })}
          </div>

          {/* East: cards on left, analysis on right */}
          {position === 'East' && <HandAnalysis points={points} vulnerability={vulnerability} />}
        </div>
      </div>
    );
  }

  // North/South: keep analysis below cards
  return (
    <div className={`player-hand player-${position.toLowerCase()}`}>
      <h3>{position}</h3>
      <div className="hand-display">
        {suitOrder.map(suit => (
          <div key={suit} className="suit-group">
            {hand.filter(card => card && card.suit === suit).map((card, index) => (
              <CardComponent
                key={`${suit}-${index}`}
                rank={card.rank}
                suit={card.suit}
              />
            ))}
          </div>
        ))}
      </div>
      <HandAnalysis points={points} vulnerability={vulnerability} />
    </div>
  );
}
function BiddingTable({ auction, players, nextPlayerIndex, onBidClick, dealer }) {
  // Build table using row-based approach:
  // - Dealer starts on row 0
  // - Each player bids in their column on current row
  // - When North column (column 0) is reached, increment to next row

  const dealerIndex = players.indexOf(dealer);

  // Build a 2D grid: rows[rowIndex][columnIndex] = bid object or null
  const grid = [];
  let currentRow = 0;
  let currentCol = dealerIndex; // Start at dealer's column

  for (let i = 0; i < auction.length; i++) {
    const bid = auction[i];

    // Ensure row exists
    if (!grid[currentRow]) {
      grid[currentRow] = [null, null, null, null]; // [North, East, South, West]
    }

    // Place bid in current position
    grid[currentRow][currentCol] = bid;

    // Move to next column (wrapping around)
    currentCol = (currentCol + 1) % 4;

    // If we just wrapped to North column (column 0), move to next row
    if (currentCol === 0 && i < auction.length - 1) {
      currentRow++;
    }
  }

  // Render grid as table rows
  const rows = grid.map((row, rowIndex) => (
    <tr key={rowIndex}>
      <td onClick={() => row[0] && onBidClick(row[0])}>{row[0]?.bid || ''}</td>
      <td onClick={() => row[1] && onBidClick(row[1])}>{row[1]?.bid || ''}</td>
      <td onClick={() => row[2] && onBidClick(row[2])}>{row[2]?.bid || ''}</td>
      <td onClick={() => row[3] && onBidClick(row[3])}>{row[3]?.bid || ''}</td>
    </tr>
  ));

  // Helper to show dealer indicator
  const dealerIndicator = (pos) => dealer === pos ? ' 🔵' : '';

  return (
    <table className="bidding-table" data-testid="bidding-table">
      <thead>
        <tr>
          <th className={players[nextPlayerIndex] === 'North' ? 'current-player' : ''} data-testid="bidding-header-north">
            North{dealerIndicator('North')}
          </th>
          <th className={players[nextPlayerIndex] === 'East' ? 'current-player' : ''} data-testid="bidding-header-east">
            East{dealerIndicator('East')}
          </th>
          <th className={players[nextPlayerIndex] === 'South' ? 'current-player' : ''} data-testid="bidding-header-south">
            South{dealerIndicator('South')}
          </th>
          <th className={players[nextPlayerIndex] === 'West' ? 'current-player' : ''} data-testid="bidding-header-west">
            West{dealerIndicator('West')}
          </th>
        </tr>
      </thead>
      <tbody data-testid="bidding-table-body">{rows}</tbody>
    </table>
  );
}
// Note: BiddingBox component migrated to components/bridge/BiddingBox.jsx

function App() {
  // Auth state
  const { user, logout, isAuthenticated, loading: authLoading, userId } = useAuth();
  const [showLogin, setShowLogin] = useState(false);

  const [hand, setHand] = useState([]);
  const [handPoints, setHandPoints] = useState(null);
  const [auction, setAuction] = useState([]);
  const [players] = useState(['North', 'East', 'South', 'West']);
  const [dealer, setDealer] = useState('North');

  // DERIVED STATE: Calculate nextPlayerIndex from auction length and dealer
  // This prevents state synchronization bugs between auction and nextPlayerIndex
  const nextPlayerIndex = useMemo(() => {
    const dealerIndex = players.indexOf(dealer);
    if (dealerIndex === -1) {
      console.error('❌ Invalid dealer:', dealer);
      return 0; // Fallback to North
    }
    return (dealerIndex + auction.length) % 4;
  }, [auction.length, dealer, players]);

  const [isAiBidding, setIsAiBidding] = useState(false);
  const [error, setError] = useState('');
  const [displayedMessage, setDisplayedMessage] = useState('');
  const [scenarioList, setScenarioList] = useState([]);
  const [scenariosByLevel, setScenariosByLevel] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [initialDeal, setInitialDeal] = useState(null);
  const [vulnerability, setVulnerability] = useState('None');
  const [allHands, setAllHands] = useState(null);
  const [showHandsThisDeal, setShowHandsThisDeal] = useState(false);
  const [alwaysShowHands, setAlwaysShowHands] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [userConcern, setUserConcern] = useState('');
  const [reviewPrompt, setReviewPrompt] = useState('');
  const [reviewFilename, setReviewFilename] = useState('');
  const [showConventionHelp, setShowConventionHelp] = useState(false);
  const [conventionInfo, setConventionInfo] = useState(null);
  const [showLearningDashboard, setShowLearningDashboard] = useState(false);

  // Session scoring state
  const [sessionData, setSessionData] = useState(null);

  // Loading state for initial system startup
  const [isInitializing, setIsInitializing] = useState(true);

  // Helper function to check if auction is complete
  const isAuctionOver = useCallback((bids) => {
    if (bids.length < 3) return false;
    const nonPassBids = bids.filter(b => b.bid !== 'Pass');

    // All four players passed out (no one bid)
    if (bids.length >= 4 && nonPassBids.length === 0) return true;

    // No bids yet
    if (nonPassBids.length === 0) return false;

    // Three consecutive passes after at least one non-Pass bid
    return bids.slice(-3).map(b => b.bid).join(',') === 'Pass,Pass,Pass';
  }, []);

  // Show login on first visit if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      setShowLogin(true);
    }
  }, [authLoading, isAuthenticated]);

  // Card play state
  const [gamePhase, setGamePhase] = useState('bidding'); // 'bidding' or 'playing'
  const [playState, setPlayState] = useState(null);
  const [dummyHand, setDummyHand] = useState(null);
  const [declarerHand, setDeclarerHand] = useState(null);
  const [isPlayingCard, setIsPlayingCard] = useState(false);
  const [scoreData, setScoreData] = useState(null);

  // Ref to store AI play loop timeout ID so we can cancel it
  const aiPlayTimeoutRef = useRef(null);

  // Ref to store pending trick clear timeout so we can cancel it when user plays
  const trickClearTimeoutRef = useRef(null);

  // Ref to prevent concurrent AI bids from racing
  const isAiBiddingInProgress = useRef(false);

  // Ref to track if we've triggered initial AI bidding after initialization
  // Prevents duplicate triggers while avoiding infinite loops
  const hasTriggeredInitialBid = useRef(false);

  const resetAuction = (dealData, skipInitialAiBidding = false) => {
    setInitialDeal(dealData);
    setHand(dealData.hand);
    setHandPoints(dealData.points);
    setVulnerability(dealData.vulnerability);

    // NEW: Get dealer from backend (Chicago rotation)
    // Backend may return abbreviated (N, E, S, W) or full names (North, East, South, West)
    const dealerFromBackend = dealData.dealer || 'North';

    // Map abbreviated to full names
    const dealerMap = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
    const currentDealer = dealerMap[dealerFromBackend] || dealerFromBackend;

    console.log('🎲 resetAuction:', {
      dealerFromBackend,
      currentDealer,
      players
    });

    setDealer(currentDealer);

    setAuction([]);

    // Reset the AI bidding guards when auction is reset
    isAiBiddingInProgress.current = false;
    hasTriggeredInitialBid.current = false;
    // NOTE: nextPlayerIndex is now derived from dealer + auction.length
    // No need to manually set it - it will auto-calculate on next render

    setDisplayedMessage('');
    setError('');
    // Set AI bidding state - but it won't actually run until isInitializing = false
    // The new useEffect (post-initialization check) will ensure AI starts at the right time
    setIsAiBidding(!skipInitialAiBidding);
    setShowHandsThisDeal(false);
    // Reset play state
    setGamePhase('bidding');
    setPlayState(null);
    setDummyHand(null);
    setDeclarerHand(null);
    setScoreData(null);
    setIsPlayingCard(false);
    if (alwaysShowHands) {
      fetchAllHands();
    } else {
      setAllHands(null);
    }
  };

  const fetchAllHands = async () => {
    try {
      console.log('📡 Fetching from:', `${API_URL}/api/get-all-hands`);
      const response = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ Fetch failed with status:', response.status, 'Error:', errorData);

        // Show user-friendly error message
        if (response.status === 400 && errorData.error) {
          setError(errorData.error);
        } else {
          setError("Failed to fetch all hands.");
        }
        return;
      }
      const data = await response.json();
      console.log('✅ Received all hands data:', data);
      console.log('🔍 Detailed check - North hand length:', data.hands?.North?.hand?.length);
      console.log('🔍 Detailed check - East hand length:', data.hands?.East?.hand?.length);
      console.log('🔍 Detailed check - South hand length:', data.hands?.South?.hand?.length);
      console.log('🔍 Detailed check - West hand length:', data.hands?.West?.hand?.length);
      console.log('🔍 Sample North card:', data.hands?.North?.hand?.[0]);
      setAllHands(data.hands);
      console.log('✅ allHands state scheduled for update with:', data.hands);
    } catch (err) {
      console.error('❌ Error fetching all hands:', err);
      setError("Could not fetch all hands from server.");
    }
  };

  const handleShowHandsThisDeal = async () => {
    console.log('🔵 handleShowHandsThisDeal clicked, current state:', showHandsThisDeal);
    if (!showHandsThisDeal) {
      console.log('📡 Fetching all hands...');
      await fetchAllHands();
    }
    setShowHandsThisDeal(!showHandsThisDeal);
    console.log('🔵 showHandsThisDeal toggled to:', !showHandsThisDeal);
  };

  const handleToggleAlwaysShowHands = async () => {
    const newValue = !alwaysShowHands;
    setAlwaysShowHands(newValue);
    if (newValue) {
      await fetchAllHands();
      setShowHandsThisDeal(true);
    } else {
      setAllHands(null);
      setShowHandsThisDeal(false);
    }
  };

  const handleRequestReview = async () => {
    try {
      const response = await fetch(`${API_URL}/api/request-review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          auction_history: auction,
          user_concern: userConcern,
          game_phase: gamePhase,  // Include current game phase
          user_hand: hand,  // Send actual hand data shown to user
          user_hand_points: handPoints,  // Send actual point data shown to user
          all_hands: allHands,  // Send all hands if available (fallback for production session loss)
          dealer: dealer  // Send dealer to ensure correct declarer determination
        })
      });

      if (!response.ok) throw new Error("Failed to request review.");
      const data = await response.json();

      setReviewFilename(data.filename);

      // Create prompt based on whether file was saved or not
      // Include appropriate slash command to invoke specialist session
      let prompt;
      const slashCommand = gamePhase === 'playing' ? '/play-specialist' : '/bidding-specialist';

      // Other specialist commands (uncomment if issue relates to a different area)
      const otherCommands = gamePhase === 'playing'
        ? `# /bidding-specialist  - if issue is with the auction
# /frontend-specialist - if issue is with UI display
# /learning-specialist - if issue is with feedback/dashboard
# /server-specialist   - if issue is with API/data`
        : `# /play-specialist     - if issue is with card play
# /frontend-specialist - if issue is with UI display
# /learning-specialist - if issue is with feedback/dashboard
# /server-specialist   - if issue is with API/data`;

      if (data.saved_to_file) {
        // Local: file was saved, reference it
        if (gamePhase === 'playing') {
          prompt = `${slashCommand} Analyze the card play in backend/review_requests/${data.filename}.${userConcern ? `\n\nUser's concern: ${userConcern}` : ''}

Focus on declarer play technique, defensive signals, and card selection decisions. Also identify any system errors (e.g., impossible card plays or invalid game states).

---
Other specialists (uncomment if needed):
${otherCommands}`;
        } else {
          prompt = `${slashCommand} Analyze the bidding in backend/review_requests/${data.filename} and identify any errors or questionable bids according to SAYC.${userConcern ? `\n\nUser's concern: ${userConcern}` : ''}

---
Other specialists (uncomment if needed):
${otherCommands}`;
        }
      } else {
        // Render: file not saved, include full data in prompt
        const reviewData = data.review_data;
        if (gamePhase === 'playing') {
          prompt = `${slashCommand} Analyze the card play in this hand.

**Hand Data:**
${JSON.stringify(reviewData, null, 2)}

${userConcern ? `**User's Concern:** ${userConcern}\n\n` : ''}Focus on declarer play technique, defensive signals, and card selection decisions. Also identify any system errors (e.g., impossible card plays or invalid game states).

---
Other specialists (uncomment if needed):
${otherCommands}`;
        } else {
          prompt = `${slashCommand} Analyze this bridge hand and identify any errors or questionable bids according to SAYC.

**Hand Data:**
${JSON.stringify(reviewData, null, 2)}

${userConcern ? `**User's Concern:** ${userConcern}\n\n` : ''}Please provide a detailed analysis of the auction and identify any bidding errors.

---
Other specialists (uncomment if needed):
${otherCommands}`;
        }
      }

      setReviewPrompt(prompt);
      setShowReviewModal(true);
    } catch (err) {
      setError("Could not save review request.");
    }
  };

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(reviewPrompt);
    setDisplayedMessage('✅ Prompt copied to clipboard! Paste it to Claude Code for analysis.');
  };

  const handleCloseReviewModal = () => {
    setShowReviewModal(false);
    setUserConcern('');
    setReviewPrompt('');
    setReviewFilename('');
  };

  const handleShowConventionHelp = async () => {
    if (!selectedScenario) return;

    // Extract convention name from scenario (e.g., "Jacoby Transfer Test" -> "Jacoby Transfer")
    const conventionName = selectedScenario.replace(' Test', '');

    try {
      const response = await fetch(`${API_URL}/api/convention-info?name=${encodeURIComponent(conventionName)}`, { headers: { ...getSessionHeaders() } });
      if (!response.ok) {
        setError(`No help available for ${conventionName}`);
        return;
      }
      const data = await response.json();
      setConventionInfo(data);
      setShowConventionHelp(true);
    } catch (err) {
      setError("Could not fetch convention information.");
    }
  };

  const handleCloseConventionHelp = () => {
    setShowConventionHelp(false);
    setConventionInfo(null);
  };

  // ========== CARD PLAY FUNCTIONS ==========

  const startPlayPhase = async () => {
    try {
      const auctionBids = auction.map(a => a.bid);

      const response = await fetch(`${API_URL}/api/start-play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          auction_history: auctionBids,
          vulnerability: vulnerability,
          dealer: dealer  // NEW: Send dealer to backend
        })
      });

      if (!response.ok) throw new Error("Failed to start play phase");

      const data = await response.json();
      console.log('Play started:', data);

      // Fetch initial play state before transitioning
      const stateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (stateResponse.ok) {
        const state = await stateResponse.json();
        setPlayState(state);
        console.log('✅ Initial play state set:', state);
        console.log('🎭 Key positions:', {
          declarer: state.contract.declarer,
          dummy: state.dummy,
          next_to_play: state.next_to_play,
          dummy_revealed: state.dummy_revealed,
          visible_hands: state.visible_hands ? Object.keys(state.visible_hands) : 'N/A'
        });

        // === BUG FIX: Use visible_hands from backend to populate declarer hand ===
        // Backend's BridgeRulesEngine determines which hands should be visible
        const declarerPos = state.contract.declarer;
        if (state.visible_hands && state.visible_hands[declarerPos]) {
          const declarerCards = state.visible_hands[declarerPos].cards || [];
          console.log('👁️ Setting declarer hand from visible_hands (startPlayPhase):', {
            declarerPos,
            cardCount: declarerCards.length,
            visible_hands_keys: Object.keys(state.visible_hands)
          });
          setDeclarerHand(declarerCards);
        } else if (state.dummy === 'S') {
          // FALLBACK: If visible_hands not available, use old method
          console.log('⚠️ visible_hands not available, falling back to /api/get-all-hands');
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            const declarerCards = handsData.hands[declarerPos]?.hand || [];
            console.log('🃏 Declarer hand fetched (fallback):', {
              declarerPos,
              cardCount: declarerCards.length,
              dummy_revealed: state.dummy_revealed
            });
            setDeclarerHand(declarerCards);
          }
        }

        // === NEW FIX: Update South's hand from visible_hands ===
        // Critical for when South is declarer - ensures user's own hand is visible
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || [];
          console.log('👁️ Updating South hand from visible_hands (startPlayPhase):', {
            cardCount: southCards.length,
            visible_hands_keys: Object.keys(state.visible_hands)
          });
          setHand(southCards);
        }
      }

      // Transition to play phase
      setGamePhase('playing');
      setShowHandsThisDeal(false);  // Hide all hands when transitioning to play
      setAllHands(null);  // Clear all hands data
      setDisplayedMessage(`Contract: ${data.contract}. Opening leader: ${data.opening_leader}`);

      // CRITICAL FIX: Use setTimeout to ensure gamePhase updates BEFORE triggering AI loop
      // This prevents race condition where useEffect checks gamePhase before it updates to 'playing'
      // Bug: AI play loop was not triggering because gamePhase was still 'bidding' when useEffect ran
      setTimeout(() => {
        console.log('🎬 Triggering AI play loop after game phase transition');
        setIsPlayingCard(true);
      }, 50);
    } catch (err) {
      console.error('Error starting play:', err);
      setError('Failed to start card play phase');
    }
  };

  const handleCardPlay = async (card) => {
    console.log('🃏 handleCardPlay called:', { card, isPlayingCard });

    // If there's a pending trick clear, execute it immediately before user plays
    if (trickClearTimeoutRef.current) {
      console.log('⚡ User played - clearing pending trick immediately');
      clearTimeout(trickClearTimeoutRef.current);
      trickClearTimeoutRef.current = null;

      // Clear the trick immediately
      await fetch(`${API_URL}/api/clear-trick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
      });

      // Fetch and update state after clearing
      const clearedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (clearedStateResponse.ok) {
        const clearedState = await clearedStateResponse.json();
        setPlayState(clearedState);
      }
    }

    try {
      console.log('✅ Playing card:', card);
      setIsPlayingCard(true);

      const response = await fetch(`${API_URL}/api/play-card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          position: 'S',
          card: { rank: card.rank, suit: card.suit }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Illegal card play');
      }

      const data = await response.json();
      console.log('Card played:', data);

      // Update hand (remove played card)
      setHand(prevHand => prevHand.filter(c =>
        !(c.rank === card.rank && c.suit === card.suit)
      ));

      // Fetch updated play state to show the card that was just played
      const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (updatedStateResponse.ok) {
        const updatedState = await updatedStateResponse.json();
        setPlayState(updatedState);
        console.log('🔄 Updated play state after user play:', {
          trick_size: updatedState.current_trick.length,
          current_trick: updatedState.current_trick
        });
      }

      // Check if trick just completed
      if (data.trick_complete && data.trick_winner) {
        // Trick is complete - show winner for 2.5 seconds before clearing
        console.log(`Trick complete! Winner: ${data.trick_winner}`);

        // Wait 2.5 seconds to display the winner (50% faster than before)
        await new Promise(resolve => {
          trickClearTimeoutRef.current = setTimeout(resolve, 2500);
        });

        // Clear timeout ref since we're about to clear
        trickClearTimeoutRef.current = null;

        // Clear the trick and get updated state
        await fetch(`${API_URL}/api/clear-trick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
        });

        // Fetch state after trick clear to see who's next
        const nextStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
        if (nextStateResponse.ok) {
          const nextState = await nextStateResponse.json();
          setPlayState(nextState);

          // Check if all 13 tricks are complete
          const totalTricks = Object.values(nextState.tricks_won).reduce((a, b) => a + b, 0);
          if (totalTricks === 13) {
            console.log('🏁 All 13 tricks complete after user card! Fetching final score...');
            // Play complete - calculate score
            const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
              body: JSON.stringify({ vulnerability: vulnerability })
            });

            if (scoreResponse.ok) {
              const scoreData = await scoreResponse.json();
              console.log('✅ Score calculated:', scoreData);
              setScoreData(scoreData);
            } else {
              const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
              console.error('❌ Failed to get score:', errorData);
              setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
            }

            setIsPlayingCard(false);
            return;
          }

          // Start AI loop only if it's not the user's turn
          const nextIsUserTurn = nextState.next_to_play === 'S' ||
                                (nextState.next_to_play === nextState.dummy && nextState.contract.declarer === 'S');
          if (!nextIsUserTurn) {
            // Reset flag first to ensure useEffect triggers, then set it back to true
            setIsPlayingCard(false);
            setTimeout(() => setIsPlayingCard(true), 100);
          } else {
            setIsPlayingCard(false);
          }
        }
      } else {
        // Trick not complete - check whose turn is next
        const updatedState = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } }).then(r => r.json());
        setPlayState(updatedState);

        const nextIsUserTurn = updatedState.next_to_play === 'S' ||
                              (updatedState.next_to_play === updatedState.dummy && updatedState.contract.declarer === 'S');
        if (!nextIsUserTurn) {
          // Reset flag first to ensure useEffect triggers, then set it back to true
          setIsPlayingCard(false);
          setTimeout(() => setIsPlayingCard(true), 100);
        } else {
          setIsPlayingCard(false);
        }
      }

    } catch (err) {
      console.error('Error playing card:', err);
      setError(err.message);
      setIsPlayingCard(false);
    }
  };

  const handleDeclarerCardPlay = async (card) => {
    if (!playState) return;

    // If there's a pending trick clear, execute it immediately before user plays
    if (trickClearTimeoutRef.current) {
      console.log('⚡ User played (declarer) - clearing pending trick immediately');
      clearTimeout(trickClearTimeoutRef.current);
      trickClearTimeoutRef.current = null;

      // Clear the trick immediately
      await fetch(`${API_URL}/api/clear-trick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
      });

      // Fetch and update state after clearing
      const clearedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (clearedStateResponse.ok) {
        const clearedState = await clearedStateResponse.json();
        setPlayState(clearedState);
      }
    }

    try {
      setIsPlayingCard(true);

      // Declarer position (partner of dummy)
      const declarerPosition = playState.contract.declarer;

      const response = await fetch(`${API_URL}/api/play-card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          position: declarerPosition,
          card: { rank: card.rank, suit: card.suit }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Illegal card play');
      }

      const data = await response.json();
      console.log('Declarer card played:', data);

      // Update declarer hand (remove played card)
      setDeclarerHand(prevHand => prevHand ? prevHand.filter(c =>
        !(c.rank === card.rank && c.suit === card.suit)
      ) : prevHand);

      // Fetch updated play state to show the card that was just played
      const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (updatedStateResponse.ok) {
        const updatedState = await updatedStateResponse.json();
        setPlayState(updatedState);
        console.log('🔄 Updated play state after declarer play:', {
          trick_size: updatedState.current_trick.length,
          current_trick: updatedState.current_trick
        });
      }

      // Check if trick just completed
      if (data.trick_complete && data.trick_winner) {
        // Trick is complete - show winner for 2.5 seconds before clearing
        console.log(`Trick complete! Winner: ${data.trick_winner}`);

        // Wait 2.5 seconds to display the winner (50% faster than before)
        await new Promise(resolve => {
          trickClearTimeoutRef.current = setTimeout(resolve, 2500);
        });

        // Clear timeout ref since we're about to clear
        trickClearTimeoutRef.current = null;

        // Clear the trick and get updated state
        await fetch(`${API_URL}/api/clear-trick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
        });

        // Fetch state after trick clear to see who's next
        const nextStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
        if (nextStateResponse.ok) {
          const nextState = await nextStateResponse.json();
          setPlayState(nextState);

          // Check if all 13 tricks are complete
          const totalTricks = Object.values(nextState.tricks_won).reduce((a, b) => a + b, 0);
          if (totalTricks === 13) {
            console.log('🏁 All 13 tricks complete after user card! Fetching final score...');
            // Play complete - calculate score
            const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
              body: JSON.stringify({ vulnerability: vulnerability })
            });

            if (scoreResponse.ok) {
              const scoreData = await scoreResponse.json();
              console.log('✅ Score calculated:', scoreData);
              setScoreData(scoreData);
            } else {
              const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
              console.error('❌ Failed to get score:', errorData);
              setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
            }

            setIsPlayingCard(false);
            return;
          }

          // Start AI loop only if it's not the user's turn
          const nextIsUserTurn = nextState.next_to_play === 'S' ||
                                (nextState.next_to_play === nextState.dummy && nextState.contract.declarer === 'S');
          if (!nextIsUserTurn) {
            // Reset flag first to ensure useEffect triggers, then set it back to true
            setIsPlayingCard(false);
            setTimeout(() => setIsPlayingCard(true), 100);
          } else {
            setIsPlayingCard(false);
          }
        }
      } else {
        // Trick not complete - check whose turn is next
        const updatedState = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } }).then(r => r.json());
        setPlayState(updatedState);

        const nextIsUserTurn = updatedState.next_to_play === 'S' ||
                              (updatedState.next_to_play === updatedState.dummy && updatedState.contract.declarer === 'S');
        if (!nextIsUserTurn) {
          // Reset flag first to ensure useEffect triggers, then set it back to true
          setIsPlayingCard(false);
          setTimeout(() => setIsPlayingCard(true), 100);
        } else {
          setIsPlayingCard(false);
        }
      }

    } catch (err) {
      console.error('Error playing declarer card:', err);
      setError(err.message);
      setIsPlayingCard(false);
    }
  };

  const handleDummyCardPlay = async (card) => {
    console.log('🃏 handleDummyCardPlay called:', { card, isPlayingCard, playState: !!playState });

    if (!playState) {
      console.log('⚠️ Blocked: playState is null');
      return;
    }

    // If there's a pending trick clear, execute it immediately before user plays
    if (trickClearTimeoutRef.current) {
      console.log('⚡ User played (dummy) - clearing pending trick immediately');
      clearTimeout(trickClearTimeoutRef.current);
      trickClearTimeoutRef.current = null;

      // Clear the trick immediately
      await fetch(`${API_URL}/api/clear-trick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
      });

      // Fetch and update state after clearing
      const clearedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (clearedStateResponse.ok) {
        const clearedState = await clearedStateResponse.json();
        setPlayState(clearedState);
      }
    }

    try {
      console.log('✅ Playing dummy card:', card);
      setIsPlayingCard(true);

      // Dummy position (partner of declarer when South is declarer)
      const dummyPosition = playState.dummy;

      const response = await fetch(`${API_URL}/api/play-card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          position: dummyPosition,
          card: { rank: card.rank, suit: card.suit }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Illegal card play');
      }

      const data = await response.json();
      console.log('Dummy card played:', data);

      // Update dummy hand (remove played card)
      setDummyHand(prevHand => prevHand ? prevHand.filter(c =>
        !(c.rank === card.rank && c.suit === card.suit)
      ) : prevHand);

      // Fetch updated play state to show the card that was just played
      const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (updatedStateResponse.ok) {
        const updatedState = await updatedStateResponse.json();
        setPlayState(updatedState);
        console.log('🔄 Updated play state after dummy play:', {
          trick_size: updatedState.current_trick.length,
          current_trick: updatedState.current_trick
        });
      }

      // Check if trick just completed
      if (data.trick_complete && data.trick_winner) {
        // Trick is complete - show winner for 2.5 seconds before clearing
        console.log(`Trick complete! Winner: ${data.trick_winner}`);

        // Wait 2.5 seconds to display the winner (50% faster than before)
        await new Promise(resolve => {
          trickClearTimeoutRef.current = setTimeout(resolve, 2500);
        });

        // Clear timeout ref since we're about to clear
        trickClearTimeoutRef.current = null;

        // Clear the trick and get updated state
        await fetch(`${API_URL}/api/clear-trick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
        });

        // Fetch state after trick clear to see who's next
        const nextStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
        if (nextStateResponse.ok) {
          const nextState = await nextStateResponse.json();
          setPlayState(nextState);

          // Check if all 13 tricks are complete
          const totalTricks = Object.values(nextState.tricks_won).reduce((a, b) => a + b, 0);
          if (totalTricks === 13) {
            console.log('🏁 All 13 tricks complete after user card! Fetching final score...');
            // Play complete - calculate score
            const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
              body: JSON.stringify({ vulnerability: vulnerability })
            });

            if (scoreResponse.ok) {
              const scoreData = await scoreResponse.json();
              console.log('✅ Score calculated:', scoreData);
              setScoreData(scoreData);
            } else {
              const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
              console.error('❌ Failed to get score:', errorData);
              setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
            }

            setIsPlayingCard(false);
            return;
          }

          // Start AI loop only if it's not the user's turn
          const nextIsUserTurn = nextState.next_to_play === 'S' ||
                                (nextState.next_to_play === nextState.dummy && nextState.contract.declarer === 'S');
          if (!nextIsUserTurn) {
            // Reset flag first to ensure useEffect triggers, then set it back to true
            setIsPlayingCard(false);
            setTimeout(() => setIsPlayingCard(true), 100);
          } else {
            setIsPlayingCard(false);
          }
        }
      } else {
        // Trick not complete - check whose turn is next
        const updatedState = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } }).then(r => r.json());
        setPlayState(updatedState);

        const nextIsUserTurn = updatedState.next_to_play === 'S' ||
                              (updatedState.next_to_play === updatedState.dummy && updatedState.contract.declarer === 'S');
        if (!nextIsUserTurn) {
          // Reset flag first to ensure useEffect triggers, then set it back to true
          setIsPlayingCard(false);
          setTimeout(() => setIsPlayingCard(true), 100);
        } else {
          setIsPlayingCard(false);
        }
      }

    } catch (err) {
      console.error('Error playing dummy card:', err);
      setError(err.message);
      setIsPlayingCard(false);
    }
  };

  const handleCloseScore = async () => {
    // Always try to save the hand if we have score data
    if (scoreData) {
      try {
        console.log('💾 Attempting to save hand to session...');
        console.log('Current state:', {
          hasSessionData: !!sessionData,
          sessionActive: sessionData?.active,
          hasScoreData: !!scoreData
        });

        // Check current session status to ensure we have an active session
        const sessionStatusResponse = await fetch(`${API_URL}/api/session/status`, {
          headers: { ...getSessionHeaders() }
        });

        if (sessionStatusResponse.ok) {
          const currentSession = await sessionStatusResponse.json();
          console.log('Session status:', currentSession);

          if (currentSession.active) {
            // Save the hand to session_hands table
            const response = await fetch(`${API_URL}/api/session/complete-hand`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
              body: JSON.stringify({
                score_data: scoreData,
                auction_history: auction.map(a => a.bid)
              })
            });

            if (response.ok) {
              const result = await response.json();
              console.log('✅ Hand saved successfully to database');
              console.log('Session updated:', result.session);
              setSessionData({ active: true, session: result.session });

              if (result.session_complete) {
                setDisplayedMessage(`Session complete! Winner: ${result.winner}`);
              } else {
                // Update dealer and vulnerability for next hand
                setVulnerability(result.session.vulnerability);
              }
            } else {
              const errorText = await response.text();
              console.error('❌ Failed to save hand:', errorText);
            }
          } else {
            console.warn('⚠️ No active session - hand not saved. Starting new session...');
            // Try to start a new session
            const sessionResponse = await fetch(`${API_URL}/api/session/start`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
              body: JSON.stringify({ user_id: userId || 1, session_type: 'chicago' })
            });
            if (sessionResponse.ok) {
              const newSession = await sessionResponse.json();
              setSessionData(newSession);
              console.log('✅ New session started');
            }
          }
        } else {
          console.error('❌ Failed to check session status');
        }
      } catch (err) {
        console.error('❌ Error saving hand to session:', err);
      }
    } else {
      console.warn('⚠️ No score data available - cannot save hand');
    }

    setScoreData(null);
  };

  // ========== END CARD PLAY FUNCTIONS ==========

  const dealNewHand = async () => {
    try {
      const response = await fetch(`${API_URL}/api/deal-hands`, { headers: { ...getSessionHeaders() } });
      if (!response.ok) throw new Error("Failed to deal hands.");
      const data = await response.json();

      // FIX: Map abbreviated dealer names to full names
      const dealerMap = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
      const dealerFromBackend = data.dealer || 'North';
      const currentDealer = dealerMap[dealerFromBackend] || dealerFromBackend;

      const shouldAiBid = players.indexOf(currentDealer) !== 2; // Dealer is not South

      resetAuction(data, !shouldAiBid); // Pass correct skipInitialAiBidding value
      setIsInitializing(false); // Ensure we're not in initializing state for manual deals
    } catch (err) { setError("Could not connect to server to deal."); }
  };

  const playRandomHand = async () => {
    try {
      const response = await fetch(`${API_URL}/api/play-random-hand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
      });
      if (!response.ok) throw new Error("Failed to create random play hand.");
      const data = await response.json();

      // Set hand and vulnerability
      setHand(data.hand);
      setHandPoints(data.points);
      setVulnerability(data.vulnerability);

      // NEW: Set dealer from backend (Chicago rotation)
      if (data.dealer) {
        setDealer(data.dealer);
        console.log('🎲 Dealer for this hand:', data.dealer);
      }

      // Set the auction that was generated by AI (for reference)
      setAuction(data.auction || []);

      // Transition directly to play phase
      setGamePhase('playing');
      setShowHandsThisDeal(false);  // Hide all hands when transitioning to play
      setAllHands(null);  // Clear all hands data
      setDisplayedMessage(`Contract: ${data.contract}. The AI bid all 4 hands. Opening leader: ${data.opening_leader}`);

      // Fetch initial play state
      const stateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (stateResponse.ok) {
        const state = await stateResponse.json();
        setPlayState(state);

        // === BUG FIX: Use visible_hands from backend ===
        const declarerPos = state.contract.declarer;
        if (state.visible_hands && state.visible_hands[declarerPos]) {
          const declarerCards = state.visible_hands[declarerPos].cards || [];
          console.log('👁️ Setting declarer hand from visible_hands (playRandomHand):', {
            declarerPos,
            cardCount: declarerCards.length
          });
          setDeclarerHand(declarerCards);
        } else if (state.dummy === 'S') {
          // FALLBACK: Old method
          console.log('⚠️ visible_hands not available, falling back to /api/get-all-hands');
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            const declarerCards = handsData.hands[declarerPos]?.hand || [];
            setDeclarerHand(declarerCards);
          }
        }

        // === NEW FIX: Update South's hand from visible_hands ===
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || [];
          console.log('👁️ Updating South hand from visible_hands (playRandomHand):', {
            cardCount: southCards.length,
            visible_hands_keys: Object.keys(state.visible_hands)
          });
          setHand(southCards);
        }
      }

      // CRITICAL FIX: Use setTimeout to ensure gamePhase updates BEFORE triggering AI loop
      // Same fix as in startPlay() - prevents race condition
      setTimeout(() => {
        console.log('🎬 Triggering AI play loop after game phase transition (random hand)');
        setIsPlayingCard(true);
      }, 50);
      setIsInitializing(false);
    } catch (err) {
      setError("Could not create random play hand.");
      console.error(err);
    }
  };

  const replayCurrentHand = async () => {
    // Replay the same hand - used after play completes
    if (!playState) return;

    try {
      // Restart play with the same contract
      const response = await fetch(`${API_URL}/api/start-play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          auction_history: auction.map(a => a.bid),
          vulnerability: vulnerability,
          replay: true  // Signal backend to use preserved original_deal
        })
      });

      if (!response.ok) throw new Error("Failed to restart play phase");

      const data = await response.json();

      // Fetch initial play state before transitioning
      const stateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (stateResponse.ok) {
        const state = await stateResponse.json();
        setPlayState(state);

        // === BUG FIX: Use visible_hands from backend ===
        const declarerPos = state.contract.declarer;
        if (state.visible_hands && state.visible_hands[declarerPos]) {
          const declarerCards = state.visible_hands[declarerPos].cards || [];
          console.log('👁️ Setting declarer hand from visible_hands (replayCurrentHand):', {
            declarerPos,
            cardCount: declarerCards.length
          });
          setDeclarerHand(declarerCards);
        } else if (state.dummy === 'S') {
          // FALLBACK: Old method
          console.log('⚠️ visible_hands not available, falling back to /api/get-all-hands');
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            const declarerCards = handsData.hands[declarerPos]?.hand || [];
            setDeclarerHand(declarerCards);
          }
        }

        // === NEW FIX: Update South's hand from visible_hands ===
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || [];
          console.log('👁️ Updating South hand from visible_hands (replayCurrentHand):', {
            cardCount: southCards.length,
            visible_hands_keys: Object.keys(state.visible_hands)
          });
          setHand(southCards);
        }
      }

      // Reset to play phase start
      setGamePhase('playing');
      setShowHandsThisDeal(false);  // Hide all hands when replaying
      setAllHands(null);  // Clear all hands data
      setScoreData(null);
      setDisplayedMessage(`Contract: ${data.contract}. Opening leader: ${data.opening_leader}`);

      // Restart hand (fetch from backend to get fresh hands)
      const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
      if (handsResponse.ok) {
        const handsData = await handsResponse.json();
        setHand(handsData.hands.S?.hand || []);
      }

      // CRITICAL FIX: Use setTimeout to ensure gamePhase updates BEFORE triggering AI loop
      // Same fix as in startPlay() and playRandomHand() - prevents race condition
      setTimeout(() => {
        console.log('🎬 Triggering AI play loop after game phase transition (replay)');
        setIsPlayingCard(true);
      }, 50);
    } catch (err) {
      setError('Failed to replay hand');
      console.error(err);
    }
  };
  
  const handleLoadScenario = async () => {
    if (!selectedScenario) return;
    try {
      const response = await fetch(`${API_URL}/api/load-scenario`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({ name: selectedScenario })
      });
      if (!response.ok) throw new Error("Failed to load scenario.");
      const data = await response.json();
      resetAuction(data, true); // Skip initial AI bidding - wait for proper turn
      setIsInitializing(false); // Ensure we're not in initializing state for scenario loads
    } catch (err) { setError("Could not load scenario from server."); }
  };

  const handleReplayHand = () => {
    if (!initialDeal) return;
    resetAuction(initialDeal, true); // Skip initial AI bidding - wait for proper turn
  };
  
  useEffect(() => {
    const fetchScenariosAndDeal = async () => {
      try {
        const response = await fetch(`${API_URL}/api/scenarios`, { headers: { ...getSessionHeaders() } });
        const data = await response.json();
        setScenarioList(data.scenarios);
        setScenariosByLevel(data.scenarios_by_level);
        if (data.scenarios.length > 0) setSelectedScenario(data.scenarios[0]);
      } catch (err) { console.error("Could not fetch scenarios", err); }

      // Start or resume session
      try {
        const sessionResponse = await fetch(`${API_URL}/api/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
          body: JSON.stringify({ user_id: 1, session_type: 'chicago' })
        });
        const sessionData = await sessionResponse.json();
        setSessionData(sessionData);

        // Use dealer and vulnerability from session
        const sessionDealer = sessionData.session.dealer;
        const sessionVuln = sessionData.session.vulnerability;
        setVulnerability(sessionVuln);

        console.log(`Session ${sessionData.resumed ? 'resumed' : 'started'}: ${sessionData.message}`);
      } catch (err) {
        console.error("Could not start session", err);
      }

      // Deal initial hand
      try {
        const response = await fetch(`${API_URL}/api/deal-hands`, { headers: { ...getSessionHeaders() } });
        if (!response.ok) throw new Error("Failed to deal hands.");
        const data = await response.json();

        // FIX: Map abbreviated dealer names and calculate if AI should bid
        const dealerMap = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
        const dealerFromBackend = data.dealer || 'North';
        const currentDealer = dealerMap[dealerFromBackend] || dealerFromBackend;
        const shouldAiBid = players.indexOf(currentDealer) !== 2; // Dealer is not South

        // Reset auction with correct skipInitialAiBidding value
        resetAuction(data, !shouldAiBid);

        // System is now ready - wait a bit for state to settle
        setTimeout(() => {
          setIsInitializing(false);
        }, 200);
      } catch (err) {
        setError("Could not connect to server to deal.");
        setIsInitializing(false);
      }
    };
    fetchScenariosAndDeal();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Helper function to calculate whose turn it is based on dealer and auction length
  const calculateExpectedBidder = (currentDealer, auctionLength) => {
    const dealerIndex = players.indexOf(currentDealer);
    if (dealerIndex === -1) {
      console.error('❌ Invalid dealer for turn calculation:', currentDealer);
      return 'North'; // Fallback
    }
    return players[(dealerIndex + auctionLength) % 4];
  };

  const handleUserBid = async (bid) => {
    // CRITICAL VALIDATION: Check if it's actually South's turn based on dealer rotation
    const expectedBidder = calculateExpectedBidder(dealer, auction.length);
    if (expectedBidder !== 'South') {
      const errorMsg = `⚠️ Not your turn! Waiting for ${expectedBidder} to bid.`;
      setError(errorMsg);
      setDisplayedMessage(errorMsg);
      console.warn('🚫 User tried to bid out of turn:', {
        dealer,
        auctionLength: auction.length,
        expectedBidder,
        nextPlayerIndex,
        players
      });
      return;
    }

    // Clear any previous errors
    setError('');

    if (players[nextPlayerIndex] !== 'South' || isAiBidding) return;

    // DEBUG: Log bid submission
    console.log('🎯 SUBMITTING USER BID:', {
      bid: bid,
      userId: userId,
      auctionLength: auction.length,
      timestamp: new Date().toISOString()
    });

    setDisplayedMessage('...');
    const newAuction = [...auction, { bid: bid, explanation: 'Your bid.', player: 'South' }];

    // CRITICAL FIX: Use flushSync to force immediate render before AI bidding starts
    // This ensures user's bid appears in the table before subsequent AI bids
    flushSync(() => {
      setAuction(newAuction);
    });

    // Enable AI bidding after user's bid is rendered
    setIsAiBidding(true);

    try {
      // Call evaluate-bid endpoint which stores decision in database for dashboard analytics
      const feedbackResponse = await fetch(`${API_URL}/api/evaluate-bid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          user_bid: bid,
          auction_history: auction.map(a => a.bid), // Auction BEFORE user's bid
          current_player: 'South',
          user_id: userId || 1,
          session_id: sessionData?.session?.session_id,
          feedback_level: 'intermediate'
        })
      });
      const feedbackData = await feedbackResponse.json();

      // DEBUG: Log response from evaluate-bid
      console.log('✅ EVALUATE-BID RESPONSE:', {
        user_bid: bid,
        feedback: feedbackData,
        stored: feedbackData.decision_id ? 'YES' : 'UNKNOWN'
      });

      setDisplayedMessage(feedbackData.user_message || feedbackData.explanation || 'Bid recorded.');
    } catch (err) {
      console.error('❌ Error evaluating bid:', err);
      setDisplayedMessage('Could not get feedback from the server.');
    }
    // NOTE: nextPlayerIndex is now derived - no need to manually increment
    // NOTE: setIsAiBidding(true) is called BEFORE the fetch (see above) to ensure proper state batching
  };
  
  const handleBidClick = (bidObject) => { setDisplayedMessage(`[${bidObject.bid}] ${bidObject.explanation}`); };
  
  useEffect(() => {
    console.log('🤖 AI BIDDING USEEFFECT TRIGGERED:', {
      isInitializing,
      isAiBidding,
      auctionLength: auction.length,
      dealer,
      gamePhase
    });

    // Don't start AI bidding during initialization
    if (isInitializing) {
      console.log('⏸️ AI bidding blocked: isInitializing = true');
      return;
    }

    // Check if auction is over
    if (isAuctionOver(auction)) {
      console.log('🏁 Auction is over');
      if (isAiBidding) {
        setIsAiBidding(false);
      }
      return;
    }

    // Determine whose turn it is
    const currentPlayer = calculateExpectedBidder(dealer, auction.length);
    console.log('👤 Current player calculated:', currentPlayer);

    // If it's South's turn, stop AI bidding
    if (currentPlayer === 'South') {
      console.log('👤 South\'s turn - stopping AI bidding');
      if (isAiBidding) {
        setIsAiBidding(false);
      }
      return; // Don't make AI bid for South
    }

    // It's an AI player's turn (North/East/West)
    console.log('🤖 AI player turn:', currentPlayer, '| isAiBidding:', isAiBidding);

    // If AI bidding is enabled, make the bid
    if (isAiBidding) {
      // Prevent concurrent AI bids using a ref guard
      if (isAiBiddingInProgress.current) {
        console.log('⏸️ AI bid already in progress - skipping');
        return;
      }

      console.log('✅ Starting AI turn for:', currentPlayer);

      const runAiTurn = async () => {
        isAiBiddingInProgress.current = true;
        console.log('⏱️ Waiting 500ms before AI bid...');

        await new Promise(resolve => setTimeout(resolve, 500));
        try {
          // Calculate current player from auction length and dealer
          const currentPlayer = calculateExpectedBidder(dealer, auction.length);
          console.log('🎯 AI making bid for:', currentPlayer);

          // Double-check it's not South's turn
          if (currentPlayer === 'South') {
            console.log('❌ Safety check failed - South\'s turn detected');
            setIsAiBidding(false);
            isAiBiddingInProgress.current = false;
            return;
          }

          console.log('📡 Fetching AI bid from server...');
          const response = await fetch(`${API_URL}/api/get-next-bid`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
            body: JSON.stringify({
              auction_history: auction.map(a => a.bid),
              current_player: currentPlayer
            })
          });
          if (!response.ok) throw new Error("AI failed to get bid.");
          const data = await response.json();
          console.log('✅ AI bid received:', data);

          // CRITICAL: Release guard BEFORE updating auction
          // This prevents race condition where flushSync triggers useEffect before guard is released
          isAiBiddingInProgress.current = false;
          console.log('🔓 AI bid guard released (before auction update)');

          // Update auction with flushSync to force immediate render
          // This ensures each AI bid appears before the next one starts
          flushSync(() => {
            setAuction(prevAuction => [...prevAuction, data]);
          });
          console.log('✅ Auction updated with AI bid');
        } catch (err) {
          console.error('❌ AI bidding error:', err);
          setError("AI bidding failed. Is the server running?");
          setIsAiBidding(false);
          // Release guard on error
          isAiBiddingInProgress.current = false;
          console.log('🔓 AI bid guard released (error path)');
        }
      };
      runAiTurn();
    } else {
      console.log('❌ AI bidding NOT enabled for', currentPlayer, '- waiting for isAiBidding to be true');
    }
    // Note: If isAiBidding is false but it's an AI player's turn, we do nothing
    // This allows the user or other code to manually trigger AI bidding by calling setIsAiBidding(true)
  }, [auction, nextPlayerIndex, isAiBidding, players, isInitializing, dealer, calculateExpectedBidder]);

  // Trigger AI bidding after initialization completes (if dealer is not South)
  // Uses ref to prevent duplicate triggers and avoid infinite loops
  useEffect(() => {
    if (!isInitializing && gamePhase === 'bidding' && auction.length === 0 && !hasTriggeredInitialBid.current) {
      const currentPlayer = players[nextPlayerIndex];
      console.log('🎬 Post-initialization check:', {
        isInitializing,
        currentPlayer,
        nextPlayerIndex,
        shouldStartAI: currentPlayer !== 'South',
        hasTriggered: hasTriggeredInitialBid.current
      });

      // Only start AI if it's not South's turn
      if (currentPlayer !== 'South') {
        console.log('▶️ Starting AI bidding after initialization');
        hasTriggeredInitialBid.current = true;  // Set ref BEFORE state to prevent race
        setIsAiBidding(true);
      }
    }
  }, [isInitializing, gamePhase, auction.length, players, nextPlayerIndex]);

  // AI play loop - runs during play phase
  useEffect(() => {
    console.log('🔄 AI play loop useEffect triggered:', {
      gamePhase,
      isPlayingCard,
      timestamp: new Date().toISOString()
    });

    if (gamePhase !== 'playing' || !isPlayingCard) {
      console.log('⏭️ AI play loop skipped - conditions not met:', {
        gamePhase,
        expectedGamePhase: 'playing',
        gamePhaseMismatch: gamePhase !== 'playing',
        isPlayingCard,
        reason: gamePhase !== 'playing' ? 'gamePhase not "playing"' : 'isPlayingCard is false'
      });
      return;
    }

    const runAiPlay = async () => {
      try {
        console.log('🎬 AI play loop RUNNING...');
        // Get current play state
        const stateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
        if (!stateResponse.ok) throw new Error("Failed to get play state");

        const state = await stateResponse.json();
        console.log('🎮 Play State:', {
          next_to_play: state.next_to_play,
          dummy: state.dummy,
          declarer: state.contract.declarer,
          trick_size: state.current_trick.length,
          current_trick_data: state.current_trick
        });
        setPlayState(state);

        // Update dummy hand if revealed (always update to reflect cards played)
        if (state.dummy_hand) {
          // Backend returns dummy_hand as { cards: [...], position: "N" }
          // Extract just the cards array
          const dummyCards = state.dummy_hand.cards || state.dummy_hand;
          console.log('🃏 Setting dummy hand:', {
            dummy_position: state.dummy,
            declarer: state.contract.declarer,
            dummy_cards_count: dummyCards?.length,
            dummy_hand_structure: state.dummy_hand
          });
          setDummyHand(dummyCards);
        }

        // Determine if user is dummy and related positions
        const userIsDummy = state.dummy === 'S';
        const declarerPos = state.contract.declarer;
        const nextPlayer = state.next_to_play;

        // === BUG FIX: Use visible_hands from backend to populate declarer hand ===
        // Backend's BridgeRulesEngine already determines which hands should be visible
        // Use this data instead of making a separate API call
        if (state.visible_hands && state.visible_hands[declarerPos]) {
          const visibleDeclarerCards = state.visible_hands[declarerPos].cards || [];
          console.log('👁️ Setting declarer hand from visible_hands:', {
            declarerPos,
            cardCount: visibleDeclarerCards.length,
            userIsDummy,
            visible_hands_keys: Object.keys(state.visible_hands)
          });
          setDeclarerHand(visibleDeclarerCards);
        } else if (userIsDummy && !declarerHand) {
          // FALLBACK: If visible_hands is not available (old API), fetch separately
          // This maintains backward compatibility but should not be needed
          console.log('⚠️ visible_hands not available, falling back to /api/get-all-hands');
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            const fetchedDeclarerHand = handsData.hands[declarerPos]?.hand || [];
            console.log('✅ Declarer hand fetched in AI loop (fallback):', {
              position: declarerPos,
              cardCount: fetchedDeclarerHand.length
            });
            setDeclarerHand(fetchedDeclarerHand);
          }
        }

        // === NEW FIX: Update South's hand from visible_hands ===
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || [];
          console.log('👁️ Updating South hand from visible_hands (AI loop):', {
            cardCount: southCards.length,
            visible_hands_keys: Object.keys(state.visible_hands)
          });
          setHand(southCards);
        }

        // Check if play is complete (13 tricks)
        const totalTricks = Object.values(state.tricks_won).reduce((a, b) => a + b, 0);
        if (totalTricks === 13) {
          console.log('🏁 All 13 tricks complete! Fetching final score...');
          // Play complete - calculate score
          const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
            body: JSON.stringify({ vulnerability: vulnerability })
          });

          if (scoreResponse.ok) {
            const scoreData = await scoreResponse.json();
            console.log('✅ Score calculated:', scoreData);
            setScoreData(scoreData);
          } else {
            // Handle error response
            const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
            console.error('❌ Failed to get score:', errorData);
            setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
          }

          setIsPlayingCard(false);
          return;
        }

        // Determine if user is declarer
        const userIsDeclarer = declarerPos === 'S';

        console.log('🤔 Turn check:', {
          nextPlayer,
          userIsDummy,
          userIsDeclarer,
          dummy: state.dummy,
          declarerPos
        });

        // ============================================================
        // CRITICAL: Determine who controls the next play (SINGLE-PLAYER MODE)
        // Single-Player Rules:
        // - User controls South ALWAYS
        // - User controls North when NS is declaring (N or S is declarer)
        // - AI controls East + West ALWAYS
        // - AI controls North when EW is declaring (E or W is declarer)
        // ============================================================

        // Check if user should control the next play
        let userShouldControl = false;
        let userControlMessage = "";

        const nsIsDeclaring = (declarerPos === 'N' || declarerPos === 'S');

        // SINGLE-PLAYER LOGIC: User controls NS when NS is declaring
        if (nsIsDeclaring) {
          // User controls BOTH North and South when NS is declaring
          if (nextPlayer === 'S') {
            userShouldControl = true;
            userControlMessage = "Your turn to play from South!";
          } else if (nextPlayer === 'N') {
            userShouldControl = true;
            userControlMessage = "Your turn to play from North (partner)!";
          }
          // If nextPlayer is E or W, AI plays
        } else {
          // EW is declaring - user controls only South (defense)
          if (nextPlayer === 'S') {
            userShouldControl = true;
            userControlMessage = "Your turn to play (defending)!";
          }
          // If nextPlayer is N, E, or W, AI plays
        }

        // DEFENSIVE CHECK: If user should control this play, stop AI loop
        // This prevents calling /api/get-ai-play for user-controlled positions
        // Backend also validates as a safeguard (returns 403 if this check is bypassed)
        if (userShouldControl) {
          console.log('⏸️ STOPPING - User controls this play:', {
            nextPlayer,
            userIsDeclarer,
            userIsDummy,
            dummy: state.dummy,
            message: userControlMessage
          });
          // Clear any pending timeout to prevent it from restarting the loop
          if (aiPlayTimeoutRef.current) {
            clearTimeout(aiPlayTimeoutRef.current);
            aiPlayTimeoutRef.current = null;
          }
          setIsPlayingCard(false);
          setDisplayedMessage(userControlMessage);
          return;
        }

        // Log what AI is doing
        console.log(`▶️ AI playing for position ${nextPlayer}`);
        // AI player's turn
        await new Promise(resolve => setTimeout(resolve, 1000)); // Delay for visibility

        const playResponse = await fetch(`${API_URL}/api/get-ai-play`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
          body: JSON.stringify({ position: nextPlayer })
        });

        if (!playResponse.ok) {
          const responseData = await playResponse.json().catch(() => ({ error: 'Unknown error' }));

          // 403 means user controls this position - this is a defensive safeguard, not an error
          // Frontend should have already detected user control, but backend validates as well
          if (playResponse.status === 403) {
            console.log(`✋ User turn detected by backend: ${nextPlayer} is controlled by user`, {
              position: nextPlayer,
              controllablePositions: responseData.controllable_positions,
              userRole: responseData.user_role,
              message: responseData.message || responseData.reason
            });
            setIsPlayingCard(false);

            // Set user-friendly turn message
            const turnMsg = nextPlayer === 'S'
              ? "Your turn (South)"
              : nextPlayer === 'N' && (declarerPos === 'N' || declarerPos === 'S')
              ? `Your turn (${responseData.user_role === 'dummy' ? 'Dummy' : 'North'})`
              : `Your turn to play from ${nextPlayer}`;
            setDisplayedMessage(turnMsg);
            return; // Exit gracefully without throwing error
          }

          // Other errors are real problems
          console.error('❌ AI play failed:', {
            status: playResponse.status,
            statusText: playResponse.statusText,
            errorData: responseData,
            position: nextPlayer,
            playState: state
          });
          throw new Error(`AI play failed for ${nextPlayer}: ${responseData.error || playResponse.statusText}`);
        }

        const playData = await playResponse.json();
        console.log('AI played:', playData);

        // Fetch updated play state to show the card that was just played
        const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
        if (updatedStateResponse.ok) {
          const updatedState = await updatedStateResponse.json();
          setPlayState(updatedState);
          console.log('🔄 Updated play state after AI play:', {
            trick_size: updatedState.current_trick.length,
            current_trick: updatedState.current_trick
          });
        }

        // Check if trick just completed
        if (playData.trick_complete && playData.trick_winner) {
          // Trick is complete - show winner for 2.5 seconds before clearing
          console.log(`Trick complete! Winner: ${playData.trick_winner}`);

          // Wait 2.5 seconds to display the winner (50% faster than before)
          await new Promise(resolve => {
            trickClearTimeoutRef.current = setTimeout(resolve, 2500);
          });

          // Clear timeout ref since we're about to clear
          trickClearTimeoutRef.current = null;

          // Clear the trick
          await fetch(`${API_URL}/api/clear-trick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
          });

          // Fetch updated play state to show empty trick
          const clearedStateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
          if (clearedStateResponse.ok) {
            const clearedState = await clearedStateResponse.json();
            setPlayState(clearedState);
            console.log('🧹 Trick cleared, updated state:', {
              trick_size: clearedState.current_trick.length,
              next_to_play: clearedState.next_to_play
            });

            // CRITICAL CHECK: See if all 13 tricks are complete (MUST check AFTER trick clear)
            const totalTricksAfterClear = Object.values(clearedState.tricks_won).reduce((a, b) => a + b, 0);
            if (totalTricksAfterClear === 13) {
              console.log('🏁 All 13 tricks complete after AI play! Fetching final score...');
              // Play complete - calculate score
              const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
                body: JSON.stringify({ vulnerability: vulnerability })
              });

              if (scoreResponse.ok) {
                const scoreData = await scoreResponse.json();
                console.log('✅ Score calculated after AI play:', scoreData);
                setScoreData(scoreData);
              } else {
                const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
                console.error('❌ Failed to get score after AI play:', errorData);
                setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
              }

              setIsPlayingCard(false);
              return;
            }

            // CRITICAL FIX: Check if next player is user-controlled before restarting AI loop
            const nextIsUserControlled = clearedState.next_to_play === 'S' ||
              (clearedState.next_to_play === clearedState.dummy && clearedState.contract.declarer === 'S');

            if (nextIsUserControlled) {
              console.log('⏸️ STOPPING - Next player after trick clear is user-controlled');
              setIsPlayingCard(false);
              return;
            }
          }

          console.log('🔁 Continuing to next trick...');
          // Continue to next trick after small delay
          // Reset flag first to ensure useEffect triggers
          setIsPlayingCard(false);
          aiPlayTimeoutRef.current = setTimeout(() => setIsPlayingCard(true), 100);
        } else {
          console.log('🔁 Continuing AI play loop (trick not complete)...');
          // Trick not complete - continue playing quickly
          // Reset flag first to ensure useEffect triggers
          setIsPlayingCard(false);
          aiPlayTimeoutRef.current = setTimeout(() => setIsPlayingCard(true), 100);
        }

      } catch (err) {
        console.error('Error in AI play loop:', err);
        setError(`AI play failed: ${err.message || 'Unknown error'}`);
        setIsPlayingCard(false);
      }
    };

    runAiPlay();
  }, [gamePhase, isPlayingCard, vulnerability]);

  // CRITICAL FIX: Only show all hands during bidding phase, not during play
  // When alwaysShowHands is true, it should only apply to bidding, not card play
  const shouldShowHands = gamePhase === 'bidding' && (showHandsThisDeal || alwaysShowHands);

  // Debug logging for card display
  useEffect(() => {
    console.log('🎨 Render state:', {
      shouldShowHands,
      showHandsThisDeal,
      alwaysShowHands,
      allHandsExists: !!allHands,
      allHandsKeys: allHands ? Object.keys(allHands) : null,
      northHand: allHands?.North?.hand?.length || 0,
      eastHand: allHands?.East?.hand?.length || 0,
      southHand: allHands?.South?.hand?.length || 0,
      westHand: allHands?.West?.hand?.length || 0,
      // Detailed structure check
      northStructure: allHands?.North ? Object.keys(allHands.North) : null,
      firstNorthCard: allHands?.North?.hand?.[0]
    });
  }, [shouldShowHands, showHandsThisDeal, alwaysShowHands, allHands]);

  // User menu component
  const UserMenu = () => {
    if (!isAuthenticated) {
      return (
        <button onClick={() => setShowLogin(true)} className="auth-button" data-testid="sign-in-button">
          Sign In
        </button>
      );
    }

    return (
      <div className="user-menu" data-testid="user-menu">
        <span className="user-display" data-testid="user-display-name">👤 {user.display_name}</span>
        <button onClick={logout} className="logout-button" data-testid="logout-button">Logout</button>
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* User Menu in top right */}
      <div className="top-bar">
        <h1 className="app-title">Bridge Bidding Practice</h1>
        <UserMenu />
      </div>

      {/* Login Modal */}
      {showLogin && <SimpleLogin onClose={() => setShowLogin(false)} />}

      {/* Session Score Panel */}
      <SessionScorePanel sessionData={sessionData} />

      {shouldShowHands && allHands ? (
        <div className="table-layout">
          <div className="table-center">
            <PlayerHand position="North" hand={allHands.North?.hand} points={allHands.North?.points} vulnerability={vulnerability} />
          </div>
          <div className="table-middle">
            <div className="table-west">
              <PlayerHand position="West" hand={allHands.West?.hand} points={allHands.West?.points} vulnerability={vulnerability} />
            </div>
            <div className="table-center-content">
              <div className="bidding-area">
                <h2>Bidding</h2>
                {/* Turn indicator - Shows whose turn it is */}
                {isAiBidding && players[nextPlayerIndex] !== 'South' && !isAuctionOver(auction) && (
                  <div className="turn-message">
                    ⏳ Waiting for {players[nextPlayerIndex]} to bid...
                  </div>
                )}
                {!isAiBidding && players[nextPlayerIndex] === 'South' && !isAuctionOver(auction) && (
                  <div className="turn-message your-turn">
                    ✅ Your turn to bid!
                  </div>
                )}
                <BiddingTable auction={auction} players={players} dealer={dealer} nextPlayerIndex={nextPlayerIndex} onBidClick={handleBidClick} />
                {displayedMessage && <div className="feedback-panel">{displayedMessage}</div>}
                {error && <div className="error-message">{error}</div>}
              </div>
            </div>
            <div className="table-east">
              <PlayerHand position="East" hand={allHands.East?.hand} points={allHands.East?.points} vulnerability={vulnerability} />
            </div>
          </div>
          <div className="table-bottom">
            <PlayerHand position="South" hand={allHands.South?.hand} points={allHands.South?.points} vulnerability={vulnerability} />
          </div>
        </div>
      ) : gamePhase === 'bidding' ? (
        <div className="top-panel">
          <div className="my-hand">
            <h2>Your Hand (South)</h2>
            <div className="hand-display">
              {hand && hand.length > 0 ? getSuitOrder(null).map(suit => ( <div key={suit} className="suit-group">{hand.filter(card => card.suit === suit).map((card, index) => ( <BridgeCard key={`${suit}-${index}`} rank={card.rank} suit={card.suit} />))}</div>)) : <p>{isInitializing ? 'System Initiating...' : 'Dealing...'}</p>}
            </div>
            <HandAnalysis points={handPoints} vulnerability={vulnerability} />
          </div>
        </div>
      ) : null}

      {!shouldShowHands && gamePhase === 'bidding' && (
        <div className="bidding-area">
          <h2>Bidding</h2>
          {/* Turn indicator - Shows whose turn it is */}
          {isAiBidding && players[nextPlayerIndex] !== 'South' && !isAuctionOver(auction) && (
            <div className="turn-message">
              ⏳ Waiting for {players[nextPlayerIndex]} to bid...
            </div>
          )}
          {!isAiBidding && players[nextPlayerIndex] === 'South' && !isAuctionOver(auction) && (
            <div className="turn-message your-turn">
              ✅ Your turn to bid!
            </div>
          )}
          <BiddingTable auction={auction} players={players} dealer={dealer} nextPlayerIndex={nextPlayerIndex} onBidClick={handleBidClick} />
          {displayedMessage && <div className="feedback-panel">{displayedMessage}</div>}
          {error && <div className="error-message">{error}</div>}
        </div>
      )}

      {!shouldShowHands && gamePhase === 'playing' && playState && (
        <div className="play-phase">
          {/* DEBUG INDICATOR: Shows AI loop state - Only show during active play, not after completion - Less prominent for testing only */}
          {Object.values(playState.tricks_won).reduce((a, b) => a + b, 0) < 13 && (
            <div style={{
              position: 'fixed',
              top: '10px',
              right: '10px',
              background: isPlayingCard ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)',
              color: '#666',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 'normal',
              zIndex: 9999,
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              border: '1px solid rgba(0,0,0,0.1)'
            }}>
              AI: {isPlayingCard ? '▶' : '⏸'}
            </div>
          )}
          {console.log('🎯 PlayTable render:', {
            next_to_play: playState.next_to_play,
            isPlayingCard: isPlayingCard,
            dummy: playState.dummy,
            declarer: playState.contract.declarer,
            userIsDeclarer: playState.contract.declarer === 'S',
            dummy_hand_in_state: playState.dummy_hand?.cards?.length || playState.dummy_hand?.length || 0,
            dummy_revealed: playState.dummy_revealed,
            isUserTurn_OLD: playState.next_to_play === 'S' && playState.dummy !== 'S',
            isUserTurn_NEW: (playState.next_to_play === 'S' && playState.dummy !== 'S') || (playState.next_to_play === playState.dummy && playState.contract.declarer === 'S') || (playState.next_to_play === playState.contract.declarer && playState.dummy === 'S'),
            isDeclarerTurn: playState.next_to_play === playState.contract.declarer && playState.dummy === 'S',
            isDummyTurn: playState.next_to_play === playState.dummy && playState.contract.declarer === 'S'
          })}
          <PlayTable
            playState={playState}
            userHand={hand}
            dummyHand={playState.dummy_hand?.cards || playState.dummy_hand || dummyHand}
            declarerHand={declarerHand}
            onCardPlay={handleCardPlay}
            onDeclarerCardPlay={handleDeclarerCardPlay}
            onDummyCardPlay={handleDummyCardPlay}
            // === BRIDGE RULES ENGINE INTEGRATION ===
            // Use rules engine data from backend for correct hand visibility and control
            isUserTurn={playState.is_user_turn ?? (playState.next_to_play === 'S' && playState.dummy !== 'S')}
            isDeclarerTurn={
              (playState.controllable_positions?.includes(playState.contract.declarer) && playState.next_to_play === playState.contract.declarer)
              ?? (playState.next_to_play === playState.contract.declarer && playState.dummy === 'S')
            }
            isDummyTurn={
              (playState.controllable_positions?.includes(playState.dummy) && playState.next_to_play === playState.dummy)
              ?? (playState.next_to_play === playState.dummy && playState.contract.declarer === 'S')
            }
            auction={auction}
            scoreData={scoreData}
          />
          {/* Don't show AI bidding status messages during play - only show errors if they occur */}
          {Object.values(playState.tricks_won).reduce((a, b) => a + b, 0) < 13 && error && <div className="error-message">{error}</div>}

          {/* Show All Hands button for play phase - available after hand is complete */}
          {Object.values(playState.tricks_won).reduce((a, b) => a + b, 0) === 13 && (
            <div className="show-hands-controls" style={{ marginTop: '20px' }}>
              <button onClick={handleShowHandsThisDeal}>
                {showHandsThisDeal ? 'Hide All Hands' : 'Show All Hands'}
              </button>
            </div>
          )}
        </div>
      )}

      <div className="action-area">
        {gamePhase === 'bidding' && (
          <BiddingBoxComponent onBid={handleUserBid} disabled={players[nextPlayerIndex] !== 'South' || isAiBidding} auction={auction} />
        )}
        <div className="controls-section">
          {/* Game controls - Context-aware based on game phase */}
          <div className="game-controls">
            {gamePhase === 'bidding' ? (
              <>
                <button className="deal-button" data-testid="deal-button" onClick={dealNewHand}>Deal Hand to Bid</button>
                <button className="play-button" data-testid="play-random-button" onClick={playRandomHand}>Play Random Hand</button>
                <button className="replay-button" data-testid="replay-button" onClick={handleReplayHand} disabled={!initialDeal || auction.length === 0}>Rebid Hand</button>
                {/* Show "Play This Hand" button when bidding is complete */}
                {auction.length >= 4 && auction.slice(-3).every(bid => bid.bid === 'Pass') && (
                  <button className="play-this-hand-button" data-testid="play-this-hand-button" onClick={startPlayPhase}>
                    ▶ Play This Hand
                  </button>
                )}
              </>
            ) : (
              <>
                <button className="play-button" data-testid="play-another-hand-button" onClick={playRandomHand}>Play Another Hand</button>
                <button className="replay-button" data-testid="replay-hand-button" onClick={replayCurrentHand}>Replay Hand</button>
                <button className="deal-button" data-testid="bid-new-hand-button" onClick={dealNewHand}>Bid New Hand</button>
                <button className="learning-dashboard-button" data-testid="dashboard-button" onClick={() => setShowLearningDashboard(true)}>📊 My Progress</button>
              </>
            )}
          </div>

          {/* AI Difficulty Selector - Only visible during gameplay */}
          {gamePhase === 'playing' && (
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <AIDifficultySelector
                onDifficultyChange={(difficulty, data) => {
                  console.log('AI difficulty changed to:', difficulty, data);
                }}
              />
              <button
                onClick={() => setShowReviewModal(true)}
                className="ai-review-button"
                style={{ whiteSpace: 'nowrap' }}
              >
                🤖 Request AI Review
              </button>
            </div>
          )}

          {/* Scenario loader - Only visible during bidding */}
          {gamePhase === 'bidding' && (
            <div className="scenario-loader">
              <select value={selectedScenario} onChange={(e) => setSelectedScenario(e.target.value)}>
                {scenariosByLevel ? (
                  <>
                    <optgroup label="Essential Conventions">
                      {scenariosByLevel.Essential?.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                    </optgroup>
                    <optgroup label="Intermediate Conventions">
                      {scenariosByLevel.Intermediate?.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                    </optgroup>
                    <optgroup label="Advanced Conventions">
                      {scenariosByLevel.Advanced?.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                    </optgroup>
                  </>
                ) : (
                  <option>Loading...</option>
                )}
              </select>
              <button onClick={handleLoadScenario}>Practice Convention</button>
            </div>
          )}
        </div>
        {/* Only show bidding-specific controls during bidding phase */}
        {gamePhase === 'bidding' && (
          <>
            <div className="show-hands-controls">
              <button onClick={handleShowHandsThisDeal}>{showHandsThisDeal ? 'Hide Hands (This Deal)' : 'Show Hands (This Deal)'}</button>
              <button onClick={handleToggleAlwaysShowHands} className={alwaysShowHands ? 'active' : ''}>{alwaysShowHands ? 'Always Show: ON' : 'Always Show: OFF'}</button>
            </div>
            <div className="ai-review-controls">
              <button onClick={handleShowConventionHelp} className="help-button" data-testid="convention-help-button">ℹ️ Convention Help</button>
              <button onClick={() => setShowReviewModal(true)} className="ai-review-button" data-testid="ai-review-button">🤖 Request AI Review</button>
              <button onClick={() => setShowLearningDashboard(true)} className="learning-dashboard-button" data-testid="progress-button">📊 My Progress</button>
            </div>
          </>
        )}
      </div>

      <ReviewModal
        isOpen={showReviewModal}
        onClose={handleCloseReviewModal}
        onSubmit={handleRequestReview}
        userConcern={userConcern}
        setUserConcern={setUserConcern}
        reviewPrompt={reviewPrompt}
        reviewFilename={reviewFilename}
        gamePhase={gamePhase}
        onCopyPrompt={handleCopyPrompt}
      />

      <ConventionHelpModal
        isOpen={showConventionHelp}
        onClose={handleCloseConventionHelp}
        conventionInfo={conventionInfo}
      />

      {scoreData && (
        <ScoreDisplay
          scoreData={scoreData}
          onClose={handleCloseScore}
          onDealNewHand={dealNewHand}
          sessionData={sessionData}
          onShowLearningDashboard={() => setShowLearningDashboard(true)}
          onPlayAnotherHand={playRandomHand}
          onReplayHand={replayCurrentHand}
        />
      )}

      {/* Learning Dashboard Modal */}
      {showLearningDashboard && (
        <div className="learning-dashboard-overlay" data-testid="dashboard-overlay" onClick={() => setShowLearningDashboard(false)}>
          <div className="learning-dashboard-modal" data-testid="dashboard-modal" onClick={(e) => e.stopPropagation()}>
            <button className="close-dashboard" data-testid="dashboard-close-button" onClick={() => setShowLearningDashboard(false)}>×</button>
            {/* Force remount on each open to refresh data */}
            <LearningDashboard
              key={Date.now()}
              userId={userId || 1}
              onPracticeClick={(rec) => {
                console.log('Practice recommendation:', rec);
                setShowLearningDashboard(false);
              }}
            />
          </div>
        </div>
      )}

      {/* DDS Status Indicator - Shows if expert AI is using DDS */}
      <DDSStatusIndicator />
    </div>
  );
}
// Wrap App with AuthProvider
function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithAuth;