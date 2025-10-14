import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { PlayTable, ScoreDisplay, getSuitOrder } from './PlayComponents';
import { BridgeCard } from './components/bridge/BridgeCard';
import { BiddingBox as BiddingBoxComponent } from './components/bridge/BiddingBox';
import { ReviewModal } from './components/bridge/ReviewModal';
import { ConventionHelpModal } from './components/bridge/ConventionHelpModal';
import LearningDashboard from './components/learning/LearningDashboard';
import { SessionScorePanel } from './components/session/SessionScorePanel';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SimpleLogin } from './components/auth/SimpleLogin';
import DDSStatusIndicator from './components/DDSStatusIndicator';

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
  return (
    <div className={`player-hand player-${position.toLowerCase()}`}>
      <h3>{position}</h3>
      <div className="hand-display">
        {suitOrder.map(suit => (
          <div key={suit} className="suit-group">
            {hand.filter(card => card && card.suit === suit).map((card, index) => (
              <BridgeCard key={`${suit}-${index}`} rank={card.rank} suit={card.suit} />
            ))}
          </div>
        ))}
      </div>
      <HandAnalysis points={points} vulnerability={vulnerability} />
    </div>
  );
}
function BiddingTable({ auction, players, nextPlayerIndex, onBidClick }) {
  const getBidsForPlayer = (playerIndex) => {
    let playerBids = [];
    for (let i = playerIndex; i < auction.length; i += 4) { playerBids.push(auction[i]); }
    return playerBids;
  };
  const northBids = getBidsForPlayer(0), eastBids = getBidsForPlayer(1), southBids = getBidsForPlayer(2), westBids = getBidsForPlayer(3);
  const maxRows = Math.max(northBids.length, eastBids.length, southBids.length, westBids.length) || 1;
  let rows = [];
  for (let i = 0; i < maxRows; i++) { rows.push( <tr key={i}><td onClick={() => northBids[i] && onBidClick(northBids[i])}>{northBids[i]?.bid || ''}</td><td onClick={() => eastBids[i] && onBidClick(eastBids[i])}>{eastBids[i]?.bid || ''}</td><td onClick={() => southBids[i] && onBidClick(southBids[i])}>{southBids[i]?.bid || ''}</td><td onClick={() => westBids[i] && onBidClick(westBids[i])}>{westBids[i]?.bid || ''}</td></tr> ); }
  return ( <table className="bidding-table"><thead><tr><th className={players[nextPlayerIndex] === 'North' ? 'current-player' : ''}>North</th><th className={players[nextPlayerIndex] === 'East' ? 'current-player' : ''}>East</th><th className={players[nextPlayerIndex] === 'South' ? 'current-player' : ''}>South</th><th className={players[nextPlayerIndex] === 'West' ? 'current-player' : ''}>West</th></tr></thead><tbody>{rows}</tbody></table> );
}
// Note: BiddingBox component migrated to components/bridge/BiddingBox.jsx

function App() {
  // Auth state
  const { user, logout, isAuthenticated, loading: authLoading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);

  const [hand, setHand] = useState([]);
  const [handPoints, setHandPoints] = useState(null);
  const [auction, setAuction] = useState([]);
  const [players] = useState(['North', 'East', 'South', 'West']);
  const [dealer] = useState('North');
  const [nextPlayerIndex, setNextPlayerIndex] = useState(0);
  const [isAiBidding, setIsAiBidding] = useState(false);
  const [error, setError] = useState('');
  const [displayedMessage, setDisplayedMessage] = useState('');
  const [scenarioList, setScenarioList] = useState([]);
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

  const resetAuction = (dealData, skipInitialAiBidding = false) => {
    setInitialDeal(dealData);
    setHand(dealData.hand);
    setHandPoints(dealData.points);
    setVulnerability(dealData.vulnerability);
    setAuction([]);
    setNextPlayerIndex(players.indexOf(dealer));
    setDisplayedMessage('');
    setError('');
    // Don't start AI bidding immediately on initial mount to prevent race condition
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
      const response = await fetch(`${API_URL}/api/get-all-hands`);
      if (!response.ok) throw new Error("Failed to fetch all hands.");
      const data = await response.json();
      setAllHands(data.hands);
    } catch (err) {
      setError("Could not fetch all hands from server.");
    }
  };

  const handleShowHandsThisDeal = () => {
    if (!showHandsThisDeal) {
      fetchAllHands();
    }
    setShowHandsThisDeal(!showHandsThisDeal);
  };

  const handleToggleAlwaysShowHands = () => {
    const newValue = !alwaysShowHands;
    setAlwaysShowHands(newValue);
    if (newValue) {
      fetchAllHands();
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          auction_history: auction,
          user_concern: userConcern,
          game_phase: gamePhase,  // Include current game phase
          user_hand: hand,  // Send actual hand data shown to user
          user_hand_points: handPoints  // Send actual point data shown to user
        })
      });

      if (!response.ok) throw new Error("Failed to request review.");
      const data = await response.json();

      setReviewFilename(data.filename);

      // Create prompt based on whether file was saved or not
      let prompt;
      if (data.saved_to_file) {
        // Local: file was saved, reference it
        if (gamePhase === 'playing') {
          prompt = `Please analyze the gameplay in backend/review_requests/${data.filename}. This includes both the auction and card play progress according to SAYC.${userConcern ? `\n\nI'm particularly concerned about: ${userConcern}` : ''}`;
        } else {
          prompt = `Please analyze the bidding in backend/review_requests/${data.filename} and identify any errors or questionable bids according to SAYC.${userConcern ? `\n\nI'm particularly concerned about: ${userConcern}` : ''}`;
        }
      } else {
        // Render: file not saved, include full data in prompt
        const reviewData = data.review_data;
        if (gamePhase === 'playing') {
          prompt = `Please analyze this bridge hand including both auction and card play according to SAYC.

**Hand Data:**
${JSON.stringify(reviewData, null, 2)}

${userConcern ? `\n**User's Concern:** ${userConcern}` : ''}

Please provide a detailed analysis of the auction and card play, identifying any bidding or play errors.`;
        } else {
          prompt = `Please analyze this bridge hand and identify any errors or questionable bids according to SAYC.

**Hand Data:**
${JSON.stringify(reviewData, null, 2)}

${userConcern ? `\n**User's Concern:** ${userConcern}` : ''}

Please provide a detailed analysis of the auction and identify any bidding errors.`;
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
      const response = await fetch(`${API_URL}/api/convention-info?name=${encodeURIComponent(conventionName)}`);
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          auction_history: auctionBids,
          vulnerability: vulnerability
        })
      });

      if (!response.ok) throw new Error("Failed to start play phase");

      const data = await response.json();
      console.log('Play started:', data);

      // Fetch initial play state before transitioning
      const stateResponse = await fetch(`${API_URL}/api/get-play-state`);
      if (stateResponse.ok) {
        const state = await stateResponse.json();
        setPlayState(state);
        console.log('✅ Initial play state set:', state);
        console.log('🎭 Key positions:', {
          declarer: state.contract.declarer,
          dummy: state.dummy,
          next_to_play: state.next_to_play,
          dummy_revealed: state.dummy_revealed
        });

        // If South is dummy, fetch declarer's hand immediately for user control
        if (state.dummy === 'S') {
          console.log('🃏 South is dummy - fetching declarer hand for user control');
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`);
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            const declarerPos = state.contract.declarer;
            const declarerCards = handsData.hands[declarerPos]?.hand || [];
            console.log('🃏 Declarer hand fetched:', {
              declarerPos,
              cardCount: declarerCards.length
            });
            setDeclarerHand(declarerCards);
          }
        }
      }

      // Transition to play phase
      setGamePhase('playing');
      setDisplayedMessage(`Contract: ${data.contract}. Opening leader: ${data.opening_leader}`);

      // Start AI play loop
      setIsPlayingCard(true);
    } catch (err) {
      console.error('Error starting play:', err);
      setError('Failed to start card play phase');
    }
  };

  const handleCardPlay = async (card) => {
    console.log('🃏 handleCardPlay called:', { card, isPlayingCard });

    try {
      console.log('✅ Playing card:', card);
      setIsPlayingCard(true);

      const response = await fetch(`${API_URL}/api/play-card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`);
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
        // Trick is complete - show winner for 5 seconds before clearing
        console.log(`Trick complete! Winner: ${data.trick_winner}`);

        // Wait 5 seconds to display the winner
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Clear the trick and get updated state
        await fetch(`${API_URL}/api/clear-trick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        // Fetch state after trick clear to see who's next
        const nextStateResponse = await fetch(`${API_URL}/api/get-play-state`);
        if (nextStateResponse.ok) {
          const nextState = await nextStateResponse.json();
          setPlayState(nextState);

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
        const updatedState = await fetch(`${API_URL}/api/get-play-state`).then(r => r.json());
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

    try {
      setIsPlayingCard(true);

      // Declarer position (partner of dummy)
      const declarerPosition = playState.contract.declarer;

      const response = await fetch(`${API_URL}/api/play-card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`);
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
        // Trick is complete - show winner for 5 seconds before clearing
        console.log(`Trick complete! Winner: ${data.trick_winner}`);

        // Wait 5 seconds to display the winner
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Clear the trick and get updated state
        await fetch(`${API_URL}/api/clear-trick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        // Fetch state after trick clear to see who's next
        const nextStateResponse = await fetch(`${API_URL}/api/get-play-state`);
        if (nextStateResponse.ok) {
          const nextState = await nextStateResponse.json();
          setPlayState(nextState);

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
        const updatedState = await fetch(`${API_URL}/api/get-play-state`).then(r => r.json());
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

    try {
      console.log('✅ Playing dummy card:', card);
      setIsPlayingCard(true);

      // Dummy position (partner of declarer when South is declarer)
      const dummyPosition = playState.dummy;

      const response = await fetch(`${API_URL}/api/play-card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`);
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
        // Trick is complete - show winner for 5 seconds before clearing
        console.log(`Trick complete! Winner: ${data.trick_winner}`);

        // Wait 5 seconds to display the winner
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Clear the trick and get updated state
        await fetch(`${API_URL}/api/clear-trick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        // Fetch state after trick clear to see who's next
        const nextStateResponse = await fetch(`${API_URL}/api/get-play-state`);
        if (nextStateResponse.ok) {
          const nextState = await nextStateResponse.json();
          setPlayState(nextState);

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
        const updatedState = await fetch(`${API_URL}/api/get-play-state`).then(r => r.json());
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
    // Complete hand in session if we have session data
    if (sessionData && sessionData.active && scoreData) {
      try {
        const response = await fetch(`${API_URL}/api/session/complete-hand`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            score_data: scoreData,
            auction_history: auction.map(a => a.bid)
          })
        });

        if (response.ok) {
          const result = await response.json();
          setSessionData({ active: true, session: result.session });

          if (result.session_complete) {
            setDisplayedMessage(`Session complete! Winner: ${result.winner}`);
          } else {
            // Update dealer and vulnerability for next hand
            setVulnerability(result.session.vulnerability);
          }
        }
      } catch (err) {
        console.error('Failed to update session:', err);
      }
    }

    setScoreData(null);
  };

  // ========== END CARD PLAY FUNCTIONS ==========

  const dealNewHand = async () => {
    try {
      const response = await fetch(`${API_URL}/api/deal-hands`);
      if (!response.ok) throw new Error("Failed to deal hands.");
      const data = await response.json();
      resetAuction(data);
    } catch (err) { setError("Could not connect to server to deal."); }
  };
  
  const handleLoadScenario = async () => {
    if (!selectedScenario) return;
    try {
      const response = await fetch(`${API_URL}/api/load-scenario`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: selectedScenario })
      });
      if (!response.ok) throw new Error("Failed to load scenario.");
      const data = await response.json();
      resetAuction(data);
    } catch (err) { setError("Could not load scenario from server."); }
  };

  const handleReplayHand = () => {
    if (!initialDeal) return;
    resetAuction(initialDeal);
  };
  
  useEffect(() => {
    const fetchScenariosAndDeal = async () => {
      try {
        const response = await fetch(`${API_URL}/api/scenarios`);
        const data = await response.json();
        setScenarioList(data.scenarios);
        if (data.scenarios.length > 0) setSelectedScenario(data.scenarios[0]);
      } catch (err) { console.error("Could not fetch scenarios", err); }

      // Start or resume session
      try {
        const sessionResponse = await fetch(`${API_URL}/api/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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
        const response = await fetch(`${API_URL}/api/deal-hands`);
        if (!response.ok) throw new Error("Failed to deal hands.");
        const data = await response.json();
        // Skip AI bidding on initial mount to prevent race condition
        resetAuction(data, true);

        // After state has settled, enable AI bidding if North starts
        setTimeout(() => {
          if (players.indexOf(dealer) !== 2) { // If dealer is not South (index 2)
            setIsAiBidding(true);
          }
        }, 100);
      } catch (err) {
        setError("Could not connect to server to deal.");
      }
    };
    fetchScenariosAndDeal();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleUserBid = async (bid) => {
    if (players[nextPlayerIndex] !== 'South' || isAiBidding) return;
    setDisplayedMessage('...'); 
    const newAuction = [...auction, { bid: bid, explanation: 'Your bid.' }];
    setAuction(newAuction);
    try {
      const feedbackResponse = await fetch(`${API_URL}/api/get-feedback`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auction_history: newAuction.map(a => a.bid) })
      });
      const feedbackData = await feedbackResponse.json();
      setDisplayedMessage(feedbackData.feedback); 
    } catch (err) { setDisplayedMessage('Could not get feedback from the server.'); }
    setNextPlayerIndex((nextPlayerIndex + 1) % 4);
    setIsAiBidding(true); 
  };
  
  const handleBidClick = (bidObject) => { setDisplayedMessage(`[${bidObject.bid}] ${bidObject.explanation}`); };
  
  useEffect(() => {
    const isAuctionOver = (bids) => {
      if (bids.length < 3) return false;
      const nonPassBids = bids.filter(b => b.bid !== 'Pass');
      if (bids.length >= 4 && nonPassBids.length === 0) return true;
      if (nonPassBids.length === 0) return false;
      return bids.slice(-3).map(b => b.bid).join(',') === 'Pass,Pass,Pass';
    };

    if (isAiBidding && players[nextPlayerIndex] !== 'South' && !isAuctionOver(auction)) {
      const runAiTurn = async () => {
        await new Promise(resolve => setTimeout(resolve, 500));
        try {
          // Capture current values to prevent race conditions
          const currentAuction = auction;
          const currentPlayer = players[nextPlayerIndex];

          const response = await fetch(`${API_URL}/api/get-next-bid`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auction_history: currentAuction.map(a => a.bid), current_player: currentPlayer })
          });
          if (!response.ok) throw new Error("AI failed to get bid.");
          const data = await response.json();

          // Use updater functions to ensure we have the latest state
          setAuction(prevAuction => [...prevAuction, data]);
          setNextPlayerIndex(prevIndex => (prevIndex + 1) % 4);
        } catch (err) {
          setError("AI bidding failed. Is the server running?");
          setIsAiBidding(false);
        }
      };
      runAiTurn();
    } else if (isAiBidding) {
      setIsAiBidding(false);
      // Check if bidding just completed - start play phase after 3 second delay
      if (isAuctionOver(auction)) {
        setTimeout(() => startPlayPhase(), 3000);
      }
    }
  }, [auction, nextPlayerIndex, isAiBidding, players, startPlayPhase]);

  // AI play loop - runs during play phase
  useEffect(() => {
    console.log('🔄 AI play loop triggered:', { gamePhase, isPlayingCard });
    if (gamePhase !== 'playing' || !isPlayingCard) {
      console.log('⏭️ AI play loop skipped:', { gamePhase, isPlayingCard });
      return;
    }

    const runAiPlay = async () => {
      try {
        console.log('🎬 AI play loop RUNNING...');
        // Get current play state
        const stateResponse = await fetch(`${API_URL}/api/get-play-state`);
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

        // If user (South) is dummy, fetch and store declarer's hand for user control
        if (userIsDummy && state.dummy_hand && !declarerHand) {
          // South is dummy, so we need to get declarer's (North's) hand
          // The backend should provide this via get-all-hands
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`);
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            setDeclarerHand(handsData.hands[declarerPos]?.hand || []);
          }
        }

        // Check if play is complete (13 tricks)
        const totalTricks = Object.values(state.tricks_won).reduce((a, b) => a + b, 0);
        if (totalTricks === 13) {
          // Play complete - calculate score
          const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vulnerability: vulnerability })
          });

          if (scoreResponse.ok) {
            const scoreData = await scoreResponse.json();
            setScoreData(scoreData);
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
        // CRITICAL: Determine who controls the next play
        // According to bridge rules:
        // - Declarer controls BOTH their own hand AND dummy's hand
        // - Dummy makes NO decisions
        // - Defenders control only their own hands
        // ============================================================

        // Check if user should control the next play
        let userShouldControl = false;
        let userControlMessage = "";

        // Case 1: User (South) is declarer
        if (userIsDeclarer) {
          // User controls BOTH South (declarer) and dummy positions
          if (nextPlayer === 'S') {
            userShouldControl = true;
            userControlMessage = "Your turn to play from your hand!";
          } else if (nextPlayer === state.dummy) {
            // User is declarer and it's dummy's turn
            userShouldControl = true;
            userControlMessage = `Your turn to play from dummy's hand (${state.dummy})!`;
          }
          // If nextPlayer is a defender (E or W), AI plays
        }
        // Case 2: User (South) is dummy
        else if (userIsDummy) {
          // When user is dummy, AI declarer controls BOTH declarer and dummy (South)
          // User makes NO plays at all
          // Exception: This should never happen in our implementation
          // because if South is dummy, declarer is N/E/W (AI), so AI controls everything
          userShouldControl = false;
        }
        // Case 3: User (South) is a defender (neither declarer nor dummy)
        else {
          // User only controls South (their own defender hand)
          if (nextPlayer === 'S') {
            userShouldControl = true;
            userControlMessage = "Your turn to play!";
          }
          // If nextPlayer is declarer or dummy, AI plays
        }

        // If user should control this play, stop AI loop
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

        // If it's dummy's turn and AI is declarer, AI plays from dummy
        if (nextPlayer === state.dummy && !userIsDeclarer) {
          console.log('▶️ AI declarer playing from dummy\'s hand:', nextPlayer);
        } else {
          console.log('▶️ AI player\'s turn:', nextPlayer);
        }
        // AI player's turn
        await new Promise(resolve => setTimeout(resolve, 1000)); // Delay for visibility

        const playResponse = await fetch(`${API_URL}/api/get-ai-play`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ position: nextPlayer })
        });

        if (!playResponse.ok) throw new Error("AI play failed");

        const playData = await playResponse.json();
        console.log('AI played:', playData);

        // Fetch updated play state to show the card that was just played
        const updatedStateResponse = await fetch(`${API_URL}/api/get-play-state`);
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
          // Trick is complete - show winner for 5 seconds before clearing
          console.log(`Trick complete! Winner: ${playData.trick_winner}`);

          // Wait 5 seconds to display the winner
          await new Promise(resolve => setTimeout(resolve, 5000));

          // Clear the trick
          await fetch(`${API_URL}/api/clear-trick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });

          // Fetch updated play state to show empty trick
          const clearedStateResponse = await fetch(`${API_URL}/api/get-play-state`);
          if (clearedStateResponse.ok) {
            const clearedState = await clearedStateResponse.json();
            setPlayState(clearedState);
            console.log('🧹 Trick cleared, updated state:', {
              trick_size: clearedState.current_trick.length,
              next_to_play: clearedState.next_to_play
            });

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
        setError('AI play failed');
        setIsPlayingCard(false);
      }
    };

    runAiPlay();
  }, [gamePhase, isPlayingCard, vulnerability]);

  const shouldShowHands = showHandsThisDeal || alwaysShowHands;

  // User menu component
  const UserMenu = () => {
    if (!isAuthenticated) {
      return (
        <button onClick={() => setShowLogin(true)} className="auth-button">
          Sign In
        </button>
      );
    }

    return (
      <div className="user-menu">
        <span className="user-display">👤 {user.display_name}</span>
        <button onClick={logout} className="logout-button">Logout</button>
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
              {hand && hand.length > 0 ? getSuitOrder(null).map(suit => ( <div key={suit} className="suit-group">{hand.filter(card => card.suit === suit).map((card, index) => ( <BridgeCard key={`${suit}-${index}`} rank={card.rank} suit={card.suit} />))}</div>)) : <p>Dealing...</p>}
            </div>
            <HandAnalysis points={handPoints} vulnerability={vulnerability} />
          </div>
        </div>
      ) : null}

      {!shouldShowHands && gamePhase === 'bidding' && (
        <div className="bidding-area">
          <h2>Bidding</h2>
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
            isUserTurn={
              // User plays South's cards when:
              // 1. It's South's turn AND South is not dummy (user is declarer or defender)
              // 2. It's South's turn AND user is dummy being controlled by AI (actually, AI controls this - so this shouldn't enable user)
              playState.next_to_play === 'S' && playState.dummy !== 'S'
            }
            isDeclarerTurn={
              // User plays declarer's cards (North) when:
              // - User is dummy (South is dummy)
              // - It's declarer's turn
              // NOTE: This scenario doesn't apply in our game - if South is dummy, AI is declarer
              playState.next_to_play === playState.contract.declarer && playState.dummy === 'S'
            }
            isDummyTurn={
              // User plays dummy's cards when:
              // - User is declarer (South is declarer)
              // - It's dummy's turn
              playState.next_to_play === playState.dummy && playState.contract.declarer === 'S'
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
          {gamePhase === 'bidding' && (
            <>
              <div className="game-controls">
                <button className="deal-button" onClick={dealNewHand}>Deal New Hand</button>
                <button className="replay-button" onClick={handleReplayHand} disabled={!initialDeal || auction.length === 0}>Replay Hand</button>
              </div>
              <div className="scenario-loader">
                <select value={selectedScenario} onChange={(e) => setSelectedScenario(e.target.value)}>{scenarioList && scenarioList.length > 0 ? scenarioList.map(name => <option key={name} value={name}>{name}</option>) : <option>Loading...</option>}</select>
                <button onClick={handleLoadScenario}>Load Scenario</button>
              </div>
            </>
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
              <button onClick={handleShowConventionHelp} className="help-button">ℹ️ Convention Help</button>
              <button onClick={() => setShowReviewModal(true)} className="ai-review-button">🤖 Request AI Review</button>
              <button onClick={() => setShowLearningDashboard(true)} className="learning-dashboard-button">📊 My Progress</button>
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
        />
      )}

      {/* Learning Dashboard Modal */}
      {showLearningDashboard && (
        <div className="learning-dashboard-overlay" onClick={() => setShowLearningDashboard(false)}>
          <div className="learning-dashboard-modal" onClick={(e) => e.stopPropagation()}>
            <button className="close-dashboard" onClick={() => setShowLearningDashboard(false)}>×</button>
            <LearningDashboard
              userId={1}
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