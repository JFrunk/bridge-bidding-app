import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { flushSync } from 'react-dom';
import './App.css';
import { PlayTable, getSuitOrder } from './PlayComponents';
import ResultOverlay from './components/shared/ResultOverlay';
import Card from './shared/components/Card';
import { BridgeCard } from './components/bridge/BridgeCard';  // Legacy - being phased out
import { VerticalCard } from './components/bridge/VerticalCard';
import { BiddingBox as BiddingBoxComponent } from './components/bridge/BiddingBox';
import { ReviewModal } from './components/bridge/ReviewModal';
import { FeedbackModal } from './components/bridge/FeedbackModal';
import { ConventionHelpModal } from './components/bridge/ConventionHelpModal';
import BidFeedbackPanel from './components/bridge/BidFeedbackPanel';
import BeliefPanel from './components/bridge/BeliefPanel';
import { SessionModeBar } from './components/bridge/SessionModeBar';
import { CoachPanel } from './components/bridge/CoachPanel';
import { BidChip } from './components/shared/BidChip';
import { GovernorConfirmDialog } from './components/bridge/GovernorConfirmDialog';
import LearningDashboard from './components/learning/LearningDashboard';
import LearningMode from './components/learning/LearningMode';
// Unified Review Page (bidding + play with tab toggle)
import ReviewPage from './components/learning/ReviewPage';
import { ModeSelector } from './components/ModeSelector';
import { BiddingWorkspace } from './components/workspaces/BiddingWorkspace';
import { PlayWorkspace } from './components/workspaces/PlayWorkspace';
import { SessionScorePanel } from './components/session/SessionScorePanel';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { UserProvider, useUser } from './contexts/UserContext';
import { RoomProvider, useRoom } from './contexts/RoomContext';
import { RoomLobby, RoomStatusBar, JoinRoomModal, RoomWaitingState } from './components/room';
import WelcomeWizard from './components/onboarding/WelcomeWizard';
import { SimpleLogin } from './components/auth/SimpleLogin';
import { PrivacyPolicy } from './components/legal/PrivacyPolicy';
import { AboutUs } from './components/legal/AboutUs';
import { RegistrationPrompt } from './components/auth/RegistrationPrompt';
import DDSStatusIndicator from './components/DDSStatusIndicator';
import AIDifficultySelector from './components/AIDifficultySelector';
import { getSessionHeaders, fetchWithSession } from './utils/sessionHelper';
import { getRecentLogs } from './utils/consoleCapture';
import { getRecentActions } from './utils/actionTracker';
import { GlossaryDrawer } from './components/glossary';
import TopNavigation from './components/navigation/TopNavigation';
import UserMenu from './components/navigation/UserMenu';
import { useDevMode } from './hooks/useDevMode';
import { TrickPotentialChart, TrickPotentialButton } from './components/analysis/TrickPotentialChart';
import LearningFlowsHub from './components/learning/flows/LearningFlowsHub';
import SplitGameLayout from './components/layout/SplitGameLayout';
import { ClaimModal } from './components/play/ClaimModal';
import { PrivacyPage } from './components/legal/PrivacyPage';
import { AboutPage } from './components/legal/AboutPage';
import { Footer } from './components/navigation/Footer';
import {
  initializeAnalytics,
  trackDealHand,
  trackBidMade,
  trackCardPlayed,
  trackHandComplete,
  trackBiddingComplete,
  trackModeChange,
  trackDashboardOpen,
  trackScenarioSelected,
} from './services/analytics';

// API URL configuration - uses environment variable in production, localhost in development
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// --- UI Components ---
// Note: Card component migrated to BridgeCard (components/bridge/BridgeCard.jsx)
function HandAnalysis({ points, vulnerability, ddTable, onShowTrickPotential, strip = false }) {
  if (!points) return null;

  // Strip mode: Single horizontal line for BID screen redesign
  if (strip) {
    return (
      <div className="hand-analysis-strip">
        <span className="strip-total">
          <strong>{points.total_points}</strong> total pts
        </span>
        <span className="strip-divider">|</span>
        <span className="strip-suits">
          <span className="suit-black">♠</span> {points.suit_hcp['♠']}({points.suit_lengths['♠']})
          {' '}
          <span className="suit-red">♥</span> {points.suit_hcp['♥']}({points.suit_lengths['♥']})
          {' '}
          <span className="suit-red">♦</span> {points.suit_hcp['♦']}({points.suit_lengths['♦']})
          {' '}
          <span className="suit-black">♣</span> {points.suit_hcp['♣']}({points.suit_lengths['♣']})
        </span>
        <span className="strip-divider">|</span>
        <span className="strip-breakdown">
          HCP: {points.hcp} + Dist: {points.dist_points}
        </span>
      </div>
    );
  }

  return (
    <div className="hand-analysis">
      <div className="hand-analysis-header">
        <h4>Hand Analysis (Vuln: {vulnerability})</h4>
        {ddTable && <TrickPotentialButton onClick={onShowTrickPotential} />}
      </div>
      <p><strong>HCP:</strong> {points.hcp} + <strong>Dist:</strong> {points.dist_points} = <strong>Total: {points.total_points}</strong></p>
      <div className="suit-points">
        <div><span className="suit-black">♠</span> {points.suit_hcp['♠']} pts ({points.suit_lengths['♠']})</div>
        <div><span className="suit-red">♥</span> {points.suit_hcp['♥']} pts ({points.suit_lengths['♥']})</div>
        <div><span className="suit-red">♦</span> {points.suit_hcp['♦']} pts ({points.suit_lengths['♦']})</div>
        <div><span className="suit-black">♣</span> {points.suit_hcp['♣']} pts ({points.suit_lengths['♣']})</div>
      </div>
    </div>
  );
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

                    // Apply overlap for rotated cards: use marginLeft for horizontal stacking
                    // Since cards are rotated 90deg, horizontal negative margin creates vertical appearance
                    // 25px overlap, leaving 45px visible per card (improved readability per user feedback)
                    const inlineStyle = absoluteIndex === 0 ? {} : { marginLeft: '-25px' };

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
function BiddingTable({ auction, players, nextPlayerIndex, onBidClick, dealer, isComplete = false, myPosition = null }) {
  // Build table using row-based approach:
  // - Dealer starts on row 0
  // - Each player bids in their column on current row
  // - When North column (column 0) is reached, increment to next row

  const dealerIndex = players.indexOf(dealer);

  // Room mode: Calculate partner position
  const positionMap = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
  const partnerMap = { 'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E' };
  const myPositionFull = myPosition ? positionMap[myPosition] : null;
  const partnerPositionFull = myPosition ? positionMap[partnerMap[myPosition]] : null;

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

  // If auction is empty, ensure we show at least one empty row with current player highlighted
  if (grid.length === 0) {
    grid.push([null, null, null, null]);
  }

  // Render grid as table rows
  // Show yellow placeholder button where the next player should bid
  const rows = grid.map((row, rowIndex) => {
    // Determine if this is the active row (last row with bids or empty first row)
    const isActiveRow = rowIndex === grid.length - 1;

    // Check if this cell should show the turn indicator
    const shouldShowTurnIndicator = (colIndex) => {
      if (isComplete) return false; // No indicator after auction ends
      if (!isActiveRow) return false;
      const cellPlayer = players[colIndex];
      return cellPlayer === players[nextPlayerIndex] && row[colIndex] === null;
    };

    // Render cell content (bid chip, turn indicator, or empty)
    const renderCellContent = (colIndex) => {
      if (row[colIndex]?.bid) {
        return <BidChip bid={row[colIndex].bid} />;
      }
      if (shouldShowTurnIndicator(colIndex)) {
        return (
          <div className="inline-flex items-center justify-center bg-white rounded-[0.3em] px-[0.5em] py-[0.1em] border-[3px] border-[#ffc107] min-w-[3.2em] h-[2em] mx-auto shadow-[0_0_8px_rgba(255,193,7,0.4)]">
            <span className="text-[0.8em] font-bold text-transparent select-none">_</span>
          </div>
        );
      }
      return '';
    };

    return (
      <tr key={rowIndex}>
        <td onClick={() => row[0] && onBidClick(row[0])}>
          {renderCellContent(0)}
        </td>
        <td onClick={() => row[1] && onBidClick(row[1])}>
          {renderCellContent(1)}
        </td>
        <td className="partnership-separator" onClick={() => row[2] && onBidClick(row[2])}>
          {renderCellContent(2)}
        </td>
        <td onClick={() => row[3] && onBidClick(row[3])}>
          {renderCellContent(3)}
        </td>
      </tr>
    );
  });

  // Helper to get header classes (partnership colors, current player, dealer)
  const getHeaderClass = (position) => {
    const classes = [];

    // Partnership color coding
    if (position === 'North' || position === 'South') {
      classes.push('ns-header');
    } else {
      classes.push('ew-header');
    }

    // Dealer indicator class
    if (dealer === position) {
      classes.push('dealer-indicator');
    }

    // Partnership separator (South column = boundary between N/S and E/W)
    if (position === 'South') {
      classes.push('partnership-separator');
    }

    // Player position indicator (gold border glow)
    // Solo mode: user is always South
    // Room mode: user is at myPositionFull
    if ((!myPosition && position === 'South') || (myPosition && position === myPositionFull)) {
      classes.push('player-you');
    }

    return classes.join(' ');
  };

  // Helper to get role class for room mode (You/Partner indicators)
  const getRoleClass = (position) => {
    if (!myPosition) return '';
    if (position === myPositionFull) return 'role-you';
    if (position === partnerPositionFull) return 'role-partner';
    return '';
  };

  // Helper to render role badge
  const renderRoleBadge = (position) => {
    if (!myPosition) return null;
    if (position === myPositionFull) {
      return <span className="role-badge role-badge-you">You</span>;
    }
    if (position === partnerPositionFull) {
      return <span className="role-badge role-badge-partner">Partner</span>;
    }
    return null;
  };

  return (
    <table className="bidding-table" data-testid="bidding-table">
      <thead>
        <tr>
          <th className={`${getHeaderClass('North')} ${getRoleClass('North')}`} data-testid="bidding-header-north">
            <span className="position-name">North</span>
            {renderRoleBadge('North')}
          </th>
          <th className={`${getHeaderClass('East')} ${getRoleClass('East')}`} data-testid="bidding-header-east">
            <span className="position-name">East</span>
            {renderRoleBadge('East')}
          </th>
          <th className={`${getHeaderClass('South')} ${getRoleClass('South')}`} data-testid="bidding-header-south">
            <span className="position-name">South</span>
            {renderRoleBadge('South')}
          </th>
          <th className={`${getHeaderClass('West')} ${getRoleClass('West')}`} data-testid="bidding-header-west">
            <span className="position-name">West</span>
            {renderRoleBadge('West')}
          </th>
        </tr>
      </thead>
      <tbody data-testid="bidding-table-body">{rows}</tbody>
    </table>
  );
}
// Note: BiddingBox component migrated to components/bridge/BiddingBox.jsx

function App() {
  // Auth state - now includes registration prompt features
  const {
    user,
    isAuthenticated,
    loading: authLoading,
    userId,
    isGuest,
    showRegistrationPrompt,
    dismissRegistrationPrompt,
    recordHandCompleted,
    promptForRegistration,
    requiresRegistration
  } = useAuth();

  // User experience state - for first-time onboarding and profile presets
  const {
    shouldShowWelcomeWizard,
    setExperienceLevel,
    applyProfilePresets,
    biddingCoachEnabled,
    playCoachEnabled,
    difficulty
  } = useUser();

  // Room state - for Team Practice Lobby
  const {
    inRoom,
    roomCode,
    isHost,
    myPosition,
    partnerConnected,
    gamePhase: roomGamePhase,
    isMyTurn,
    myHand: roomHand,
    auction: roomAuction,
    dealer: roomDealer,
    vulnerability: roomVulnerability,
    currentBidder: roomCurrentBidder,
    playState: roomPlayState,
    beliefs: roomBeliefs,
    leaveRoom,
    submitBid: submitRoomBid,
    startRoomPlay,
    playRoomCard,
    error: roomError,
  } = useRoom();

  const [showLogin, setShowLogin] = useState(false);
  const [showJoinRoomModal, setShowJoinRoomModal] = useState(false);
  const [vulnerability, setVulnerability] = useState('None');

  // Dev mode - toggle with Ctrl+Shift+D (or Cmd+Shift+D on Mac)
  // Also available via URL param ?dev=true or console: window.enableDevMode()
  // Controls visibility of: AI Review button, AI Difficulty Selector, AI messages
  // V2 Schema - toggle with ?v2schema=true or console: window.enableV2Schema()
  const { isDevMode, useV2Schema, toggleV2Schema } = useDevMode();

  const [hand, setHand] = useState([]);
  const [handPoints, setHandPoints] = useState(null);
  const [ddTable, setDdTable] = useState(null);  // Double-dummy trick potential table
  const [showTrickPotential, setShowTrickPotential] = useState(false);  // Overlay visibility
  const [auction, setAuction] = useState([]);
  const [players] = useState(['North', 'East', 'South', 'West']);
  const [dealer, setDealer] = useState('North');

  // Backend-authoritative bidder: set from API responses (/api/deal-hands,
  // /api/get-next-bid, /api/evaluate-bid).  The backend is the single source
  // of truth for whose turn it is to bid.
  const [nextBidder, setNextBidder] = useState(null);

  // Derive the numeric index for UI display (BiddingTable highlight, etc.)
  const nextPlayerIndex = useMemo(() => {
    if (!nextBidder) return 0;
    const idx = players.indexOf(nextBidder);
    return idx >= 0 ? idx : 0;
  }, [nextBidder, players]);

  // === ROOM MODE: Dynamic state swapping ===
  // When in a room, use shared room state instead of local state
  const displayHand = useMemo(() => {
    if (inRoom && roomHand) return roomHand;
    return hand;
  }, [inRoom, roomHand, hand]);

  const displayAuction = useMemo(() => {
    if (inRoom && roomAuction) {
      // Convert room auction (array of strings) to expected format {bid, explanation}
      return roomAuction.map(bid => ({ bid, explanation: '' }));
    }
    return auction;
  }, [inRoom, roomAuction, auction]);

  const displayDealer = useMemo(() => {
    if (inRoom && roomDealer) {
      // Convert short position to full name
      const posMap = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
      return posMap[roomDealer] || roomDealer;
    }
    return dealer;
  }, [inRoom, roomDealer, dealer]);

  const displayVulnerability = useMemo(() => {
    if (inRoom) return roomVulnerability || 'None';
    return vulnerability;
  }, [inRoom, roomVulnerability, vulnerability]);

  // In room mode, determine if user can bid based on position and turn
  const canUserBid = useMemo(() => {
    if (inRoom) {
      return isMyTurn && partnerConnected && roomGamePhase === 'bidding';
    }
    return nextBidder === 'South';
  }, [inRoom, isMyTurn, partnerConnected, roomGamePhase, nextBidder]);

  // Waiting for host to deal (guest joined but no hands yet)
  const isWaitingForDeal = useMemo(() => {
    return inRoom && !isHost && partnerConnected && roomGamePhase === 'waiting';
  }, [inRoom, isHost, partnerConnected, roomGamePhase]);

  // Game is active in room mode (bidding or playing)
  const isRoomGameActive = useMemo(() => {
    return inRoom && (roomGamePhase === 'bidding' || roomGamePhase === 'playing');
  }, [inRoom, roomGamePhase]);

  // Initialize Google Analytics on mount
  useEffect(() => {
    initializeAnalytics();
  }, []);

  // AUTO-HIDE lobby when game becomes active (view orchestration)
  // Also sync local state from room state when in room mode
  useEffect(() => {
    if (isRoomGameActive) {
      // Game started - unmount lobby, show game view
      setShowTeamPractice(false);
      setShowModeSelector(false);

      // Sync local gamePhase from room state
      if (roomGamePhase === 'bidding') {
        setGamePhase('bidding');
      } else if (roomGamePhase === 'playing') {
        setGamePhase('playing');
      }

      // Sync hand from room state
      if (roomHand && roomHand.length > 0) {
        setHand(roomHand);
      }
    }
  }, [isRoomGameActive, roomGamePhase, roomHand]);

  // ROOM MODE: Sync nextBidder from roomCurrentBidder (short form → full form)
  // This ensures AI bidding triggers correctly for E/W positions
  useEffect(() => {
    if (!inRoom || !roomCurrentBidder) return;

    // Convert short position to full name
    const positionMap = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
    const fullPosition = positionMap[roomCurrentBidder] || roomCurrentBidder;

    // Only update if different to avoid infinite loops
    if (fullPosition !== nextBidder) {
      console.log('🔄 Room: Syncing nextBidder:', roomCurrentBidder, '→', fullPosition);
      setNextBidder(fullPosition);
    }
  }, [inRoom, roomCurrentBidder, nextBidder]);

  // ROOM MODE: Sync auction from room state
  // Room auction comes from polling, need to sync to local auction state
  useEffect(() => {
    if (!inRoom) return;

    // Import roomAuction - need to convert to expected format if needed
    const { auction: roomAuctionFromContext } = { auction: roomAuction };
    if (roomAuctionFromContext && roomAuctionFromContext.length > 0) {
      // Room auction might be just bid strings, convert to {bid, explanation} format
      const formattedAuction = roomAuctionFromContext.map(bid =>
        typeof bid === 'string' ? { bid, explanation: '' } : bid
      );

      // Only update if different
      if (JSON.stringify(formattedAuction) !== JSON.stringify(auction)) {
        console.log('🔄 Room: Syncing auction from room state:', formattedAuction.length, 'bids');
        setAuction(formattedAuction);
      }
    }
  }, [inRoom, roomAuction, auction]);

  // ROOM MODE: Sync dealer from room state
  useEffect(() => {
    if (!inRoom || !roomDealer) return;

    // Convert short to full name if needed
    const positionMap = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
    const fullDealer = positionMap[roomDealer] || roomDealer;

    if (fullDealer !== dealer) {
      console.log('🔄 Room: Syncing dealer:', roomDealer, '→', fullDealer);
      setDealer(fullDealer);
    }
  }, [inRoom, roomDealer, dealer]);

  // ROOM MODE: Sync playState from room context
  // Room's play_state comes from polling - need to sync to local playState
  useEffect(() => {
    if (!inRoom) return;

    if (roomPlayState) {
      console.log('🔄 Room: Syncing playState from room context');
      setPlayState(roomPlayState);
    }
  }, [inRoom, roomPlayState]);

  // ROOM MODE: Invalidate stale hint when auction advances
  // When partner or AI bids, the suggested bid is no longer valid
  const roomAuctionLength = displayAuction?.length || 0;
  useEffect(() => {
    if (!inRoom) return;
    // Clear stale hint so user must re-request for current auction state
    setSuggestedBid(null);
  }, [inRoom, roomAuctionLength]);

  const [isAiBidding, setIsAiBidding] = useState(false);
  const [error, setError] = useState('');
  const [displayedMessage, setDisplayedMessage] = useState('');
  const [bidFeedback, setBidFeedback] = useState(null);  // Structured feedback from evaluate-bid
  const [lastUserBid, setLastUserBid] = useState(null);  // Track last user bid for feedback display
  const [beliefs, setBeliefs] = useState(null);  // BiddingState beliefs (partner + opponents)

  // Beliefs for coaching - use room beliefs when in room mode
  const displayBeliefs = useMemo(() => {
    if (inRoom && roomBeliefs) return roomBeliefs;
    return beliefs;
  }, [inRoom, roomBeliefs, beliefs]);

  const [suggestedBid, setSuggestedBid] = useState(null);  // AI-suggested bid for "What Should I Bid?"
  const [selectedBid, setSelectedBid] = useState(null);  // Selected bid for explanation display in CoachPanel

  // Governor Safety Guard state - blocks critical/significant impact bids when hints are enabled
  const [pendingBid, setPendingBid] = useState(null);  // Bid waiting for governor confirmation
  const [pendingBidFeedback, setPendingBidFeedback] = useState(null);  // Feedback for pending bid
  const [showGovernorDialog, setShowGovernorDialog] = useState(false);  // Governor confirmation dialog visibility

  const [scenarioList, setScenarioList] = useState([]);
  const [scenariosByLevel, setScenariosByLevel] = useState(null);
  const [initialDeal, setInitialDeal] = useState(null);
  const [allHands, setAllHands] = useState(null);
  // Single toggle for showing all hands - persisted to localStorage
  const [showAllHands, setShowAllHands] = useState(() => {
    const saved = localStorage.getItem('bridge-show-all-hands');
    return saved === 'true';
  });
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showGlossary, setShowGlossary] = useState(false);
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);
  const [showAboutUs, setShowAboutUs] = useState(false);

  // Auto-show privacy/about modals when URL path matches (for crawler access)
  useEffect(() => {
    const path = window.location.pathname;
    if (path === '/privacy') setShowPrivacyPolicy(true);
    if (path === '/about') setShowAboutUs(true);
  }, []);

  const [userConcern, setUserConcern] = useState('');
  const [reviewPrompt, setReviewPrompt] = useState('');
  const [reviewFilename, setReviewFilename] = useState('');
  const [showConventionHelp, setShowConventionHelp] = useState(false);
  const [conventionInfo, setConventionInfo] = useState(null);
  const [showLearningDashboard, setShowLearningDashboard] = useState(false);
  const [showLearningMode, setShowLearningMode] = useState(false);
  const [showLearningFlowsHub, setShowLearningFlowsHub] = useState(false);
  const [learningModeTrack, setLearningModeTrack] = useState('bidding'); // 'bidding' or 'play'
  const [showModeSelector, setShowModeSelector] = useState(true); // Landing page - shown by default
  const [showTeamPractice, setShowTeamPractice] = useState(false); // Team Practice Lobby
  const [showPrivacy, setShowPrivacy] = useState(false); // Privacy modal
  const [showAbout, setShowAbout] = useState(false); // About modal

  // Hand review - full-screen page (used for both post-game and dashboard review)
  const [showReviewPage, setShowReviewPage] = useState(false);
  const [handReviewSource, setHandReviewSource] = useState(null); // 'post-hand' or 'dashboard'
  const [lastSavedHandId, setLastSavedHandId] = useState(null);
  const [reviewPageHandId, setReviewPageHandId] = useState(null);
  const [reviewPageType, setReviewPageType] = useState('play'); // 'play' or 'bidding'
  // Navigation data for review pages
  const [reviewHandList, setReviewHandList] = useState([]);
  const [reviewCurrentIndex, setReviewCurrentIndex] = useState(0);
  const savedScrollPositionRef = useRef(0);

  // Hint Mode: When enabled, shows real-time feedback during bidding and play
  // This replaces the dev-only restriction with a user-controlled toggle
  const [hintModeEnabled, setHintModeEnabled] = useState(() => {
    const saved = localStorage.getItem('bridge-hint-mode');
    return saved !== 'false'; // Default to enabled
  });

  // Persist hint mode preference
  useEffect(() => {
    localStorage.setItem('bridge-hint-mode', hintModeEnabled.toString());
  }, [hintModeEnabled]);

  // Current workspace mode: 'bid' or 'play' (null when on landing page or learning mode)
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  // Active tab within bidding workspace: 'random', 'conventions', 'history'
  const [biddingTab, setBiddingTab] = useState('random');
  // Active convention name when practicing a specific convention (null = random hands mode)
  const [activeConvention, setActiveConvention] = useState(null);
  // Session hands history for replay
  const [sessionHands, setSessionHands] = useState([]);

  // Session scoring state
  const [sessionData, setSessionData] = useState(null);

  // Loading state for initial system startup
  const [isInitializing, setIsInitializing] = useState(true);

  // Helper function to check if auction is complete
  const isAuctionOver = useCallback((bids) => {
    if (!bids || bids.length < 3) return false;
    const nonPassBids = bids.filter(b => b?.bid && b.bid !== 'Pass');

    // All four players passed out (no one bid)
    if (bids.length >= 4 && nonPassBids.length === 0) return true;

    // No bids yet
    if (nonPassBids.length === 0) return false;

    // Three consecutive passes after at least one non-Pass bid
    return bids.slice(-3).every(b => b?.bid === 'Pass');
  }, []);

  // Helper function to check if auction was passed out (all 4 players passed)
  const isPassedOut = useCallback((bids) => {
    if (!bids || bids.length < 4) return false;
    const nonPassBids = bids.filter(b => b?.bid && b.bid !== 'Pass');
    return bids.length >= 4 && nonPassBids.length === 0;
  }, []);

  // Helper: Check if next player is user-controlled using BridgeRulesEngine data
  // This replaces inconsistent inline checks with a single source of truth.
  // Uses controllable_positions from backend when available, with comprehensive fallback.
  const isNextPlayerUserControlled = useCallback((state) => {
    if (!state || !state.next_to_play || !state.contract) return false;

    // Prefer backend BridgeRulesEngine data (single-player mode aware)
    if (state.controllable_positions) {
      return state.controllable_positions.includes(state.next_to_play);
    }

    // Fallback: match AI loop's comprehensive single-player logic
    const nsIsDeclaring = state.contract.declarer === 'N' || state.contract.declarer === 'S';
    if (nsIsDeclaring) {
      return state.next_to_play === 'N' || state.next_to_play === 'S';
    }
    return state.next_to_play === 'S';
  }, []);

  // No longer auto-show login - users start as guests and can register later
  // The RegistrationPrompt will appear after they've played a few hands

  // Clear game state when user logs out (isAuthenticated becomes false)
  useEffect(() => {
    if (!isAuthenticated && !authLoading) {
      // User logged out - clear all game state to prevent stale data
      setHand([]);
      setAuction([]);
      setGamePhase('bidding');
      setPlayState(null);
      setDummyHand(null);
      setDeclarerHand(null);
      setScoreData(null);
      setShowLastTrick(false);
      setLastTrick(null);
      setAllHands(null);
      setShowModeSelector(true);  // Return to landing page
      setCurrentWorkspace(null);
    }
  }, [isAuthenticated, authLoading]);

  // Card play state
  const [gamePhase, setGamePhase] = useState('bidding'); // 'bidding' or 'playing'
  const [sessionMode, setSessionMode] = useState('coached'); // 'practice', 'coached', 'quiz'
  const [showCoachPanel, setShowCoachPanel] = useState(true); // Coach panel visibility
  const [playState, setPlayState] = useState(null);

  // Sync session mode with user preferences on load
  // This ensures returning users get their saved coach preferences applied
  useEffect(() => {
    // Only sync if not in the middle of the welcome wizard
    if (!shouldShowWelcomeWizard) {
      if (biddingCoachEnabled) {
        setSessionMode('coached');
        setShowCoachPanel(true);
      } else {
        setSessionMode('practice');
        setShowCoachPanel(false);
      }
    }
    // Note: playCoachEnabled and difficulty are available for future play phase integration
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount
  const [dummyHand, setDummyHand] = useState(null);
  const [declarerHand, setDeclarerHand] = useState(null);
  const [isPlayingCard, setIsPlayingCard] = useState(false);
  const [scoreData, setScoreData] = useState(null);


  // Last trick display state
  const [showLastTrick, setShowLastTrick] = useState(false);
  const [lastTrick, setLastTrick] = useState(null);

  // Claim modal state
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [claimValidating, setClaimValidating] = useState(false);
  const [claimValidationResult, setClaimValidationResult] = useState(null);

  // Extract last trick from play state whenever it changes
  useEffect(() => {
    if (playState?.trick_history && playState.trick_history.length > 0) {
      const latestTrick = playState.trick_history[playState.trick_history.length - 1];
      setLastTrick(latestTrick);
      // Hide last trick overlay when a new trick completes (user should see current trick)
      setShowLastTrick(false);
    }
  }, [playState?.trick_history?.length]);

  // Auto-dismiss last trick overlay after 3 seconds
  useEffect(() => {
    if (showLastTrick) {
      const timer = setTimeout(() => setShowLastTrick(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [showLastTrick]);

  // Ref to store AI play loop timeout ID so we can cancel it
  const aiPlayTimeoutRef = useRef(null);

  // Ref to store pending trick clear timeout so we can cancel it when user plays
  const trickClearTimeoutRef = useRef(null);

  // Ref to prevent concurrent AI bids from racing
  const isAiBiddingInProgress = useRef(false);

  // Ref to track if we've triggered initial AI bidding after initialization
  // Prevents duplicate triggers while avoiding infinite loops
  const hasTriggeredInitialBid = useRef(false);

  // Track hand completion once when scoreData is set (avoids multiple code paths double-counting)
  const lastRecordedScoreRef = useRef(null);
  useEffect(() => {
    if (scoreData && scoreData !== lastRecordedScoreRef.current) {
      lastRecordedScoreRef.current = scoreData;
      recordHandCompleted();
    }
  }, [scoreData, recordHandCompleted]);

  // Ref to track if AI loop should be kept alive during state transitions
  // Prevents cleanup function from killing the loop when we just want to restart it
  const keepAiLoopAlive = useRef(false);

  // Ref to track deal request version - incremented when convention is loaded
  // to invalidate pending random deals (prevents race condition)
  const dealRequestIdRef = useRef(0);

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

    // Set next bidder from backend response (source of truth)
    const backendNextBidder = dealData.next_bidder || currentDealer;
    console.log('🎲 resetAuction:', {
      dealerFromBackend,
      currentDealer,
      nextBidder: backendNextBidder,
      players
    });

    setDealer(currentDealer);
    setNextBidder(backendNextBidder);

    setAuction([]);
    setBeliefs(null);
    setSuggestedBid(null);
    setSelectedBid(null);

    // Reset the AI bidding guards when auction is reset
    isAiBiddingInProgress.current = false;
    hasTriggeredInitialBid.current = skipInitialAiBidding;
// NOTE: nextPlayerIndex is now derived from dealer + auction.length
    // No need to manually set it - it will auto-calculate on next render

    setDisplayedMessage('');
    setError('');
    // Clear bid feedback from previous hand
    setBidFeedback(null);
    setLastUserBid(null);
    // Set AI bidding state - but it won't actually run until isInitializing = false
    // The new useEffect (post-initialization check) will ensure AI starts at the right time
    setIsAiBidding(!skipInitialAiBidding);
    // Reset play state
    setGamePhase('bidding');
    setPlayState(null);
    setDummyHand(null);
    setDeclarerHand(null);
    setScoreData(null);
    setIsPlayingCard(false);
    setShowLastTrick(false);
    setLastTrick(null);
    setLastSavedHandId(null);  // Clear for new hand
    // Fetch hands if showAllHands is enabled
    if (showAllHands) {
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

  // Toggle show all hands - persists to localStorage
  const handleToggleShowAllHands = async () => {
    const newValue = !showAllHands;
    setShowAllHands(newValue);
    localStorage.setItem('bridge-show-all-hands', String(newValue));

    if (newValue) {
      console.log('📡 Fetching all hands...');
      await fetchAllHands();
    } else {
      setAllHands(null);
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

  // Welcome wizard handler - saves experience level, applies presets, and routes to appropriate starting point
  const handleExperienceSelect = (data) => {
    // Save the experience level (this closes the wizard)
    setExperienceLevel(data);

    // Apply profile presets (coaches and difficulty) based on selection
    // These are initial settings - manual toggles during session will override
    const presets = applyProfilePresets(data.experienceId);
    console.log(`Applied ${data.experienceId} profile presets:`, presets);

    // Update session mode based on bidding coach preset
    if (presets.biddingCoachEnabled) {
      setSessionMode('coached');
      setShowCoachPanel(true);
    } else {
      setSessionMode('practice');
      setShowCoachPanel(false);
    }

    // Route based on selection
    switch (data.route) {
      case 'play':
        // Beginner: Go to Main Play Component with full coaching
        setShowModeSelector(false);
        setCurrentWorkspace('play');
        playRandomHand();
        break;

      case 'bid':
        // Intermediate: Jump straight into bidding practice with bidding coach
        setShowModeSelector(false);
        setCurrentWorkspace('bid');
        setBiddingTab('random');
        setGamePhase('bidding');
        dealNewHand();
        break;

      case 'modeSelector':
      default:
        // Experienced: Show full mode selector (Practice Dashboard / Convention Selector)
        setShowModeSelector(true);
        break;
    }
  };

  // Mode selection handler - routes user to appropriate mode from landing page
  const handleModeSelect = async (modeId) => {
    setShowModeSelector(false);

    switch (modeId) {
      case 'learning':
        // Open Learning Mode overlay (guard for guest users)
        if (isGuest && requiresRegistration('learning')) {
          promptForRegistration();
        } else {
          setShowLearningMode(true);
          setCurrentWorkspace(null);
        }
        break;

      case 'bid':
        // Open Bidding workspace with Random tab
        setCurrentWorkspace('bid');
        setBiddingTab('random');
        setGamePhase('bidding');  // Reset to bidding phase (fixes stuck screen when switching from play)
        // Always deal new hand when coming from landing page (showModeSelector is true)
        // But preserve state when navigating within session via top nav (if hand and auction exist)
        if (showModeSelector || !hand || hand.length === 0 || auction.length === 0) {
          dealNewHand();
        }
        break;

      case 'play': {
        // Open Play workspace and immediately start a random hand
        setCurrentWorkspace('play');

        // Determine if we should start a fresh hand or resume current game
        // Start fresh if:
        // - Coming from landing page (showModeSelector is true)
        // - Not currently in play phase
        // - Game is complete (scoreData exists from finished hand)
        // - No active play state exists
        const shouldStartFresh = showModeSelector ||
          gamePhase !== 'playing' ||
          scoreData !== null ||
          !playState;

        if (shouldStartFresh) {
          playRandomHand();  // Deal fresh hand
        }
        // If navigating via top nav while actively playing (in-progress game), keep state intact
        break;
      }

      case 'progress':
        // Open Progress dashboard (guard for guest users)
        if (isGuest && requiresRegistration('progress')) {
          promptForRegistration();
        } else {
          setShowLearningDashboard(true);
          trackDashboardOpen();
        }
        break;

      case 'team':
        // Open Team Practice Lobby
        setShowTeamPractice(true);
        setCurrentWorkspace(null);
        break;

      default:
        setCurrentWorkspace('bid');
        dealNewHand();
    }
  };

  // Handle bidding tab changes
  const handleBiddingTabChange = (tab) => {
    setBiddingTab(tab);
    // Exit convention mode when switching to random tab
    if (tab === 'random' && activeConvention) {
      setActiveConvention(null);
    }
  };

  // Add hand to session history when bidding completes
  const addToSessionHistory = useCallback((handData) => {
    setSessionHands(prev => [{
      id: Date.now(),
      hand: handData.hand,
      hcp: handData.points?.hcp || 0,
      contract: handData.contract || null,
      result: handData.result,
      dealer: handData.dealer,
      vulnerability: handData.vulnerability,
      auction: handData.auction,
      allHands: handData.allHands,
      timestamp: new Date().toISOString()
    }, ...prev].slice(0, 20)); // Keep last 20 hands
  }, []);

  // Replay a hand from session history
  const handleReplayFromHistory = useCallback((handData) => {
    // Restore the hand state
    if (handData.allHands) {
      setAllHands(handData.allHands);
    }
    if (handData.hand) {
      setHand(handData.hand);
    }
    if (handData.dealer) {
      setDealer(handData.dealer);
    }
    if (handData.vulnerability) {
      setVulnerability(handData.vulnerability);
    }
    setAuction([]);
    setGamePhase('bidding');
    setDisplayedMessage('Replaying hand from history');
  }, []);

  const handleFeedbackSubmit = async (feedbackData) => {
    // Build context data for freeplay mode
    const contextData = {
      game_phase: gamePhase,
      auction: auction,
      vulnerability: vulnerability,
      dealer: dealer,
      hand: hand,
      hand_points: handPoints,
      all_hands: allHands,
      console_logs: getRecentLogs(30),
      user_actions: getRecentActions(20),
      screenshot: feedbackData.screenshot || null,  // User-captured screenshot from modal
    };

    try {
      const response = await fetch(`${API_URL}/api/submit-feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getSessionHeaders(),
        },
        body: JSON.stringify({
          ...feedbackData,
          context: 'freeplay',
          contextData,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      throw error;
    }
  };

  const handleShowConventionHelp = async () => {
    if (!activeConvention) return;

    // Extract convention name from scenario (e.g., "Jacoby Transfer Test" -> "Jacoby Transfer")
    const conventionName = activeConvention.replace(' Test', '');

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
    // Room mode: Use room-aware play endpoints
    if (inRoom) {
      if (!isHost) {
        // Guest cannot start play - this shouldn't happen, button should be disabled
        console.warn('Guest cannot start play - waiting for host');
        return;
      }

      // Host starts room play
      const result = await startRoomPlay();
      if (result.success) {
        console.log('🎮 Room play started:', result.data);
        setGamePhase('playing');
      } else {
        console.error('Failed to start room play:', result.error);
        setError(result.error);
      }
      return;
    }

    // Individual mode: Use session-based play endpoints
    try {
      const auctionBids = auction.map(a => a.bid);

      // Convert allHands to format expected by backend
      // Backend expects: { N: [{rank, suit}, ...], E: [...], S: [...], W: [...] }
      let handsData = null;
      let handsSource = allHands;

      // If allHands not available, fetch them first
      if (!handsSource) {
        try {
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
          if (handsResponse.ok) {
            const handsResult = await handsResponse.json();
            handsSource = handsResult.hands;
          }
        } catch (e) {
          console.warn('Could not fetch hands for play:', e);
        }
      }

      if (handsSource) {
        handsData = {};
        const posMap = { 'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W' };
        for (const [fullPos, data] of Object.entries(handsSource)) {
          const shortPos = posMap[fullPos];
          if (shortPos && data?.hand) {
            handsData[shortPos] = data.hand;
          }
        }
        console.log('📤 Sending hands to start-play:', {
          positions: Object.keys(handsData),
          cardCounts: Object.fromEntries(Object.entries(handsData).map(([k, v]) => [k, v?.length || 0]))
        });
      } else {
        console.warn('⚠️ No hands available for start-play');
      }

      const response = await fetch(`${API_URL}/api/start-play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          auction_history: auctionBids,
          vulnerability: vulnerability,
          dealer: dealer,
          hands: handsData  // Send hands to avoid session state dependency
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ start-play failed:', errorData);
        throw new Error(errorData.error || "Failed to start play phase");
      }

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
        // IMPORTANT: Only set declarerHand when declarer is NOT South (user).
        // When S is declarer, the user's own hand is managed by the `hand` state.
        // Setting declarerHand to S's cards causes duplication and stale-state bugs.
        const declarerPos = state.contract.declarer;
        if (declarerPos !== 'S' && state.visible_hands && state.visible_hands[declarerPos]) {
          const declarerCards = state.visible_hands[declarerPos].cards || [];
          console.log('👁️ Setting declarer hand from visible_hands (startPlayPhase):', {
            declarerPos,
            cardCount: declarerCards.length,
            visible_hands_keys: Object.keys(state.visible_hands)
          });
          setDeclarerHand(declarerCards);
        } else if (declarerPos !== 'S' && state.dummy === 'S') {
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

        // === Update South's hand from visible_hands (only if non-empty) ===
        // Guard: never overwrite an existing hand with empty data
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || state.visible_hands['S'];
          if (Array.isArray(southCards) && southCards.length > 0) {
            console.log('👁️ Updating South hand from visible_hands (startPlayPhase):', {
              cardCount: southCards.length
            });
            setHand(southCards);
          }
        }
      }

      // Transition to play phase
      setGamePhase('playing');
      // Note: showAllHands persists user preference - don't force hide
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

    // Room mode: Use room-aware play endpoint
    if (inRoom) {
      try {
        console.log('🎮 Room card play:', card);
        setIsPlayingCard(true);

        const result = await playRoomCard({ rank: card.rank, suit: card.suit });

        if (result.success) {
          console.log('✅ Room card played:', result.data);
          // Update local hand state - remove played card
          setHand(prevHand => prevHand.filter(c =>
            !(c.rank === card.rank && c.suit === card.suit)
          ));
        } else {
          console.error('Failed to play room card:', result.error);
          setError(result.error);
        }
      } catch (err) {
        console.error('Room card play error:', err);
        setError(err.message);
      } finally {
        setIsPlayingCard(false);
      }
      return;
    }

    // Individual mode: Use session-based play endpoint

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
          card: { rank: card.rank, suit: card.suit },
          user_id: userId,
          session_id: sessionData?.session?.id
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        // Handle session state loss (e.g., server restart)
        if (errorData.error && (errorData.error.includes('No play in progress') || errorData.error.includes('Deal has not been made'))) {
          setError("Session expired. Please deal a new hand to continue.");
          setIsPlayingCard(false);
          return;
        }
        throw new Error(errorData.error || 'Illegal card play');
      }

      const data = await response.json();
      console.log('Card played:', data);

      // Track user card play
      trackCardPlayed(true);

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
              // Save hand to database immediately - pass contract info as fallback
              const saved = await saveHandToDatabase(scoreData, auction, playState?.contract);
              if (saved) scoreData._saved = true;
              setScoreData(scoreData);

              // Track hand completion
              const contractMade = scoreData.declarerMade || scoreData.declarer_made;
              const tricksWon = scoreData.tricks_won_declarer || scoreData.declarerTricks || 0;
              trackHandComplete(scoreData.contract, contractMade, tricksWon);
            } else {
              const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
              console.error('❌ Failed to get score:', errorData);
              setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
            }

            setIsPlayingCard(false);
            return;
          }

          // Start AI loop only if it's not the user's turn
          if (!isNextPlayerUserControlled(nextState)) {
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

        if (!isNextPlayerUserControlled(updatedState)) {
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

    // Room mode: route through room API (declarer controls dummy in room)
    if (inRoom) {
      return handleCardPlay(card);
    }

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
          card: { rank: card.rank, suit: card.suit },
          user_id: userId,
          session_id: sessionData?.session?.id
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
              // Save hand to database immediately - pass contract info as fallback
              const saved = await saveHandToDatabase(scoreData, auction, playState?.contract);
              if (saved) scoreData._saved = true;
              setScoreData(scoreData);

              // Track hand completion
              const contractMade = scoreData.declarerMade || scoreData.declarer_made;
              const tricksWon = scoreData.tricks_won_declarer || scoreData.declarerTricks || 0;
              trackHandComplete(scoreData.contract, contractMade, tricksWon);
            } else {
              const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
              console.error('❌ Failed to get score:', errorData);
              setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
            }

            setIsPlayingCard(false);
            return;
          }

          // Start AI loop only if it's not the user's turn
          if (!isNextPlayerUserControlled(nextState)) {
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

        if (!isNextPlayerUserControlled(updatedState)) {
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

    // Room mode: route through room API (declarer controls dummy in room)
    if (inRoom) {
      return handleCardPlay(card);
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
          card: { rank: card.rank, suit: card.suit },
          user_id: userId,
          session_id: sessionData?.session?.id
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
              // Save hand to database immediately - pass contract info as fallback
              const saved = await saveHandToDatabase(scoreData, auction, playState?.contract);
              if (saved) scoreData._saved = true;
              setScoreData(scoreData);

              // Track hand completion
              const contractMade = scoreData.declarerMade || scoreData.declarer_made;
              const tricksWon = scoreData.tricks_won_declarer || scoreData.declarerTricks || 0;
              trackHandComplete(scoreData.contract, contractMade, tricksWon);
            } else {
              const errorData = await scoreResponse.json().catch(() => ({ error: 'Unknown error' }));
              console.error('❌ Failed to get score:', errorData);
              setError(`Failed to calculate score: ${errorData.error || 'Unknown error'}`);
            }

            setIsPlayingCard(false);
            return;
          }

          // Start AI loop only if it's not the user's turn
          if (!isNextPlayerUserControlled(nextState)) {
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

        if (!isNextPlayerUserControlled(updatedState)) {
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

  // Guard to prevent duplicate saves - multiple code paths can detect hand completion
  const handSaveInProgressRef = useRef(false);

  // Helper function to save hand to database - called immediately when play ends
  // This ensures hand is saved even if user navigates away before closing score display
  const saveHandToDatabase = useCallback(async (scoreDataToSave, auctionToSave, contractInfo = null) => {
    if (!scoreDataToSave) {
      console.warn('⚠️ No score data available - cannot save hand');
      return false;
    }

    // Prevent duplicate saves - multiple code paths may try to save the same hand
    if (handSaveInProgressRef.current) {
      console.log('⏳ Hand save already in progress - skipping duplicate');
      return false;
    }

    try {
      handSaveInProgressRef.current = true;
      console.log('💾 Saving hand to session...');

      // Check current session status to ensure we have an active session
      const sessionStatusResponse = await fetch(`${API_URL}/api/session/status`, {
        headers: { ...getSessionHeaders() }
      });

      if (sessionStatusResponse.ok) {
        const currentSession = await sessionStatusResponse.json();
        console.log('Session status:', currentSession);

        if (currentSession.active) {
          // Build request body with contract data as fallback for backend
          const requestBody = {
            score_data: scoreDataToSave,
            auction_history: auctionToSave.map(a => typeof a === 'object' ? a.bid : a)
          };

          // Include contract data if available (fallback for when backend play_state is lost)
          if (contractInfo) {
            requestBody.contract_data = {
              level: contractInfo.level,
              strain: contractInfo.strain,
              declarer: contractInfo.declarer,
              doubled: contractInfo.doubled || 0
            };
          }

          // Save the hand to session_hands table
          const response = await fetch(`${API_URL}/api/session/complete-hand`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
            body: JSON.stringify(requestBody)
          });

          if (response.ok) {
            const result = await response.json();
            console.log('✅ Hand saved successfully to database');
            console.log('Session updated:', result.session);
            console.log('Hand ID:', result.hand_id);
            setSessionData({ active: true, session: result.session });

            // Store hand_id for Review Hand functionality
            if (result.hand_id) {
              setLastSavedHandId(result.hand_id);
            }

            // Update vulnerability for next hand (dealer/vuln rotation continues)
            setVulnerability(result.session.vulnerability);
            return true;
          } else {
            const errorText = await response.text();
            console.error('❌ Failed to save hand:', errorText);
          }
        } else {
          console.warn('⚠️ No active session - starting new session...');
          // Try to start a new session
          const sessionResponse = await fetch(`${API_URL}/api/session/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
            body: JSON.stringify({ user_id: userId, session_type: 'continuous' })
          });
          if (sessionResponse.ok) {
            const newSession = await sessionResponse.json();
            setSessionData(newSession);
            console.log('✅ New session started - hand will be saved on next attempt');
          }
        }
      } else {
        console.error('❌ Failed to check session status');
      }
    } catch (err) {
      console.error('❌ Error saving hand to session:', err);
    } finally {
      // Reset the save guard after a short delay to allow for next hand
      setTimeout(() => {
        handSaveInProgressRef.current = false;
      }, 1000);
    }
    return false;
  }, [userId]);

  const handleCloseScore = async () => {
    // Hand should already be saved by now (saved immediately when play ended)
    // But if not saved yet for some reason, try again
    if (scoreData && !scoreData._saved) {
      await saveHandToDatabase(scoreData, auction, playState?.contract);
    }
    setScoreData(null);
  };

  // Review page handlers - for full-screen play/bid analysis
  const handleOpenReviewPage = (handId, type = 'play', handList = []) => {
    savedScrollPositionRef.current = window.scrollY;
    setReviewPageHandId(handId);
    setReviewPageType(type);
    setHandReviewSource('dashboard'); // Coming from My Progress dashboard

    // Setup navigation if hand list provided
    if (handList.length > 0) {
      setReviewHandList(handList);
      const idx = handList.findIndex(h => (h.id || h.hand_id) === handId);
      setReviewCurrentIndex(idx >= 0 ? idx : 0);
    } else {
      setReviewHandList([]);
      setReviewCurrentIndex(0);
    }

    setShowReviewPage(true);
  };

  const handleCloseReviewPage = () => {
    const scrollY = savedScrollPositionRef.current;
    setShowReviewPage(false);
    setReviewPageHandId(null);
    setReviewHandList([]);
    setReviewCurrentIndex(0);
    setHandReviewSource(null);
    // Restore scroll position after React re-renders the previous view
    requestAnimationFrame(() => {
      window.scrollTo(0, scrollY);
    });
  };

  const handleNavigateReviewHand = (direction) => {
    if (reviewHandList.length === 0) return;
    const newIndex = reviewCurrentIndex + direction;
    if (newIndex >= 0 && newIndex < reviewHandList.length) {
      setReviewCurrentIndex(newIndex);
      const hand = reviewHandList[newIndex];
      setReviewPageHandId(hand.id || hand.hand_id);
    }
  };

  /**
   * Handle claim button click - opens the claim modal
   */
  const handleClaim = () => {
    if (!playState) return;

    // Reset modal state and open
    setClaimValidationResult(null);
    setClaimValidating(false);
    setShowClaimModal(true);
  };

  /**
   * Handle claim modal close
   */
  const handleClaimModalClose = () => {
    // If claim was accepted (valid result), close immediately
    // The score modal will be shown automatically
    setShowClaimModal(false);
    setClaimValidationResult(null);
    setClaimValidating(false);
  };

  /**
   * Submit claim to backend - validates and completes hand if valid
   */
  const handleSubmitClaim = async (claimedTricks) => {
    setClaimValidating(true);
    setClaimValidationResult(null);

    try {
      const response = await fetch(`${API_URL}/api/complete-with-claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({ claimed_tricks: claimedTricks })
      });

      const result = await response.json();

      if (!response.ok) {
        setClaimValidationResult({
          valid: false,
          message: result.error || 'Failed to validate claim',
          claimed: claimedTricks,
          max_possible: null,
          dds_available: false
        });
        setClaimValidating(false);
        return;
      }

      if (result.valid) {
        // Claim accepted! Close modal and show score
        setShowClaimModal(false);
        setClaimValidationResult(null);
        setClaimValidating(false);

        // Save hand to database (backend already updated play state with claimed tricks)
        const saved = await saveHandToDatabase(result, auction, playState?.contract);
        if (saved) result._saved = true;

        // Set score data to trigger the result overlay
        setScoreData(result);
      } else {
        // Claim rejected - show result in modal
        setClaimValidationResult({
          valid: false,
          message: result.message,
          claimed: result.claimed,
          max_possible: result.max_possible,
          dds_available: result.dds_available
        });
        setClaimValidating(false);
      }

    } catch (err) {
      console.error('Error submitting claim:', err);
      setClaimValidationResult({
        valid: false,
        message: 'Failed to validate claim. Please try again.',
        claimed: claimedTricks,
        max_possible: null,
        dds_available: false
      });
      setClaimValidating(false);
    }
  };

  // ========== END CARD PLAY FUNCTIONS ==========

  const dealNewHand = async () => {
    // Reset save guard for new hand
    handSaveInProgressRef.current = false;

    // Capture current request ID to detect if a convention was loaded during fetch
    const requestId = dealRequestIdRef.current;

    try {
      const response = await fetch(`${API_URL}/api/deal-hands`, { headers: { ...getSessionHeaders() } });
      if (!response.ok) throw new Error("Failed to deal hands.");
      const data = await response.json();

      // Check if request was invalidated by a convention load during fetch
      // This prevents race condition where random deal overwrites convention
      if (dealRequestIdRef.current !== requestId) {
        console.log('🚫 Random deal cancelled - convention was loaded during fetch');
        return;
      }

      // Backend returns next_bidder — use it to decide if AI should start bidding
      const shouldAiBid = data.next_bidder && data.next_bidder !== 'South';

      // Store DD table if provided (production only)
      setDdTable(data.dd_table || null);

      resetAuction(data, !shouldAiBid);
      setIsInitializing(false); // Ensure we're not in initializing state for manual deals
      setActiveConvention(null); // Exit convention mode when dealing random hand

      // Track deal hand event
      trackDealHand('random');
    } catch (err) { setError("Could not connect to server to deal."); }
  };

  const playRandomHand = async () => {
    // Reset save guard for new hand
    handSaveInProgressRef.current = false;

    // Set game phase to 'playing' IMMEDIATELY to prevent showing PlayWorkspace options menu
    // The PlayWorkspace options menu shows when gamePhase === 'bidding' && !hand?.length
    setGamePhase('playing');

    // Clear previous play state immediately to prevent stale data display
    setPlayState(null);
    setDummyHand(null);
    setDeclarerHand(null);
    setScoreData(null);
    setLastTrick(null);
    setShowLastTrick(false);
    setLastSavedHandId(null);  // Clear for new hand

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
      // Note: showAllHands persists user preference - don't force hide
      setDisplayedMessage(`Contract: ${data.contract}. The AI bid all 4 hands. Opening leader: ${data.opening_leader}`);

      // Fetch initial play state
      const stateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });
      if (stateResponse.ok) {
        const state = await stateResponse.json();
        setPlayState(state);

        // === BUG FIX: Use visible_hands from backend ===
        // Only set declarerHand when declarer is NOT South to avoid duplication
        const declarerPos = state.contract.declarer;
        if (declarerPos !== 'S' && state.visible_hands && state.visible_hands[declarerPos]) {
          const declarerCards = state.visible_hands[declarerPos].cards || [];
          console.log('👁️ Setting declarer hand from visible_hands (playRandomHand):', {
            declarerPos,
            cardCount: declarerCards.length
          });
          setDeclarerHand(declarerCards);
        } else if (declarerPos !== 'S' && state.dummy === 'S') {
          // FALLBACK: Old method
          console.log('⚠️ visible_hands not available, falling back to /api/get-all-hands');
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            const declarerCards = handsData.hands[declarerPos]?.hand || [];
            setDeclarerHand(declarerCards);
          }
        }

        // === Update South's hand from visible_hands (only if non-empty) ===
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || state.visible_hands['S'];
          if (Array.isArray(southCards) && southCards.length > 0) {
            console.log('👁️ Updating South hand from visible_hands (playRandomHand):', {
              cardCount: southCards.length
            });
            setHand(southCards);
          }
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
        // Only set declarerHand when declarer is NOT South to avoid duplication
        const declarerPos = state.contract.declarer;
        if (declarerPos !== 'S' && state.visible_hands && state.visible_hands[declarerPos]) {
          const declarerCards = state.visible_hands[declarerPos].cards || [];
          console.log('👁️ Setting declarer hand from visible_hands (replayCurrentHand):', {
            declarerPos,
            cardCount: declarerCards.length
          });
          setDeclarerHand(declarerCards);
        } else if (declarerPos !== 'S' && state.dummy === 'S') {
          // FALLBACK: Old method
          console.log('⚠️ visible_hands not available, falling back to /api/get-all-hands');
          const handsResponse = await fetch(`${API_URL}/api/get-all-hands`, { headers: { ...getSessionHeaders() } });
          if (handsResponse.ok) {
            const handsData = await handsResponse.json();
            const declarerCards = handsData.hands[declarerPos]?.hand || [];
            setDeclarerHand(declarerCards);
          }
        }

        // === Update South's hand from visible_hands (only if non-empty) ===
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || state.visible_hands['S'];
          if (Array.isArray(southCards) && southCards.length > 0) {
            console.log('👁️ Updating South hand from visible_hands (replayCurrentHand):', {
              cardCount: southCards.length
            });
            setHand(southCards);
          }
        }
      }

      // Reset to play phase start
      setGamePhase('playing');
      // Note: showAllHands persists user preference - don't force hide
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

  // Get short convention name for display (e.g., "Jacoby Transfer Test" -> "Jacoby")
  const getShortConventionName = (fullName) => {
    if (!fullName) return '';
    // Remove common suffixes and simplify
    const shortNames = {
      'Jacoby Transfer Test': 'Jacoby',
      'Stayman Test': 'Stayman',
      'Blackwood Test': 'Blackwood',
      'Preemptive Test': 'Preempt',
      'Takeout Double Test': 'Takeout Double',
      'Negative Double Test': 'Negative Double',
      'Michaels Cuebid Test': 'Michaels',
      'Unusual 2NT Test': 'Unusual 2NT',
      'Fourth Suit Forcing Test': 'Fourth Suit',
      'Splinter Test': 'Splinter',
    };
    return shortNames[fullName] || fullName.replace(' Test', '');
  };

  // Load scenario by name (for convention grid)
  // In room mode, also updates room settings for sync to guest
  const loadScenarioByName = async (scenarioName) => {
    if (!scenarioName) return;

    // ROOM MODE: Update room settings so guest sees the drill
    if (inRoom && isHost) {
      try {
        const { updateSettings } = { updateSettings: async (s) => {
          const response = await fetchWithSession(`${API_URL}/api/room/settings`, {
            method: 'POST',
            body: JSON.stringify(s),
          });
          return response.json();
        }};
        await updateSettings({
          deal_type: 'convention',
          convention_filter: scenarioName,
        });
        console.log('🎯 Room: Set drill focus to', scenarioName);
        setActiveConvention(scenarioName);
        return; // Don't load scenario directly - let host deal via status bar
      } catch (err) {
        console.error('Failed to update room settings:', err);
      }
    }

    // Non-room mode: Load scenario directly
    // Invalidate any pending random deal (prevents race condition)
    dealRequestIdRef.current++;

    try {
      const response = await fetch(`${API_URL}/api/load-scenario`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({ name: scenarioName })
      });
      if (!response.ok) throw new Error("Failed to load scenario.");
      const data = await response.json();

      // Check if AI should bid first (same logic as dealNewHand)
      const shouldAiBid = data.next_bidder && data.next_bidder !== 'South';
      resetAuction(data, !shouldAiBid);
      setIsInitializing(false);
      setActiveConvention(scenarioName); // Enter convention mode

      // Track scenario selection
      trackScenarioSelected(scenarioName);
      trackDealHand('scenario');
    } catch (err) { setError("Could not load scenario from server."); }
  };

  // Exit convention mode and return to random hands
  const exitConventionMode = () => {
    setActiveConvention(null);
    dealNewHand();
  };

  const handleReplayHand = () => {
    if (!initialDeal) return;
    resetAuction(initialDeal, true); // Skip initial AI bidding - wait for proper turn
  };

  // Fetch scenarios (only once on mount)
  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const response = await fetch(`${API_URL}/api/scenarios`, { headers: { ...getSessionHeaders() } });
        const data = await response.json();
        setScenarioList(data.scenarios);
        setScenariosByLevel(data.scenarios_by_level);
      } catch (err) { console.error("Could not fetch scenarios", err); }
    };
    fetchScenarios();
  }, []);

  // Start or resume session AFTER auth is loaded AND userId is available
  useEffect(() => {
    // Wait for auth to finish loading before starting session
    if (authLoading) return;

    // Don't start a session until we have a real userId (from login or guest)
    // Without this guard, userId defaults to 1 which causes 500 errors.
    // Keep isInitializing=true so AI bidding stays blocked until session starts.
    if (!userId) return;

    const startSession = async () => {
      try {
        console.log(`🔄 Starting session for user_id: ${userId}`);

        const sessionResponse = await fetch(`${API_URL}/api/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
          body: JSON.stringify({ user_id: userId, session_type: 'continuous' })
        });

        if (!sessionResponse.ok) {
          console.error(`❌ Session start failed with status ${sessionResponse.status}`);
          setIsInitializing(false);
          return;
        }

        const sessionData = await sessionResponse.json();
        setSessionData(sessionData);

        // Use dealer and vulnerability from session
        if (sessionData.session?.vulnerability) {
          setVulnerability(sessionData.session.vulnerability);
        }

        console.log(`✅ Session ${sessionData.resumed ? 'resumed' : 'started'} for user ${userId}: ${sessionData.message}`);
      } catch (err) {
        console.error("Could not start session", err);
      }

      setIsInitializing(false);
    };
    startSession();
  }, [authLoading, userId]);

  // calculateExpectedBidder removed — backend is now the single source of
  // truth for whose turn it is to bid (via next_bidder in API responses).

  // Helper function to commit a bid after all validations/confirmations
  const commitBid = async (bid, feedbackData = null) => {
    // DEBUG: Log bid submission
    console.log('🎯 COMMITTING USER BID:', {
      bid: bid,
      userId: userId,
      auctionLength: auction.length,
      timestamp: new Date().toISOString()
    });

    // Clear any pending hint suggestion
    setSuggestedBid(null);
    setDisplayedMessage('...');
    const newAuction = [...auction, { bid: bid, explanation: 'Your bid.', player: 'South' }];

    // Optimistic next-bidder: clockwise from current position.
    // The evaluate-bid response will carry the authoritative value.
    const dealerIdx = players.indexOf(dealer);
    const optimisticNextBidder = players[(dealerIdx + newAuction.length) % 4];

    // Use flushSync to ensure user's bid and next bidder render together
    flushSync(() => {
      setAuction(newAuction);
      setNextBidder(optimisticNextBidder);
    });

    // Enable AI bidding after user's bid is rendered
    setIsAiBidding(true);

    // If we already have feedback data (from pre-evaluation), use it
    // BUT we must still record the bid on the backend — pre-evaluation used
    // record_bid=false so state.auction_history is missing this bid.
    if (feedbackData) {
      try {
        const recordResponse = await fetch(`${API_URL}/api/evaluate-bid`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
          body: JSON.stringify({
            user_bid: bid,
            record_only: true
          })
        });
        const recordData = await recordResponse.json();
        if (recordData.next_bidder) {
          setNextBidder(recordData.next_bidder);
        }
        if (recordData.beliefs) setBeliefs(recordData.beliefs);
      } catch (err) {
        console.error('❌ Failed to record bid on backend:', err);
        // Fall through — optimistic nextBidder is already set
      }
      setLastUserBid(bid);
      // Only show bid evaluation feedback in coached mode
      if (sessionMode === 'coached') {
        setBidFeedback(feedbackData.feedback || null);
        setDisplayedMessage(feedbackData.user_message || feedbackData.explanation || 'Bid recorded.');
      } else {
        setBidFeedback(null);
        setDisplayedMessage('Bid recorded.');
      }
      return;
    }

    // Otherwise, fetch feedback (this path is used when governor is bypassed or disabled)
    try {
      const feedbackResponse = await fetch(`${API_URL}/api/evaluate-bid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          user_bid: bid,
          auction_history: auction.map(a => a.bid),
          current_player: 'South',
          user_id: userId,
          session_id: sessionData?.session?.id,
          feedback_level: 'intermediate',
          use_v2_schema: useV2Schema
        })
      });

      const data = await feedbackResponse.json();

      if (feedbackResponse.status === 400) {
        console.warn('⚠️ evaluate-bid returned 400:', data.error);
        // Handle all 400 errors - session state is corrupted/missing
        const errorMsg = data.session_expired
          ? "Session expired. Please click 'Deal New Hand' to continue."
          : data.error?.includes('Deal has not been made')
          ? "Session expired. Please deal a new hand to continue."
          : data.error?.includes('not available')
          ? "Session data lost. Please deal a new hand to continue."
          : `Server error: ${data.error || 'Unknown error'}`;
        setError(errorMsg);
        setDisplayedMessage(errorMsg);
        setBidFeedback(null);
        setIsAiBidding(false);
        return;
      }
      // Update nextBidder from authoritative backend response
      if (data.next_bidder) {
        setNextBidder(data.next_bidder);
      }
      if (data.beliefs) setBeliefs(data.beliefs);
      setLastUserBid(bid);

      // Track user bid event
      const bidScore = data.feedback?.score ?? null;
      trackBidMade(bid, true, bidScore);

      // Only show bid evaluation feedback in coached mode
      if (sessionMode === 'coached') {
        setBidFeedback(data.feedback || null);
        setDisplayedMessage(data.user_message || data.explanation || 'Bid recorded.');
      } else {
        setBidFeedback(null);
        setDisplayedMessage('Bid recorded.');
      }
    } catch (err) {
      console.error('❌ Error evaluating bid:', err);
      setBidFeedback(null);
      setDisplayedMessage('Could not get feedback from the server.');
    }
  };

  // Fetch AI's suggested bid for "What Should I Bid?" button
  const handleRequestHint = async () => {
    // Determine user's position and check if it's their turn
    const userPosition = inRoom ? (isHost ? 'South' : 'North') : 'South';
    const canRequestHint = inRoom ? isMyTurn : (nextBidder === 'South');

    if (!canRequestHint || isAuctionOver(displayAuction)) {
      return;
    }

    try {
      setSuggestedBid({ loading: true });
      const response = await fetch(`${API_URL}/api/get-next-bid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
        body: JSON.stringify({
          auction_history: displayAuction.map(a => a.bid),
          current_player: userPosition,
          vulnerability: displayVulnerability,
          explanation_detail: 'detailed',
          hint_only: true  // Don't record this bid in session state
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get hint');
      }

      const data = await response.json();
      setSuggestedBid({
        bid: data.bid,
        explanation: data.explanation,
        loading: false
      });

      // Also enable hint mode so feedback shows after they bid
      if (!hintModeEnabled) {
        setHintModeEnabled(true);
      }
    } catch (err) {
      console.error('❌ Error getting hint:', err);
      setSuggestedBid({ error: 'Could not get suggestion', loading: false });
    }
  };

  const handleUserBid = async (bid) => {
    // ROOM MODE: Route to room bid submission
    if (inRoom) {
      if (!isMyTurn) {
        setError("Not your turn!");
        return;
      }
      setSuggestedBid(null);
      const result = await submitRoomBid(bid);
      if (!result.success) {
        setError(result.error || 'Failed to submit bid');
      }
      return;
    }

    // CRITICAL VALIDATION: Check if auction is already complete
    if (isAuctionOver(auction)) {
      console.warn('🚫 User tried to bid after auction ended');
      return;
    }

    // CRITICAL VALIDATION: Check if it's actually South's turn (backend-authoritative)
    if (nextBidder !== 'South') {
      const errorMsg = `⚠️ Not your turn! Waiting for ${nextBidder} to bid.`;
      setError(errorMsg);
      setDisplayedMessage(errorMsg);
      console.warn('🚫 User tried to bid out of turn:', { nextBidder });
      return;
    }

    // Clear any previous errors
    setError('');

    if (nextBidder !== 'South' || isAiBidding) return;

    // Governor Safety Guard: Only in coached mode with hints enabled, pre-evaluate bid to check for critical issues
    if (hintModeEnabled && sessionMode === 'coached') {
      setDisplayedMessage('Evaluating bid...');

      try {
        // Pre-evaluate the bid BEFORE committing it.
        // record_bid: false so governor-blocked bids aren't recorded in session state.
        const feedbackResponse = await fetch(`${API_URL}/api/evaluate-bid`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
          body: JSON.stringify({
            user_bid: bid,
            auction_history: auction.map(a => a.bid),
            current_player: 'South',
            user_id: userId,
            session_id: sessionData?.session?.id,
            feedback_level: 'intermediate',
            use_v2_schema: useV2Schema,
            record_bid: false
          })
        });

        const feedbackData = await feedbackResponse.json();

        // Handle non-200 responses (400, 500, etc.)
        if (!feedbackResponse.ok) {
          const isSessionExpired = feedbackData.session_expired ||
            feedbackData.error?.includes('Deal has not been made') ||
            feedbackData.error?.includes('not available');

          if (isSessionExpired) {
            console.warn('⚠️ Server session lost - deal not found. User should deal new hands.');
            setError("Session expired. Please click 'Deal New Hand' to continue.");
            return;
          }
          console.warn(`⚠️ Pre-evaluation returned ${feedbackResponse.status}:`, feedbackData.error);
          throw new Error(feedbackData.error || 'Pre-evaluation failed');
        }

        // DEBUG: Log response from evaluate-bid
        console.log('✅ EVALUATE-BID RESPONSE:', {
          user_bid: bid,
          feedback: feedbackData,
          impact: feedbackData.feedback?.impact,
          stored: feedbackData.decision_id ? 'YES' : 'UNKNOWN'
        });

        // Check if this is a Governor-blocked bid (critical or significant impact)
        const impact = feedbackData.feedback?.impact;
        if (impact === 'critical' || impact === 'significant') {
          console.log('🛡️ Governor blocking bid:', bid, 'Impact:', impact);
          // Store pending bid and show confirmation dialog
          setPendingBid(bid);
          setPendingBidFeedback(feedbackData);
          setShowGovernorDialog(true);
          setDisplayedMessage('');
          return; // Don't commit yet - wait for user confirmation
        }

        // No blocking needed - commit the bid with the feedback we already have
        await commitBid(bid, feedbackData);

      } catch (err) {
        console.error('❌ Error pre-evaluating bid:', err);
        // On error, fall through and commit the bid anyway
        await commitBid(bid);
      }
    } else {
      // Hint mode disabled - commit bid directly (original flow)
      await commitBid(bid);
    }
  };

  // Handler for when user confirms proceeding with a Governor-blocked bid
  const handleGovernorProceed = async () => {
    if (pendingBid) {
      console.log('🛡️ Governor override: User proceeding with blocked bid:', pendingBid);
      await commitBid(pendingBid, pendingBidFeedback);
    }
    // Clear the pending state
    setPendingBid(null);
    setPendingBidFeedback(null);
    setShowGovernorDialog(false);
  };

  // Handler for when user cancels a Governor-blocked bid
  const handleGovernorCancel = () => {
    console.log('🛡️ Governor: User chose different bid');
    setPendingBid(null);
    setPendingBidFeedback(null);
    setShowGovernorDialog(false);
    setDisplayedMessage('Choose a different bid.');
  };

  const handleBidClick = (bidObject) => {
    // Set selected bid for CoachPanel explanation display
    setSelectedBid(bidObject);
  };

  // ── AI BIDDING LOOP ──
  // Driven by `nextBidder` (set from backend API responses).
  // When nextBidder is an AI player and isAiBidding is true, this effect
  // calls /api/get-next-bid.  The response includes `next_bidder` which
  // is written into state, re-triggering this effect for the next turn.
  useEffect(() => {
    console.log('🤖 AI BIDDING USEEFFECT:', {
      isInitializing, isAiBidding, nextBidder, auctionLength: auction.length, gamePhase, inRoom, roomError
    });

    // ROOM MODE: Skip local AI bidding UNLESS there's a room error (fallback to local)
    // When room polling fails (e.g., server restart), continue with local AI
    if (inRoom && !roomError) return;

    if (isInitializing) return;

    if (isAuctionOver(auction)) {
      if (isAiBidding) setIsAiBidding(false);
      return;
    }

    // SAFETY: Prevent runaway auctions (max 60 bids — far beyond any legal auction)
    if (auction.length >= 60) {
      console.error('🛑 Runaway auction detected:', auction.length, 'bids. Stopping AI bidding.');
      setIsAiBidding(false);
      return;
    }

    // Backend tells us whose turn it is
    if (!nextBidder) return;

    if (nextBidder === 'South') {
      if (isAiBidding) setIsAiBidding(false);
      return;
    }

    // It's an AI player's turn
    if (!isAiBidding) return;

    // Prevent concurrent AI bids
    if (isAiBiddingInProgress.current) return;

    // Snapshot nextBidder at effect time for stale-check
    const expectedBidder = nextBidder;
    console.log('✅ Starting AI turn for:', expectedBidder);

    const runAiTurn = async () => {
      isAiBiddingInProgress.current = true;
      await new Promise(resolve => setTimeout(resolve, 500));

      try {
        // Stale-check: if nextBidder changed during delay, abort
        // (nextBidder is captured via closure — this check uses the value
        //  from the render that scheduled this effect)
        if (nextBidder !== expectedBidder) {
          isAiBiddingInProgress.current = false;
          return;
        }

        console.log('📡 Fetching AI bid for:', expectedBidder);
        const response = await fetch(`${API_URL}/api/get-next-bid`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
          body: JSON.stringify({
            auction_history: auction.map(a => a.bid),
            current_player: expectedBidder,
            dealer: dealer,
            use_v2_schema: useV2Schema
          })
        });

        if (response.status === 400) {
          const errorData = await response.json();
          if (errorData.error?.includes('Deal has not been made')) {
            throw new Error("Session expired. Please deal a new hand to continue.");
          }
        }
        if (!response.ok) throw new Error("AI failed to get bid.");

        const data = await response.json();
        console.log('✅ AI bid received:', data);

        // Update auction + next bidder from backend response
        // NOTE: Do NOT use flushSync here. flushSync synchronously re-renders
        // and fires the useEffect for the new nextBidder while
        // isAiBiddingInProgress is still true, causing the next AI turn to
        // be skipped. Regular setState batches updates; the guard is released
        // before the next render cycle runs effects.
        setAuction(prev => [...prev, data]);
        setNextBidder(data.next_bidder || null);
        if (data.beliefs) setBeliefs(data.beliefs);

        // Track AI bid event
        trackBidMade(data.bid, false, null);

        isAiBiddingInProgress.current = false;
        console.log('✅ Auction updated, next_bidder:', data.next_bidder);
      } catch (err) {
        console.error('❌ AI bidding error:', err);
        setError("AI bidding failed. Is the server running?");
        setIsAiBidding(false);
        isAiBiddingInProgress.current = false;
      }
    };

    runAiTurn();
  }, [nextBidder, isAiBidding, auction, isInitializing, dealer, gamePhase, inRoom, roomError]);

  // Trigger AI bidding after initialization completes (if it's not South's turn)
  // ROOM MODE: Skip UNLESS there's an error (fallback to local)
  useEffect(() => {
    if (showModeSelector) return;
    if (inRoom && !roomError) return;  // Room mode: bidding handled by room polling (unless error)
    if (!isInitializing && gamePhase === 'bidding' && auction.length === 0
        && !hasTriggeredInitialBid.current && nextBidder && nextBidder !== 'South') {
      console.log('▶️ Starting AI bidding after init, nextBidder:', nextBidder);
      hasTriggeredInitialBid.current = true;
      setIsAiBidding(true);
    }
  }, [isInitializing, gamePhase, auction.length, nextBidder, showModeSelector, inRoom, roomError]);

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

    // AbortController prevents stale invocations from racing with fresh ones
    const abortController = new AbortController();
    const signal = abortController.signal;

    const runAiPlay = async () => {
      try {
        if (signal.aborted) return;
        console.log('🎬 AI play loop RUNNING...');
        // Get current play state
        if (signal.aborted) return;
        const stateResponse = await fetch(`${API_URL}/api/get-play-state`, { headers: { ...getSessionHeaders() } });

        // Handle session state loss (e.g., server restart)
        if (stateResponse.status === 400) {
          const errorData = await stateResponse.json();
          if (errorData.error && (errorData.error.includes('No play in progress') || errorData.error.includes('Deal has not been made'))) {
            console.warn('⚠️ Server session lost - play state not found. User should deal new hands.');
            setError("Session expired. Please deal a new hand to continue.");
            setIsPlayingCard(false);
            return;
          }
        }

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
        // IMPORTANT: Only set declarerHand when declarer is NOT South to avoid duplication.
        // When S is declarer, the user's own hand is managed by the `hand` state.
        if (declarerPos !== 'S' && state.visible_hands && state.visible_hands[declarerPos]) {
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

        // === Update South's hand from visible_hands (only if non-empty) ===
        if (state.visible_hands && state.visible_hands['S']) {
          const southCards = state.visible_hands['S'].cards || state.visible_hands['S'];
          if (Array.isArray(southCards) && southCards.length > 0) {
            console.log('👁️ Updating South hand from visible_hands (AI loop):', {
              cardCount: southCards.length
            });
            setHand(southCards);
          }
        }

        // Check if play is complete (13 tricks)
        const totalTricks = Object.values(state.tricks_won).reduce((a, b) => a + b, 0);
        if (totalTricks === 13) {
          console.log('🏁 All 13 tricks complete! Fetching final score...');
          // Play complete - calculate score
          if (signal.aborted) return;
          const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
            body: JSON.stringify({ vulnerability: vulnerability })
          });

          if (scoreResponse.ok) {
            const scoreData = await scoreResponse.json();
            console.log('✅ Score calculated:', scoreData);
            // Save hand to database immediately - pass contract info as fallback
            const saved = await saveHandToDatabase(scoreData, auction, playState?.contract);
            if (saved) scoreData._saved = true;
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

        if (signal.aborted) return;
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

        // Track AI card play
        trackCardPlayed(false);

        // Fetch updated play state to show the card that was just played
        if (signal.aborted) return;
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
          if (signal.aborted) return;
          await fetch(`${API_URL}/api/clear-trick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }
          });

          // Fetch updated play state to show empty trick
          if (signal.aborted) return;
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
              if (signal.aborted) return;
              const scoreResponse = await fetch(`${API_URL}/api/complete-play`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getSessionHeaders() },
                body: JSON.stringify({ vulnerability: vulnerability })
              });

              if (scoreResponse.ok) {
                const scoreData = await scoreResponse.json();
                console.log('✅ Score calculated after AI play:', scoreData);
                // Save hand to database immediately - pass contract info as fallback
                const saved = await saveHandToDatabase(scoreData, auction, playState?.contract);
                if (saved) scoreData._saved = true;
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
            if (isNextPlayerUserControlled(clearedState)) {
              console.log('⏸️ STOPPING - Next player after trick clear is user-controlled');
              setIsPlayingCard(false);
              return;
            }

            // CRITICAL: If E or W should play next (AI positions), explicitly continue
            if (clearedState.next_to_play === 'E' || clearedState.next_to_play === 'W') {
              console.log(`🤖 AI position ${clearedState.next_to_play} should lead - ensuring AI loop continues`);
            }
          }

          console.log('🔁 Continuing to next trick...');
          // Continue to next trick after delay
          // Reset flag first to ensure useEffect triggers
          // Use 200ms delay to ensure React state updates have propagated
          keepAiLoopAlive.current = true; // Signal cleanup to NOT cancel timeout
          setIsPlayingCard(false);
          aiPlayTimeoutRef.current = setTimeout(() => {
            console.log('⏰ Timeout fired - restarting AI play loop');
            keepAiLoopAlive.current = false; // Reset flag
            setIsPlayingCard(true);
          }, 200);
        } else {
          console.log('🔁 Continuing AI play loop (trick not complete)...');
          // Trick not complete - continue playing quickly
          // Reset flag first to ensure useEffect triggers
          keepAiLoopAlive.current = true; // Signal cleanup to NOT cancel timeout
          setIsPlayingCard(false);
          aiPlayTimeoutRef.current = setTimeout(() => {
            console.log('⏰ Timeout fired - continuing AI play (mid-trick)');
            keepAiLoopAlive.current = false; // Reset flag
            setIsPlayingCard(true);
          }, 150);
        }

      } catch (err) {
        console.error('Error in AI play loop:', err);
        setError(`AI play failed: ${err.message || 'Unknown error'}`);
        setIsPlayingCard(false);
      }
    };

    runAiPlay();

    // Cleanup function to clear pending timeouts when effect re-runs or component unmounts
    return () => {
      // Only clear timeout if we're NOT intentionally keeping the loop alive
      // This allows us to toggle isPlayingCard (false -> true) without killing the pending timeout
      if (keepAiLoopAlive.current) {
        console.log('🧘 Keeping AI loop alive during effect cleanup');
        // Reset flag for next time, but DON'T clear timeout
        keepAiLoopAlive.current = false;
      } else {
        if (aiPlayTimeoutRef.current) {
          console.log('🧹 Clearing AI loop timeout');
          clearTimeout(aiPlayTimeoutRef.current);
          aiPlayTimeoutRef.current = null;
        }
      }
    };
  }, [gamePhase, isPlayingCard, vulnerability]);

  // Show all hands during bidding phase only when toggle is enabled
  const shouldShowHands = gamePhase === 'bidding' && showAllHands;

  // Debug logging for card display
  useEffect(() => {
    console.log('🎨 Render state:', {
      shouldShowHands,
      showAllHands,
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
  }, [shouldShowHands, showAllHands, allHands]);

  // Determine current active module for navigation
  const getCurrentModule = () => {
    if (showLearningFlowsHub) return 'lab';
    if (showLearningMode) return 'learning';
    if (showLearningDashboard) return 'progress';
    if (currentWorkspace === 'play') return 'play';
    // When in bid workspace but playing phase, show play module active
    if (currentWorkspace === 'bid') {
      return gamePhase === 'playing' ? 'play' : 'bid';
    }
    return null; // On home/mode selector
  };

  // Handle navigation from TopNavigation
  const handleNavModuleSelect = (modeId) => {
    // Guard: protected features require registration for guests
    if (isGuest && requiresRegistration(modeId)) {
      promptForRegistration();
      return;
    }

    // Close any open overlays first
    setShowLearningMode(false);
    setShowLearningDashboard(false);
    setShowModeSelector(false);
    setShowLearningFlowsHub(false);

    // Handle LAB mode (localhost-only learning flows preview)
    if (modeId === 'lab') {
      setShowLearningFlowsHub(true);
      return;
    }

    // Navigate to selected module
    handleModeSelect(modeId);
  };

  return (
    <div className="app-container">
      {/* Top Navigation - Always visible */}
      {isAuthenticated && (
        <TopNavigation
          currentModule={getCurrentModule()}
          onModuleSelect={handleNavModuleSelect}
          showTitle={!showModeSelector}
        >
          {/* Partner Practice button - dev only (not yet functional in production) */}
          {!inRoom && process.env.NODE_ENV === 'development' && (
            <button
              className="nav-utility-button nav-join-button"
              onClick={() => setShowJoinRoomModal(true)}
              title="Play with a human partner"
              data-testid="partner-practice-button"
            >
              👥 Partner
            </button>
          )}
          {/* Room indicator when in a room */}
          {inRoom && (
            <span className="nav-room-indicator" title={`Room: ${roomCode}`}>
              👥 {roomCode}
            </span>
          )}
          {/* Feedback button - text only */}
          <button
            className="nav-utility-button"
            onClick={() => setShowFeedbackModal(true)}
            title="Send feedback"
            data-testid="feedback-button"
          >
            Feedback
          </button>
          {/* Glossary button - text only */}
          <button
            className="nav-utility-button"
            onClick={() => setShowGlossary(true)}
            title="Bridge terminology glossary"
            data-testid="glossary-button"
          >
            Glossary
          </button>
          {/* User avatar menu */}
          <UserMenu
            onSignInClick={() => setShowLogin(true)}
            onFeedbackClick={() => setShowFeedbackModal(true)}
          />
        </TopNavigation>
      )}

      {/* Welcome Wizard - First-time user experience selection */}
      {/* Shows BEFORE ModeSelector for new users, routes them to appropriate starting point */}
      <WelcomeWizard
        isOpen={isAuthenticated && shouldShowWelcomeWizard}
        onSelectExperience={handleExperienceSelect}
      />

      {/* Mode Selector - Landing Page (shown for returning users or after wizard) */}
      {/* Note: !showLearningFlowsHub guard prevents race condition on LAB navigation from landing page */}
      {showModeSelector && isAuthenticated && !shouldShowWelcomeWizard && !showLearningFlowsHub && (
        <ModeSelector
          onSelectMode={handleModeSelect}
          userName={user?.display_name}
        />
      )}

      {/* Team Practice Lobby - Unmount when game is active (View Orchestration Rule) */}
      {showTeamPractice && !isRoomGameActive && (
        <RoomLobby
          onBack={() => {
            setShowTeamPractice(false);
            setShowModeSelector(true);
          }}
        />
      )}

      {/* Login Modal - Show when explicitly opened OR when not authenticated (after loading) */}
      {(showLogin || (!isAuthenticated && !authLoading)) && (
        <SimpleLogin onClose={() => {
          setShowLogin(false);
          // If still not authenticated after closing, they chose to be guest
        }} />
      )}

      {/* Registration Prompt - appears after guest plays a few hands */}
      {showRegistrationPrompt && (
        <RegistrationPrompt
          message="You're making great progress! Create an account to save your results and track your improvement."
          onClose={() => dismissRegistrationPrompt(false)}
        />
      )}

      {/* Join Room Modal */}
      <JoinRoomModal
        isOpen={showJoinRoomModal}
        onClose={() => setShowJoinRoomModal(false)}
        onJoined={() => {
          setShowModeSelector(false);
          setShowTeamPractice(true);
        }}
      />

      {/* Room Status Bar - Fixed 40px bar at top when in any room */}
      {inRoom && <RoomStatusBar />}

      {/* Room Waiting State - Guest waiting for host to deal (only when NOT game active) */}
      {isWaitingForDeal && !isRoomGameActive && <RoomWaitingState />}

      {/* Glossary Drawer */}
      <GlossaryDrawer
        isOpen={showGlossary}
        onClose={() => setShowGlossary(false)}
      />

      {/* Session Score Panel */}
      <SessionScorePanel sessionData={sessionData} />

      {/* Learning Flows Hub - localhost only preview */}
      {/* key prop forces remount to reset activeFlow state when reopening */}
      {showLearningFlowsHub && (
        <LearningFlowsHub key={Date.now()} onClose={() => setShowLearningFlowsHub(false)} />
      )}

      {/* Play Workspace - Show options when entering play mode (before playing) */}
      {currentWorkspace === 'play' && gamePhase === 'bidding' && !hand?.length && (
        <PlayWorkspace
          onNewHand={playRandomHand}
          onPlayLastBid={startPlayPhase}
          onReplayLast={replayCurrentHand}
          hasLastBidHand={isAuctionOver(displayAuction)}
          hasLastPlayedHand={!!initialDeal}
          isPlaying={false}
        />
      )}

      {/* Bidding Workspace Tabs - Only show in old table layout (shouldShowHands mode)
          New layout uses SessionModeBar for mode/deal controls */}
      {currentWorkspace === 'bid' && gamePhase === 'bidding' && shouldShowHands && (
        <BiddingWorkspace
          activeTab={biddingTab}
          onTabChange={handleBiddingTabChange}
          onDealHand={dealNewHand}
          onLoadScenario={loadScenarioByName}
          onReplayHand={handleReplayFromHistory}
          scenarios={scenariosByLevel}
          sessionHands={sessionHands}
          hasActiveHand={hand && hand.length > 0}
        />
      )}

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
                {/* Room mode: Partner is thinking */}
                {inRoom && !isMyTurn && roomGamePhase === 'bidding' && !isAuctionOver(displayAuction) && (
                  <div className="turn-message partner-thinking">
                    💭 Partner is thinking...
                  </div>
                )}
                {/* Solo mode: AI bidding */}
                {!inRoom && isAiBidding && players[nextPlayerIndex] !== 'South' && !isAuctionOver(displayAuction) && (
                  <div className="turn-message">
                    ⏳ Waiting for {players[nextPlayerIndex]} to bid...
                  </div>
                )}
                {/* Both modes: User's turn */}
                {!isAiBidding && canUserBid && !isAuctionOver(displayAuction) && (
                  <div className="turn-message your-turn">
                    ✅ Your turn to bid!
                  </div>
                )}
                <BiddingTable auction={displayAuction} players={players} dealer={displayDealer} nextPlayerIndex={nextPlayerIndex} onBidClick={handleBidClick} isComplete={isAuctionOver(displayAuction)} myPosition={inRoom ? (isHost ? 'S' : 'N') : null} />
                {/* Bid feedback panel - shown when hint mode is enabled */}
                {hintModeEnabled && (
                  <BidFeedbackPanel
                    feedback={bidFeedback}
                    userBid={lastUserBid}
                    isVisible={!!bidFeedback && gamePhase === 'bidding'}
                    onDismiss={() => setBidFeedback(null)}
                    onOpenGlossary={(termId) => setShowGlossary(termId || true)}
                    mode="review"
                  />
                )}
                <BeliefPanel beliefs={displayBeliefs} myHcp={handPoints?.hcp} />
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
        /* BID screen layout per bid-mockup-v2.html */
        <div className="bidding-phase">
          {/* Session Mode Bar - below header */}
          <SessionModeBar
            mode={sessionMode}
            onModeChange={(mode) => {
              setSessionMode(mode);
              trackModeChange(mode);
              // Show/hide coach panel based on mode
              setShowCoachPanel(mode === 'coached');
            }}
            vulnerability={vulnerability}
            dealer={dealer}
            dealSource={activeConvention || 'random'}
            onDealSourceChange={(source) => {
              if (source === 'random') {
                dealNewHand();
              } else {
                loadScenarioByName(source);
              }
            }}
            conventions={Object.values(scenariosByLevel || {}).flat().map(s => s.name)}
          />

          {/* Main content: game column + coach panel using SplitGameLayout */}
          <SplitGameLayout
            isSidebarOpen={sessionMode === 'coached' && showCoachPanel}
            sidebarWidth={350}
            sidebar={
              sessionMode === 'coached' ? (
                <CoachPanel
                  isVisible={true}
                  onClose={() => setShowCoachPanel(false)}
                  beliefs={displayBeliefs}
                  myHcp={handPoints?.hcp}
                  auction={displayAuction}
                  suggestedBid={suggestedBid}
                  selectedBid={selectedBid}
                  onRequestHint={handleRequestHint}
                  handAnalysis={handPoints ? {
                    totalPoints: handPoints.total_points,
                    hcp: handPoints.hcp,
                    dist: handPoints.dist_points,
                    suits: {
                      spades: { hcp: handPoints.suit_hcp?.['♠'] || 0, length: handPoints.suit_lengths?.['♠'] || 0 },
                      hearts: { hcp: handPoints.suit_hcp?.['♥'] || 0, length: handPoints.suit_lengths?.['♥'] || 0 },
                      diamonds: { hcp: handPoints.suit_hcp?.['♦'] || 0, length: handPoints.suit_lengths?.['♦'] || 0 },
                      clubs: { hcp: handPoints.suit_hcp?.['♣'] || 0, length: handPoints.suit_lengths?.['♣'] || 0 }
                    },
                    suitQuality: handPoints.suit_quality || [],
                    balanced: handPoints.balanced !== undefined ? handPoints.balanced : (
                      // Calculate balanced if not provided: 4-3-3-3, 4-4-3-2, or 5-3-3-2 with no voids/singletons
                      (() => {
                        const lengths = [
                          handPoints.suit_lengths?.['♠'] || 0,
                          handPoints.suit_lengths?.['♥'] || 0,
                          handPoints.suit_lengths?.['♦'] || 0,
                          handPoints.suit_lengths?.['♣'] || 0
                        ].sort((a, b) => b - a);
                        return lengths[0] <= 5 && lengths[3] >= 2;
                      })()
                    )
                  } : null}
                />
              ) : null
            }
          >
            {/* Game Column - green table */}
            <div className="bid-game-column">
              <div className="bid-game-area">
                {/* BIDDING TABLE ZONE — fills green space above hand */}
                <div className="bidding-table-zone">
                  <div className="bidding-scroll">
                    <BiddingTable auction={displayAuction} players={players} dealer={displayDealer} nextPlayerIndex={nextPlayerIndex} onBidClick={handleBidClick} isComplete={isAuctionOver(displayAuction)} myPosition={inRoom ? (isHost ? 'S' : 'N') : null} />
                  </div>
                </div>

                {/* Bid feedback - between table and hand (coached mode only) */}
                {bidFeedback && gamePhase === 'bidding' && sessionMode === 'coached' && (
                  <div className="feedback-strip">
                    <div className={`feedback-icon ${bidFeedback.score >= 8 ? 'good' : bidFeedback.score >= 5 ? 'ok' : 'poor'}`}>
                      {bidFeedback.score >= 8 ? '✓' : bidFeedback.score >= 5 ? '~' : '✗'}
                    </div>
                    <div className="feedback-text">
                      <strong>{bidFeedback.score >= 8 ? 'Excellent!' : bidFeedback.score >= 5 ? 'Acceptable' : 'Suboptimal'}</strong> {bidFeedback.message || ''}
                    </div>
                    {bidFeedback.concept && <div className="feedback-concept">{bidFeedback.concept}</div>}
                    <button className="feedback-close" onClick={() => setBidFeedback(null)}>×</button>
                  </div>
                )}

                {/* SOUTH ZONE — hand + bidding controls only (content-sized) */}
                <div className={`south-affordance-zone ${!displayHand || displayHand.length === 0 ? 'loading' : ''}`}>
                {/* Your Hand */}
                <div className="bid-hand-container shrink-to-fit-center">
                  {displayHand && displayHand.length > 0 ? (
                    <div className="text-base flex flex-row gap-[0.6em] justify-center py-2 scale-on-squeeze">
                      {getSuitOrder(null).map(suit => {
                        const suitCards = displayHand.filter(card => card.suit === suit);
                        if (suitCards.length === 0) return null;
                        const count = suitCards.length;
                        const spacingClass = count >= 7 ? '-space-x-[2.0em]' : count >= 5 ? '-space-x-[1.6em]' : '-space-x-[1.2em]';
                        return (
                          <div key={suit} className={`flex flex-row ${spacingClass}`}>
                            {suitCards.map((card, idx) => (
                              <div key={`${suit}-${card.rank}`} style={{ zIndex: 10 + idx }}>
                                <Card rank={card.rank} suit={card.suit} customScaleClass="text-base" />
                              </div>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p style={{color: 'rgba(255,255,255,0.7)', textAlign: 'center', padding: '16px'}}>
                      {isInitializing ? 'System Initiating...' : 'Dealing...'}
                    </p>
                  )}
                </div>

                {/* Bidding controls — box + action buttons */}
                <div className="bidding-section">
                  <div className="bidding-box-container">
                    <BiddingBoxComponent onBid={handleUserBid} disabled={!canUserBid || isAiBidding || isAuctionOver(displayAuction)} auction={displayAuction} />
                  </div>

                  <div className="deal-actions">
                    {isAuctionOver(displayAuction) && !isPassedOut(displayAuction) ? (
                      inRoom && !isHost ? (
                        <div className="waiting-for-host" style={{
                          background: 'rgba(59, 130, 246, 0.15)',
                          border: '2px solid #3b82f6',
                          borderRadius: '8px',
                          padding: '12px 20px',
                          color: '#93c5fd',
                          fontWeight: '600',
                          fontSize: '15px',
                          textAlign: 'center'
                        }}>
                          ⏳ Waiting for Host to start play...
                        </div>
                      ) : (
                        <button className="deal-btn primary" data-testid="play-this-hand-button" onClick={startPlayPhase}>
                          ▶ Play This Hand
                        </button>
                      )
                    ) : (
                      <button className="deal-btn primary" data-testid="deal-button" onClick={dealNewHand}>
                        🎲 Deal New Hand
                      </button>
                    )}
                    <button className="deal-btn secondary" data-testid="replay-button" onClick={handleReplayHand} disabled={!initialDeal || displayAuction.length === 0}>
                      ↻ Rebid Hand
                    </button>
                    {isAuctionOver(displayAuction) && !isPassedOut(displayAuction) && (
                      <button className="deal-btn secondary" onClick={dealNewHand}>
                        🎲 Deal New
                      </button>
                    )}
                  </div>
                </div>
                </div>{/* End south-affordance-zone */}

                {error && <div className="error-message" style={{color: '#ff8a8a', textAlign: 'center', padding: '8px'}}>{error}</div>}
              </div>
            </div>
          </SplitGameLayout>
        </div>
      ) : null}

      {/* Trick Potential Chart Overlay */}
      {showTrickPotential && ddTable && (
        <TrickPotentialChart
          ddTable={ddTable}
          onClose={() => setShowTrickPotential(false)}
        />
      )}

      {/* Loading state - showing when transitioning to play but playState not yet loaded */}
      {!shouldShowHands && gamePhase === 'playing' && !playState && (
        <div className="play-phase loading-play">
          <div className="loading-indicator">
            <div className="loading-spinner"></div>
            <p>Dealing hand and setting up play...</p>
          </div>
        </div>
      )}

      {!shouldShowHands && gamePhase === 'playing' && playState && (
        <div className="play-phase" style={{ position: 'relative' }}>
          {/* DEBUG INDICATOR: Shows AI loop state - Dev mode only */}
          {isDevMode && playState.tricks_won && Object.values(playState.tricks_won).reduce((a, b) => a + b, 0) < 13 && (
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
          <PlayTable
            playState={playState}
            userHand={hand}
            dummyHand={playState.dummy_hand?.cards || playState.dummy_hand || dummyHand}
            declarerHand={declarerHand}
            onCardPlay={handleCardPlay}
            onDeclarerCardPlay={handleDeclarerCardPlay}
            onDummyCardPlay={handleDummyCardPlay}
            onNewHand={playRandomHand}
            onReplay={replayCurrentHand}
            // Room mode: pass actual user position
            userPosition={inRoom ? myPosition : 'S'}
            // Turn control: use backend data when available
            isUserTurn={
              playState.is_user_turn ?? (
                inRoom
                  ? isMyTurn
                  : (playState.next_to_play === 'S' && playState.dummy !== 'S')
              )
            }
            isDeclarerTurn={
              Array.isArray(playState.controllable_positions)
                ? (playState.controllable_positions.includes(playState.contract.declarer) && playState.next_to_play === playState.contract.declarer)
                : (playState.next_to_play === playState.contract.declarer && (playState.contract.declarer === 'N' || playState.contract.declarer === 'S'))
            }
            isDummyTurn={
              Array.isArray(playState.controllable_positions)
                ? (playState.controllable_positions.includes(playState.dummy) && playState.next_to_play === playState.dummy)
                : (playState.next_to_play === playState.dummy && (playState.contract.declarer === 'N' || playState.contract.declarer === 'S'))
            }
            auction={auction}
            dealer={dealer}
            scoreData={scoreData}
            vulnerability={vulnerability}
            // Last trick feature
            showLastTrick={showLastTrick}
            lastTrick={lastTrick}
            onShowLastTrick={() => setShowLastTrick(true)}
            onHideLastTrick={() => setShowLastTrick(false)}
            // Claim remaining tricks
            onClaim={handleClaim}
          />
          {/* Don't show AI bidding status messages during play - only show errors if they occur */}
          {/* Play phase errors - Show session-related errors always, dev errors in dev mode only */}
          {playState.tricks_won && Object.values(playState.tricks_won).reduce((a, b) => a + b, 0) < 13 && error && (
            error.toLowerCase().includes('session') || error.toLowerCase().includes('no play in progress') || error.toLowerCase().includes('deal') ? (
              <div className="session-lost-message" style={{
                background: 'rgba(244, 67, 54, 0.15)',
                border: '1px solid #f44336',
                borderRadius: '8px',
                padding: '16px',
                margin: '16px auto',
                maxWidth: '400px',
                textAlign: 'center'
              }}>
                <p style={{ color: '#f44336', fontWeight: 600, marginBottom: '12px' }}>
                  Session expired
                </p>
                <p style={{ color: '#666', fontSize: '14px', marginBottom: '16px' }}>
                  The game state was lost. Please deal a new hand to continue.
                </p>
                <button
                  onClick={dealNewHand}
                  className="action-btn primary"
                  style={{ padding: '10px 24px' }}
                >
                  Deal New Hand
                </button>
              </div>
            ) : isDevMode && <div className="error-message">{error}</div>
          )}

          {/* Show All Hands toggle for play phase - available after hand is complete */}
          {playState.tricks_won && Object.values(playState.tricks_won).reduce((a, b) => a + b, 0) === 13 && (
            <div className="show-hands-controls" style={{ marginTop: '20px' }}>
              <label className="show-hands-toggle">
                <input
                  type="checkbox"
                  checked={showAllHands}
                  onChange={handleToggleShowAllHands}
                />
                <span>Show All Hands</span>
              </label>
            </div>
          )}

          {/* Floating Result Overlay - appears over the game board when hand is complete (via tricks or claim) */}
          <ResultOverlay
            scoreData={scoreData}
            isVisible={!!scoreData}
            onPlayAnotherHand={playRandomHand}
            onReplayHand={replayCurrentHand}
            onReviewHand={lastSavedHandId ? () => {
              setReviewPageHandId(lastSavedHandId);
              setReviewPageType('play');
              setHandReviewSource('post-hand');
              setShowReviewPage(true);
            } : null}
            onViewProgress={() => {
              if (isGuest && requiresRegistration('progress')) {
                promptForRegistration();
              } else {
                setShowLearningDashboard(true);
          trackDashboardOpen();
              }
            }}
            onDealNewHand={dealNewHand}
          />
        </div>
      )}

      {/* Action area - only show in old table-layout mode (shouldShowHands)
          New layout: PlayTable has its own action-bar, no external controls needed
          Per CC_CORRECTIONS Fix #5: Remove separate button section below table */}
      {shouldShowHands && (
      <div className="action-area">
        <div className="controls-section">
          {/* Game controls - Context-aware based on game phase AND workspace */}
          <div className="game-controls">
            {/* In Play workspace: always show play-oriented buttons */}
            {currentWorkspace === 'play' ? (
              <>
                {/* Primary action - Play a new hand (AI bids, user plays) */}
                <button className="play-new-hand-button primary-action" data-testid="play-new-hand-button" onClick={playRandomHand}>🎲 Play New Hand</button>
                {/* Secondary actions */}
                <div className="secondary-actions">
                  <button className="deal-button" data-testid="bid-new-hand-button" onClick={dealNewHand}>📝 Bid New Hand</button>
                  <button className="replay-button" data-testid="replay-hand-button" onClick={replayCurrentHand} disabled={!initialDeal}>🔄 Replay Hand</button>
                </div>
              </>
            ) : gamePhase === 'bidding' && shouldShowHands ? (
              <>
                {/* Bidding controls for table-layout view (shouldShowHands) */}
                <BiddingBoxComponent onBid={handleUserBid} disabled={!canUserBid || isAiBidding || isAuctionOver(displayAuction)} auction={displayAuction} />
                {/* Convention mode badge */}
                {activeConvention && (
                  <div className="convention-mode-badge" data-testid="convention-mode-badge">
                    <span className="convention-name">🎯 {getShortConventionName(activeConvention)}</span>
                    <button
                      className="exit-convention-button"
                      onClick={exitConventionMode}
                      title="Exit convention mode"
                      data-testid="exit-convention-button"
                    >
                      ✕
                    </button>
                  </div>
                )}
                {/* Primary action when bidding is complete */}
                {isAuctionOver(displayAuction) && !isPassedOut(displayAuction) && (
                  inRoom && !isHost ? (
                    <div className="waiting-for-host" style={{
                      background: 'rgba(59, 130, 246, 0.15)',
                      border: '2px solid #3b82f6',
                      borderRadius: '8px',
                      padding: '12px 20px',
                      color: '#93c5fd',
                      fontWeight: '600',
                      fontSize: '15px',
                      textAlign: 'center'
                    }}>
                      ⏳ Waiting for Host to start play...
                    </div>
                  ) : (
                    <button className="play-this-hand-button primary-action" data-testid="play-this-hand-button" onClick={startPlayPhase}>
                      ▶ Play This Hand
                    </button>
                  )
                )}
                {/* Show message when hand is passed out */}
                {isPassedOut(displayAuction) && (
                  <div className="passed-out-message" data-testid="passed-out-message">
                    Passed Out - No contract
                  </div>
                )}
                {/* Secondary actions */}
                <div className="secondary-actions">
                  {activeConvention ? (
                    <button className="deal-button" data-testid="deal-convention-button" onClick={() => loadScenarioByName(activeConvention)}>
                      🎯 Bid Another {getShortConventionName(activeConvention)} Hand
                    </button>
                  ) : (
                    <button className="deal-button" data-testid="deal-button" onClick={dealNewHand}>🎲 Deal New Hand</button>
                  )}
                  <button className="replay-button" data-testid="replay-button" onClick={handleReplayHand} disabled={!initialDeal || displayAuction.length === 0}>🔄 Rebid Hand</button>
                </div>
              </>
            ) : gamePhase === 'playing' ? (
              <>
                {/* Playing phase in Bid workspace - show play controls */}
                <button className="play-new-hand-button primary-action" data-testid="play-new-hand-button" onClick={playRandomHand}>🎲 Play New Hand</button>
                {/* Secondary actions */}
                <div className="secondary-actions">
                  <button className="deal-button" data-testid="bid-new-hand-button" onClick={dealNewHand}>📝 Bid New Hand</button>
                  <button className="replay-button" data-testid="replay-hand-button" onClick={replayCurrentHand}>🔄 Replay Hand</button>
                </div>
              </>
            ) : null}
          </div>

          {/* AI Difficulty Selector & Review - Dev mode only (Ctrl+Shift+D to toggle) */}
          {isDevMode && gamePhase === 'playing' && (
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
        </div>
        {/* Only show bidding-specific controls during bidding phase */}
        {gamePhase === 'bidding' && (
          <>
            <div className="show-hands-controls">
              <label className="show-hands-toggle">
                <input
                  type="checkbox"
                  checked={showAllHands}
                  onChange={handleToggleShowAllHands}
                  data-testid="show-all-hands-toggle"
                />
                <span>Show All Hands</span>
              </label>
              <label className="show-hands-toggle hint-mode-toggle">
                <input
                  type="checkbox"
                  checked={hintModeEnabled}
                  onChange={() => setHintModeEnabled(!hintModeEnabled)}
                  data-testid="hint-mode-toggle"
                />
                <span>💡 AI Hints</span>
              </label>
            </div>
            <div className="ai-review-controls">
              {activeConvention && (
                <button onClick={handleShowConventionHelp} className="help-button" data-testid="convention-help-button">ℹ️ Convention Help</button>
              )}
              {/* AI Review - Dev mode only (Ctrl+Shift+D to toggle) */}
              {isDevMode && (
                <button onClick={() => setShowReviewModal(true)} className="ai-review-button" data-testid="ai-review-button">🤖 Request AI Review</button>
              )}
            </div>
          </>
        )}
      </div>
      )}

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

      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmit={handleFeedbackSubmit}
        context="freeplay"
        contextData={{
          game_phase: gamePhase,
          auction: auction,
          hand: hand,
        }}
      />

      {/* Governor Safety Guard Dialog - blocks critical/significant impact bids when hints are enabled */}
      <GovernorConfirmDialog
        isOpen={showGovernorDialog}
        onClose={handleGovernorCancel}
        onProceed={handleGovernorProceed}
        bid={pendingBid}
        impact={pendingBidFeedback?.feedback?.impact}
        reasoning={pendingBidFeedback?.feedback?.reasoning}
        optimalBid={pendingBidFeedback?.feedback?.optimal_bid}
      />

      {/* Claim Modal - for claiming remaining tricks during play */}
      <ClaimModal
        isOpen={showClaimModal}
        onClose={handleClaimModalClose}
        tricksRemaining={playState?.tricks_won ? 13 - Object.values(playState.tricks_won).reduce((a, b) => a + b, 0) : 0}
        tricksWonNS={playState ? (playState.tricks_won?.N || 0) + (playState.tricks_won?.S || 0) : 0}
        tricksWonEW={playState ? (playState.tricks_won?.E || 0) + (playState.tricks_won?.W || 0) : 0}
        tricksNeeded={playState?.contract?.tricks_needed || 7}
        onSubmitClaim={handleSubmitClaim}
        isValidating={claimValidating}
        validationResult={claimValidationResult}
      />

      {/* ScoreDisplay modal replaced by floating ResultOverlay in play-phase section */}

      {/* Progress/Dashboard - Full-screen page */}
      {showLearningDashboard && (
        <div className="learning-dashboard-overlay" data-testid="dashboard-overlay">
          {/* Force remount on each open to refresh data */}
          <LearningDashboard
            key={Date.now()}
            userId={userId}
            onPracticeClick={(rec) => {
              console.log('Practice recommendation:', rec);
              setShowLearningDashboard(false);
            }}
            onStartLearning={(track) => {
              console.log('Start learning:', track);
              setShowLearningDashboard(false);
              setLearningModeTrack(track || 'bidding');
              setShowLearningMode(true);
            }}
            onStartFreeplay={(track) => {
              console.log('Start freeplay:', track);
              setShowLearningDashboard(false);
              if (track === 'play') {
                setCurrentWorkspace('play');
                // Always start a fresh random hand when coming from dashboard
                // User expects a new hand ready for gameplay, not to see previous hand state
                playRandomHand();
              } else {
                setCurrentWorkspace('bid');
                dealNewHand();
              }
            }}
            onReviewHand={handleOpenReviewPage}
          />
        </div>
      )}

      {/* Unified review page (bidding + play with tab toggle) */}
      {showReviewPage && reviewPageHandId && (
        <ReviewPage
          handId={reviewPageHandId}
          initialMode={reviewPageType}
          onBack={handleCloseReviewPage}
          onPrevHand={reviewCurrentIndex > 0 ? () => handleNavigateReviewHand(-1) : null}
          onNextHand={reviewCurrentIndex < reviewHandList.length - 1 ? () => handleNavigateReviewHand(1) : null}
          currentIndex={reviewCurrentIndex}
          totalHands={reviewHandList.length}
          handReviewSource={handReviewSource}
          onPlayAnother={handReviewSource === 'post-hand' ? () => {
            handleCloseReviewPage();
            playRandomHand();
          } : null}
          onReplay={handReviewSource === 'post-hand' ? () => {
            handleCloseReviewPage();
            replayCurrentHand();
          } : null}
          onViewProgress={handReviewSource === 'post-hand' ? () => {
            handleCloseReviewPage();
            setShowLearningDashboard(true);
          trackDashboardOpen();
          } : null}
        />
      )}

      {/* Learning Mode - Full-screen guided learning */}
      {showLearningMode && (
        <div className="learning-mode-overlay">
          <LearningMode userId={userId} initialTrack={learningModeTrack} />
        </div>
      )}

      {/* Privacy Policy Modal - accessible via /privacy URL and footer link */}
      {showPrivacyPolicy && (
        <PrivacyPolicy onClose={() => {
          setShowPrivacyPolicy(false);
          if (window.location.pathname === '/privacy') window.history.replaceState(null, '', '/');
        }} />
      )}

      {/* About Us Modal - accessible via /about URL and footer link */}
      {showAboutUs && (
        <AboutUs onClose={() => {
          setShowAboutUs(false);
          if (window.location.pathname === '/about') window.history.replaceState(null, '', '/');
        }} />
      )}

      {/* Persistent footer with legal links */}
      <footer className="app-footer">
        <button className="footer-link" onClick={() => setShowPrivacyPolicy(true)}>Privacy Policy</button>
        <span className="footer-divider">|</span>
        <button className="footer-link" onClick={() => setShowAboutUs(true)}>About Us</button>
      </footer>

      {/* DDS Status Indicator - Dev mode only */}
      {isDevMode && <DDSStatusIndicator />}

      {/* Privacy Modal */}
      <PrivacyPage isOpen={showPrivacy} onClose={() => setShowPrivacy(false)} />

      {/* About Modal */}
      <AboutPage isOpen={showAbout} onClose={() => setShowAbout(false)} />

      {/* Footer with trust links - shown on mode selector */}
      {showModeSelector && (
        <Footer
          onPrivacyClick={() => setShowPrivacy(true)}
          onAboutClick={() => setShowAbout(true)}
        />
      )}

      {/* Dev mode indicator - subtle badge when dev mode is active */}
      {isDevMode && (
        <div
          style={{
            position: 'fixed',
            top: '8px',
            left: '8px',
            display: 'flex',
            gap: '4px',
            zIndex: 10000
          }}
        >
          <div
            style={{
              background: 'rgba(139, 92, 246, 0.9)',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 'bold',
              cursor: 'pointer',
              userSelect: 'none'
            }}
            onClick={() => window.disableDevMode?.()}
            title="Click to disable dev mode (or press Ctrl+Shift+D)"
          >
            DEV
          </div>
          <div
            style={{
              background: useV2Schema ? 'rgba(59, 130, 246, 0.9)' : 'rgba(100, 100, 100, 0.7)',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 'bold',
              cursor: 'pointer',
              userSelect: 'none'
            }}
            onClick={toggleV2Schema}
            title={useV2Schema ? 'V2 Schema ACTIVE - Click to disable' : 'Click to enable V2 Schema engine'}
          >
            {useV2Schema ? 'V2 ✓' : 'V2'}
          </div>
        </div>
      )}
    </div>
  );
}
// Wrap App with AuthProvider, UserProvider, and RoomProvider
function AppWithAuth() {
  return (
    <AuthProvider>
      <UserProvider>
        <RoomProvider>
          <App />
        </RoomProvider>
      </UserProvider>
    </AuthProvider>
  );
}

export default AppWithAuth;