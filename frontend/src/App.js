import React, { useState, useEffect } from 'react';
import './App.css';

// --- UI Components ---
function Card({ rank, suit }) {
  const suitColor = suit === '♥' || suit === '♦' ? 'suit-red' : 'suit-black';
  
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[rank] || rank;

  return (
    <div className="card">
      <div className={`card-corner top-left ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{suit}</span>
      </div>
      <div className={`card-center ${suitColor}`}>
        <span className="suit-symbol-large">{suit}</span>
      </div>
      <div className={`card-corner bottom-right ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{suit}</span>
      </div>
    </div>
  );
}
function HandAnalysis({ points, vulnerability }) {
  if (!points) return null;
  return ( <div className="hand-analysis"><h4>Hand Analysis (Vuln: {vulnerability})</h4><p><strong>HCP:</strong> {points.hcp} + <strong>Dist:</strong> {points.dist_points} = <strong>Total: {points.total_points}</strong></p><div className="suit-points"><div><span className="suit-black">♠</span> {points.suit_hcp['♠']} pts ({points.suit_lengths['♠']})</div><div><span className="suit-red">♥</span> {points.suit_hcp['♥']} pts ({points.suit_lengths['♥']})</div><div><span className="suit-red">♦</span> {points.suit_hcp['♦']} pts ({points.suit_lengths['♦']})</div><div><span className="suit-black">♣</span> {points.suit_hcp['♣']} pts ({points.suit_lengths['♣']})</div></div></div> );
}

function PlayerHand({ position, hand, points, vulnerability }) {
  if (!hand || !points) return null;
  return (
    <div className={`player-hand player-${position.toLowerCase()}`}>
      <h3>{position}</h3>
      <div className="hand-display">
        {['♠', '♥', '♦', '♣'].map(suit => (
          <div key={suit} className="suit-group">
            {hand.filter(card => card.suit === suit).map((card, index) => (
              <Card key={`${suit}-${index}`} rank={card.rank} suit={card.suit} />
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
function BiddingBox({ onBid, disabled, auction }) {
  const [level, setLevel] = useState(null);
  const suits = ['♣', '♦', '♥', '♠', 'NT'];
  const calls = ['Pass', 'X', 'XX'];
  const lastRealBid = [...auction].reverse().find(b => !['Pass', 'X', 'XX'].includes(b.bid));
  const suitOrder = { '♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5 };
  const isBidLegal = (level, suit) => {
    if (!lastRealBid) return true;
    const lastLevel = parseInt(lastRealBid.bid[0], 10);
    const lastSuit = lastRealBid.bid.slice(1);
    if (level > lastLevel) return true;
    if (level === lastLevel && suitOrder[suit] > suitOrder[lastSuit]) return true;
    return false;
  };
  const handleBid = (suit) => { if (level) { onBid(suit === 'NT' ? `${level}NT` : `${level}${suit}`); setLevel(null); } };
  const handleCall = (call) => { onBid(call); setLevel(null); };
  return ( <div className="bidding-box-container"><div className="bidding-box-levels">{[1, 2, 3, 4, 5, 6, 7].map(l => ( <button key={l} onClick={() => setLevel(l)} className={level === l ? 'selected' : ''} disabled={disabled}>{l}</button>))}</div><div className="bidding-box-suits">{suits.map(s => ( <button key={s} onClick={() => handleBid(s)} disabled={!level || disabled || !isBidLegal(level, s)}>{s === 'NT' ? 'NT' : <span className={s === '♥' || s === '♦' ? 'suit-red' : 'suit-black'}>{s}</span>}</button>))}</div><div className="bidding-box-calls">{calls.map(c => <button key={c} onClick={() => handleCall(c)} disabled={disabled}>{c}</button>)}</div></div> );
}

function App() {
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

  const resetAuction = (dealData) => {
    setInitialDeal(dealData);
    setHand(dealData.hand);
    setHandPoints(dealData.points);
    setVulnerability(dealData.vulnerability);
    setAuction([]);
    setNextPlayerIndex(players.indexOf(dealer));
    setDisplayedMessage('');
    setError('');
    setIsAiBidding(true);
    setShowHandsThisDeal(false);
    if (alwaysShowHands) {
      fetchAllHands();
    } else {
      setAllHands(null);
    }
  };

  const fetchAllHands = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/get-all-hands');
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

  const dealNewHand = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/deal-hands');
      if (!response.ok) throw new Error("Failed to deal hands.");
      const data = await response.json();
      resetAuction(data);
    } catch (err) { setError("Could not connect to server to deal."); }
  };
  
  const handleLoadScenario = async () => {
    if (!selectedScenario) return;
    try {
      const response = await fetch('http://localhost:5001/api/load-scenario', {
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
        const response = await fetch('http://localhost:5001/api/scenarios');
        const data = await response.json();
        setScenarioList(data.scenarios);
        if (data.scenarios.length > 0) setSelectedScenario(data.scenarios[0]);
      } catch (err) { console.error("Could not fetch scenarios", err); }
      await dealNewHand();
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
      const feedbackResponse = await fetch('http://localhost:5001/api/get-feedback', {
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
          const response = await fetch('http://localhost:5001/api/get-next-bid', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auction_history: auction.map(a => a.bid), current_player: players[nextPlayerIndex] })
          });
          if (!response.ok) throw new Error("AI failed to get bid.");
          const data = await response.json();
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
    }
  }, [auction, nextPlayerIndex, isAiBidding, players]);

  const shouldShowHands = showHandsThisDeal || alwaysShowHands;

  return (
    <div className="app-container">
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
      ) : (
        <div className="top-panel">
          <div className="my-hand">
            <h2>Your Hand (South)</h2>
            <div className="hand-display">
              {['♠', '♥', '♦', '♣'].map(suit => ( <div key={suit} className="suit-group">{hand.filter(card => card.suit === suit).map((card, index) => ( <Card key={`${suit}-${index}`} rank={card.rank} suit={card.suit} />))}</div>))}
            </div>
            <HandAnalysis points={handPoints} vulnerability={vulnerability} />
          </div>
        </div>
      )}

      {!shouldShowHands && (
        <div className="bidding-area">
          <h2>Bidding</h2>
          <BiddingTable auction={auction} players={players} dealer={dealer} nextPlayerIndex={nextPlayerIndex} onBidClick={handleBidClick} />
          {displayedMessage && <div className="feedback-panel">{displayedMessage}</div>}
          {error && <div className="error-message">{error}</div>}
        </div>
      )}

      <div className="action-area">
        <BiddingBox onBid={handleUserBid} disabled={players[nextPlayerIndex] !== 'South' || isAiBidding} auction={auction} />
        <div className="scenario-loader">
          <select value={selectedScenario} onChange={(e) => setSelectedScenario(e.target.value)}>{scenarioList.map(name => <option key={name} value={name}>{name}</option>)}</select>
          <button onClick={handleLoadScenario}>Load Scenario</button>
        </div>
        <div className="game-controls">
          <button className="replay-button" onClick={handleReplayHand} disabled={!initialDeal || auction.length === 0}>Replay Hand</button>
          <button className="deal-button" onClick={dealNewHand}>Deal New Hand</button>
        </div>
        <div className="show-hands-controls">
          <button onClick={handleShowHandsThisDeal}>{showHandsThisDeal ? 'Hide Hands (This Deal)' : 'Show Hands (This Deal)'}</button>
          <button onClick={handleToggleAlwaysShowHands} className={alwaysShowHands ? 'active' : ''}>{alwaysShowHands ? 'Always Show: ON' : 'Always Show: OFF'}</button>
        </div>
      </div>
    </div>
  );
}
export default App;