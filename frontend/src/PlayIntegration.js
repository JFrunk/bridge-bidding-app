/**
 * PlayIntegration.js
 *
 * This file contains all the play-phase logic that needs to be integrated into App.js
 * Copy these functions into App.js after line 260 (after handleCloseConventionHelp)
 */

// ========== CARD PLAY FUNCTIONS ==========
// Add these functions to App.js

export const playFunctions = `
  // Start play phase after bidding completes
  const startPlayPhase = async () => {
    try {
      const auctionBids = auction.map(a => a.bid);

      const response = await fetch(\`\${API_URL}/api/start-play\`, {
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
      setDisplayedMessage(\`Contract: \${data.contract}. Opening leader: \${data.opening_leader}\`);

      // Start AI play loop
      setIsPlayingCard(true);
    } catch (err) {
      console.error('Error starting play:', err);
      setError('Failed to start card play phase');
    }
  };

  // Handle user card play
  const handleCardPlay = async (card) => {
    if (isPlayingCard) return; // Prevent double-click

    try {
      setIsPlayingCard(true);

      const response = await fetch(\`\${API_URL}/api/play-card\`, {
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

  // Close score modal
  const handleCloseScore = () => {
    setScoreData(null);
  };
`;

// ========== USEEFFECT MODIFICATIONS ==========

export const aiPlayLoopUseEffect = `
  // AI play loop - runs after bidding completes
  useEffect(() => {
    if (gamePhase !== 'playing' || !isPlayingCard) return;

    const runAiPlay = async () => {
      try {
        // Get current play state
        const stateResponse = await fetch(\`\${API_URL}/api/get-play-state\`);
        if (!stateResponse.ok) throw new Error("Failed to get play state");

        const state = await stateResponse.json();
        setPlayState(state);

        // Update dummy hand if revealed
        if (state.dummy_hand && !dummyHand) {
          setDummyHand(state.dummy_hand);
        }

        // Check if play is complete (13 tricks)
        const totalTricks = Object.values(state.tricks_won).reduce((a, b) => a + b, 0);
        if (totalTricks === 13) {
          // Play complete - calculate score
          const scoreResponse = await fetch(\`\${API_URL}/api/complete-play\`, {
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

        const playResponse = await fetch(\`\${API_URL}/api/get-ai-play\`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ position: nextPlayer })
        });

        if (!playResponse.ok) throw new Error("AI play failed");

        const playData = await playResponse.json();
        console.log('AI played:', playData);

        setDisplayedMessage(\`\${nextPlayer} played \${playData.card.rank}\${playData.card.suit}\`);

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
`;

export const aiBiddingModification = `
  // In the AI bidding useEffect, replace the else block:
  } else if (isAiBidding) {
    setIsAiBidding(false);
    // Check if bidding just completed - start play phase
    if (isAuctionOver(auction)) {
      setTimeout(() => startPlayPhase(), 1000);
    }
  }
`;

// ========== RENDER MODIFICATIONS ==========

export const renderModifications = `
  // Replace the bidding-area div (around line 393-398) with:

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

  // Update BiddingBox disabled prop (around line 402):
  <BiddingBox
    onBid={handleUserBid}
    disabled={gamePhase === 'playing' || players[nextPlayerIndex] !== 'South' || isAiBidding}
    auction={auction}
  />

  // Add score modal before the final </div> (around line 497):
  {scoreData && (
    <ScoreDisplay scoreData={scoreData} onClose={handleCloseScore} />
  )}
`;

console.log("PlayIntegration.js loaded. See PLAY_INTEGRATION_GUIDE.md for manual integration steps.");
