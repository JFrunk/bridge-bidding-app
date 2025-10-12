# Card Play Integration Guide

## Changes needed to App.js

### 1. Add import (line 3) - DONE ✅
```javascript
import { PlayTable, ScoreDisplay } from './PlayComponents';
```

### 2. Add state variables (after line 126) - DONE ✅
```javascript
// Card play state
const [gamePhase, setGamePhase] = useState('bidding'); // 'bidding' or 'playing'
const [playState, setPlayState] = useState(null);
const [dummyHand, setDummyHand] = useState(null);
const [isPlayingCard, setIsPlayingCard] = useState(false);
const [scoreData, setScoreData] = useState(null);
```

### 3. Update resetAuction to also reset play state (around line 135)
Add at the end of `resetAuction` function:
```javascript
setGamePhase('bidding');
setPlayState(null);
setDummyHand(null);
setScoreData(null);
```

### 4. Add card play functions (insert after line 260)
```javascript
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
  if (isPlayingCard) return; // Prevent double-click

  try {
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

    // Continue AI play loop
    setTimeout(() => setIsPlayingCard(true), 500);

  } catch (err) {
    console.error('Error playing card:', err);
    setError(err.message);
    setIsPlayingCard(false);
  }
};

const handleCloseScore = () => {
  setScoreData(null);
  // Optionally deal new hand
  // dealNewHand();
};
```

### 5. Update AI bidding useEffect to trigger play phase (around line 354)
Replace:
```javascript
} else if (isAiBidding) {
  setIsAiBidding(false);
}
```

With:
```javascript
} else if (isAiBidding) {
  setIsAiBidding(false);
  // Check if bidding just completed
  if (isAuctionOver(auction)) {
    // Small delay before transitioning to play
    setTimeout(() => startPlayPhase(), 1000);
  }
}
```

### 6. Add AI play loop useEffect (insert after the AI bidding useEffect, around line 358)
```javascript
// AI play loop - fetches play state and makes AI plays
useEffect(() => {
  if (gamePhase !== 'playing' || !isPlayingCard) return;

  const runAiPlay = async () => {
    try {
      // Get current play state
      const stateResponse = await fetch(`${API_URL}/api/get-play-state`);
      if (!stateResponse.ok) throw new Error("Failed to get play state");

      const state = await stateResponse.json();
      setPlayState(state);

      // Update dummy hand if revealed
      if (state.dummy_hand && !dummyHand) {
        setDummyHand(state.dummy_hand);
      }

      // Check if play is complete
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

      const nextPlayer = state.next_to_play;

      // If it's South's turn, stop and wait for user
      if (nextPlayer === 'S') {
        setIsPlayingCard(false);
        setDisplayedMessage("Your turn to play!");
        return;
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

      setDisplayedMessage(`${nextPlayer} played ${playData.card.rank}${playData.card.suit}`);

      // Continue loop
      setTimeout(() => setIsPlayingCard(true), 500);

    } catch (err) {
      console.error('Error in AI play loop:', err);
      setError('AI play failed');
      setIsPlayingCard(false);
    }
  };

  runAiPlay();
}, [gamePhase, isPlayingCard, dummyHand, vulnerability]);
```

### 7. Update render to show PlayTable when in play phase (around line 392-398)
Replace the bidding-area div:
```javascript
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
    <PlayTable
      playState={playState}
      userHand={hand}
      dummyHand={dummyHand}
      onCardPlay={handleCardPlay}
      isUserTurn={playState.next_to_play === 'S' && !isPlayingCard}
    />
    {displayedMessage && <div className="feedback-panel">{displayedMessage}</div>}
    {error && <div className="error-message">{error}</div>}
  </div>
)}
```

### 8. Add score modal at the end of render (before closing </div>, around line 497)
```javascript
{scoreData && (
  <ScoreDisplay scoreData={scoreData} onClose={handleCloseScore} />
)}
```

### 9. Disable bidding controls during play phase (around line 402)
Update BiddingBox to be disabled during play:
```javascript
<BiddingBox
  onBid={handleUserBid}
  disabled={gamePhase === 'playing' || players[nextPlayerIndex] !== 'South' || isAiBidding}
  auction={auction}
/>
```

## Testing Steps

1. Start backend: `cd backend && python server.py`
2. Start frontend: `cd frontend && npm start`
3. Deal a hand and complete bidding (bid to contract, then 3 passes)
4. Should automatically transition to play phase
5. Watch AI players make opening lead
6. Dummy should be revealed after opening lead
7. When it's your turn (South), click a card to play
8. Continue until all 13 tricks played
9. Score modal should appear showing result

## Known Issues / Future Enhancements

- **Issue**: User hand not being updated correctly after card play
  - **Fix**: Ensure `setHand` filter logic works correctly with Card objects

- **Enhancement**: Add "Play Hand" button to manually trigger play phase
  - Useful if user wants to replay just the bidding

- **Enhancement**: Show trick history
  - Add UI to show previous tricks

- **Enhancement**: Highlight legal cards to play
  - Use `PlayEngine.is_legal_play()` logic on frontend

- **Enhancement**: Add animation for cards being played
  - CSS transitions for cards moving to center

## File Structure
```
frontend/src/
├── App.js (main app - MODIFIED)
├── App.css (existing styles)
├── PlayComponents.js (NEW - play UI components)
└── PlayComponents.css (NEW - play styles)

backend/
├── server.py (MODIFIED - added play endpoints)
├── engine/play_engine.py (NEW - core play logic)
└── engine/simple_play_ai.py (NEW - AI card play)
```
