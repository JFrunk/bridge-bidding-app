/**
 * HandReviewPage - Full-screen play-by-play analysis page
 * 
 * Replaces the modal-based HandReviewModal with a dedicated full-screen page.
 * Provides better mobile and desktop UX with no viewport constraints.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PlayableCard } from '../play/PlayableCard';
import DecayChart from '../analysis/DecayChart';
import ChartHelp from '../help/ChartHelp';
import HeuristicScorecard from './HeuristicScorecard';
import './HandReviewPage.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Rating colors and labels (same as modal)
const RATING_CONFIG = {
    optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '✓', label: 'Optimal' },
    good: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Good' },
    acceptable: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Acceptable' },
    suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
    suboptimal_signal: { color: '#ed8936', bgColor: '#fffaf0', icon: '⚠', label: 'Suboptimal Signal' },
    blunder: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Blunder' },
    error: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Error' }
};

// Suit order (trump-aware for replay)
const getSuitOrder = (trumpStrain) => {
    if (!trumpStrain || trumpStrain === 'NT') {
        return ['♠', '♥', '♣', '♦'];
    }
    const strainToSuit = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
    const trumpSuit = strainToSuit[trumpStrain] || trumpStrain;
    if (trumpSuit === '♥') return ['♥', '♠', '♦', '♣'];
    if (trumpSuit === '♦') return ['♦', '♠', '♥', '♣'];
    if (trumpSuit === '♠') return ['♠', '♥', '♣', '♦'];
    if (trumpSuit === '♣') return ['♣', '♥', '♠', '♦'];
    return ['♠', '♥', '♣', '♦'];
};

// Sort cards within a hand by rank (high to low)
const sortCards = (cards) => {
    const rankOrder = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
    return [...cards].sort((a, b) => {
        const aRank = a.rank || a.r;
        const bRank = b.rank || b.r;
        return rankOrder.indexOf(aRank) - rankOrder.indexOf(bRank);
    });
};

// Normalize suit to Unicode format
const normalizeSuit = (suit) => {
    const map = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
    return map[suit] || suit;
};

// Replay hand display - shows remaining cards with visual PlayableCard components
const ReplayHandDisplay = ({ cards, position, trumpStrain, isVertical = false }) => {
    const suitOrder = getSuitOrder(trumpStrain);

    const cardsBySuit = useMemo(() => {
        const grouped = { '♠': [], '♥': [], '♦': [], '♣': [] };
        cards.forEach(card => {
            const suit = normalizeSuit(card.suit || card.s);
            if (grouped[suit]) {
                grouped[suit].push({
                    rank: card.rank || card.r,
                    suit: suit
                });
            }
        });
        Object.keys(grouped).forEach(suit => {
            grouped[suit] = sortCards(grouped[suit]);
        });
        return grouped;
    }, [cards]);

    const positionLabels = { N: 'North', E: 'East', S: 'South', W: 'West' };

    if (isVertical) {
        const col1Suits = suitOrder.filter(s => s === '♠' || s === '♥');
        const col2Suits = suitOrder.filter(s => s === '♦' || s === '♣');

        return (
            <div className={`replay-hand replay-hand-${position.toLowerCase()} vertical-2col`}>
                <div className="replay-hand-label">{positionLabels[position]}</div>
                <div className="replay-hand-2col">
                    <div className="replay-col">
                        {col1Suits.map(suit => {
                            const suitCards = cardsBySuit[suit];
                            return suitCards.map((card) => (
                                <PlayableCard
                                    key={`${card.rank}-${card.suit}`}
                                    card={card}
                                    disabled
                                    compact
                                />
                            ));
                        })}
                    </div>
                    <div className="replay-col">
                        {col2Suits.map(suit => {
                            const suitCards = cardsBySuit[suit];
                            return suitCards.map((card) => (
                                <PlayableCard
                                    key={`${card.rank}-${card.suit}`}
                                    card={card}
                                    disabled
                                    compact
                                />
                            ));
                        })}
                    </div>
                </div>
                {cards.length === 0 && (
                    <div className="replay-hand-empty">No cards</div>
                )}
            </div>
        );
    }

    return (
        <div className={`replay-hand replay-hand-${position.toLowerCase()} horizontal`}>
            <div className="replay-hand-label">{positionLabels[position]}</div>
            <div className="replay-hand-cards">
                {suitOrder.map(suit => {
                    const suitCards = cardsBySuit[suit];
                    if (suitCards.length === 0) return null;
                    return (
                        <div key={suit} className="replay-suit-group">
                            {suitCards.map((card) => (
                                <PlayableCard
                                    key={`${card.rank}-${card.suit}`}
                                    card={card}
                                    disabled
                                />
                            ))}
                        </div>
                    );
                })}
                {cards.length === 0 && (
                    <div className="replay-hand-empty">No cards</div>
                )}
            </div>
        </div>
    );
};

// Current trick display for replay mode - compass layout
const ReplayTrickDisplay = ({ trick, leader }) => {
    const cardByPosition = useMemo(() => {
        const map = { N: null, E: null, S: null, W: null };
        trick.forEach(play => {
            const pos = play.player || play.position;
            map[pos] = {
                rank: play.rank || play.r,
                suit: normalizeSuit(play.suit || play.s)
            };
        });
        return map;
    }, [trick]);

    const positions = [
        { pos: 'N', className: 'replay-trick-north' },
        { pos: 'W', className: 'replay-trick-west' },
        { pos: 'E', className: 'replay-trick-east' },
        { pos: 'S', className: 'replay-trick-south' }
    ];

    return (
        <div className="replay-trick-display">
            <div className="replay-trick-center">
                {leader && <span className="replay-trick-leader">Lead: {leader}</span>}
            </div>
            {positions.map(({ pos, className }) => (
                <div key={pos} className={className}>
                    {cardByPosition[pos] ? (
                        <div className="replay-trick-card-wrapper">
                            <PlayableCard card={cardByPosition[pos]} disabled />
                            <span className="replay-trick-position-label">{pos}</span>
                        </div>
                    ) : (
                        <div className="replay-trick-empty" />
                    )}
                </div>
            ))}
        </div>
    );
};

// Feedback panel for the current trick
const TrickFeedbackPanel = ({ decision }) => {
    if (!decision) {
        return (
            <div className="trick-feedback-panel no-data" data-testid="trick-feedback-no-data">
                <p style={{ margin: 0, color: '#6b7280' }}>
                    No analysis recorded for this play
                </p>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: '#9ca3af' }}>
                    This may occur for AI plays or when detailed analysis was unavailable
                </p>
            </div>
        );
    }

    if (decision.is_basic_info) {
        const positionName = decision.position === 'N' ? 'North' :
            decision.position === 'S' ? 'South' :
                decision.position === 'E' ? 'East' : 'West';
        return (
            <div className="trick-feedback-panel basic-info" style={{
                borderColor: '#6b7280',
                backgroundColor: '#f9fafb'
            }} data-testid="trick-feedback-basic-info" data-position={decision.position}>
                <div className="feedback-body">
                    <div className="play-comparison">
                        <span className="played-card">
                            <strong>{positionName} played:</strong> {decision.user_card}
                        </span>
                    </div>
                    <p className="feedback-text" style={{ color: '#6b7280', fontStyle: 'italic' }}>
                        Trick {decision.trick_number} • No detailed analysis recorded
                    </p>
                </div>
            </div>
        );
    }

    const isSignalFeedback = decision.signal_reason && decision.tricks_cost === 0 && !decision.is_signal_optimal;
    const reasoning = (decision.reasoning || '').toLowerCase();
    const correctIndicators = ['correct', 'conserving', 'optimal', 'good', 'right', 'best', 'perfect'];
    const reasoningSaysCorrect = correctIndicators.some(ind => reasoning.includes(ind));

    let suppressSignalFeedback = false;
    if (isSignalFeedback && decision.rating === 'optimal' && reasoningSaysCorrect) {
        suppressSignalFeedback = true;
    }
    if (isSignalFeedback && decision.is_signal_optimal) {
        suppressSignalFeedback = true;
    }

    const effectiveRating = (isSignalFeedback && !suppressSignalFeedback) ? 'suboptimal_signal' : decision.rating;
    const config = RATING_CONFIG[effectiveRating] || RATING_CONFIG.good;

    const positionName = decision.position === 'N' ? 'North' :
        decision.position === 'S' ? 'South' :
            decision.position === 'E' ? 'East' : 'West';

    return (
        <div
            className={`trick-feedback-panel ${effectiveRating}`}
            style={{ borderColor: config.color, backgroundColor: config.bgColor }}
            data-testid="trick-feedback-panel"
            data-rating={effectiveRating}
            data-position={decision.position}
        >
            <div className="feedback-header">
                <span className="feedback-badge" style={{ backgroundColor: config.color }} data-testid="feedback-badge">
                    {config.icon} {config.label}
                </span>
                <span className="position-indicator" style={{ marginLeft: '8px', color: '#6b7280' }}>
                    ({positionName})
                </span>
                {decision.tricks_cost > 0 && (
                    <span className="tricks-cost">
                        -{decision.tricks_cost} trick{decision.tricks_cost !== 1 ? 's' : ''}
                    </span>
                )}
                {isSignalFeedback && !suppressSignalFeedback && (
                    <span className="signal-warning-badge" style={{
                        marginLeft: '8px',
                        padding: '2px 6px',
                        backgroundColor: '#fffaf0',
                        border: '1px solid #fbd38d',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: '#9c4221'
                    }}>
                        Signal
                    </span>
                )}
            </div>

            <div className="feedback-body">
                <div className="play-comparison">
                    <span className="played-card">
                        <strong>{positionName} played:</strong> {decision.user_card}
                    </span>
                    {decision.optimal_card && decision.optimal_card !== decision.user_card && (
                        <span className="optimal-card">
                            <strong>Better:</strong> {decision.optimal_card}
                        </span>
                    )}
                </div>

                {decision.feedback && (
                    <p className="feedback-text">{decision.feedback}</p>
                )}

                <HeuristicScorecard decision={decision} />
            </div>
        </div>
    );
};

const HandReviewPage = ({
    handId,
    onBack,
    onPrevHand,
    onNextHand,
    currentIndex,
    totalHands
}) => {
    const [handData, setHandData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [replayPosition, setReplayPosition] = useState(0);

    // Fetch hand details
    useEffect(() => {
        const fetchHandDetail = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE}/api/hand-detail?hand_id=${handId}`);
                if (!response.ok) throw new Error('Failed to load hand');
                const data = await response.json();
                setHandData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (handId) {
            fetchHandDetail();
        }
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

    const userControlledPositions = useMemo(() => {
        return handData?.user_controlled_positions || ['S'];
    }, [handData?.user_controlled_positions]);

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

    const trumpStrain = useMemo(() => {
        if (!handData?.contract) return 'NT';
        const match = handData.contract.match(/\d([SHDC♠♥♦♣]|NT)/i);
        if (match) {
            const s = match[1].toUpperCase();
            if (s === 'NT') return 'NT';
            const strainMap = { 'S': 'S', '♠': 'S', 'H': 'H', '♥': 'H', 'D': 'D', '♦': 'D', 'C': 'C', '♣': 'C' };
            return strainMap[s] || 'NT';
        }
        return 'NT';
    }, [handData?.contract]);

    const remainingHands = useMemo(() => {
        if (!handData?.deal || !handData?.play_history) return null;

        const hands = {
            N: [...(handData.deal.N?.hand || [])],
            E: [...(handData.deal.E?.hand || [])],
            S: [...(handData.deal.S?.hand || [])],
            W: [...(handData.deal.W?.hand || [])]
        };

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
    }, [handData?.deal, handData?.play_history, replayPosition]);

    const currentReplayTrick = useMemo(() => {
        if (!handData?.play_history || replayPosition === 0) return [];
        const lastPlayedIdx = replayPosition - 1;
        const trickStartIdx = Math.floor(lastPlayedIdx / 4) * 4;
        const cardsInTrick = (lastPlayedIdx % 4) + 1;
        return handData.play_history.slice(trickStartIdx, trickStartIdx + cardsInTrick);
    }, [handData?.play_history, replayPosition]);

    const currentReplayTrickNumber = replayPosition === 0 ? 1 : Math.floor((replayPosition - 1) / 4) + 1;

    const currentReplayLeader = useMemo(() => {
        if (!handData?.play_history || replayPosition === 0) return null;
        const lastPlayedIdx = replayPosition - 1;
        const trickStartIdx = Math.floor(lastPlayedIdx / 4) * 4;
        if (trickStartIdx < handData.play_history.length) {
            return handData.play_history[trickStartIdx]?.player || handData.play_history[trickStartIdx]?.position;
        }
        return null;
    }, [handData?.play_history, replayPosition]);

    const currentReplayDecision = useMemo(() => {
        if (!handData?.play_history || replayPosition === 0) return null;

        const lastPlayedIdx = replayPosition - 1;
        const lastPlay = handData.play_history[lastPlayedIdx];
        if (!lastPlay) return null;

        const trickNum = Math.floor(lastPlayedIdx / 4) + 1;
        const position = lastPlay.player || lastPlay.position;

        if (!userControlledPositions.includes(position)) return null;

        const key = `${trickNum}_${position}`;
        const storedDecision = decisionsByTrickAndPosition[key];

        if (storedDecision) return storedDecision;

        const cardRank = lastPlay.rank || lastPlay.r;
        const cardSuit = normalizeSuit(lastPlay.suit || lastPlay.s);
        return {
            position: position,
            trick_number: trickNum,
            user_card: `${cardRank}${cardSuit}`,
            rating: null,
            score: null,
            feedback: `${position === 'N' ? 'North' : 'South'} played ${cardRank}${cardSuit}`,
            is_basic_info: true
        };
    }, [handData?.play_history, replayPosition, userControlledPositions, decisionsByTrickAndPosition]);

    const totalPlays = handData?.play_history?.length || 0;

    const userRole = useMemo(() => {
        if (!handData) return 'Unknown';
        if (handData.user_role) return handData.user_role;
        const declarer = handData.contract_declarer;
        if (declarer === 'S' || declarer === 'N') return 'Declarer';
        return 'Defender';
    }, [handData]);

    const isUserDefender = userRole === 'Defender';

    const getScoreForUser = () => {
        const score = handData?.hand_score || 0;
        const declarer = handData?.contract_declarer;
        if (declarer === 'E' || declarer === 'W') {
            return -score;
        }
        return score;
    };

    const getResultForUser = () => {
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
    };

    const handleKeyDown = useCallback((e) => {
        if (e.key === 'Escape' && onBack) {
            onBack();
            return;
        }

        if (e.key === 'ArrowLeft' && replayPosition > 0) {
            setReplayPosition(p => p - 1);
        } else if (e.key === 'ArrowRight' && replayPosition < totalPlays) {
            setReplayPosition(p => p + 1);
        } else if (e.key === 'Home') {
            setReplayPosition(0);
        } else if (e.key === 'End') {
            setReplayPosition(totalPlays);
        }
    }, [replayPosition, totalPlays, onBack]);

    useEffect(() => {
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);

    if (loading) {
        return (
            <div className="hand-review-page">
                <div className="loading-state">Loading hand...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="hand-review-page">
                <div className="error-state">
                    <p>Error: {error}</p>
                    <button onClick={onBack}>Go Back</button>
                </div>
            </div>
        );
    }

    return (
        <div className="hand-review-page">
            {/* Page Header */}
            <div className="page-header">
                <div className="page-header-inner">
                    <button className="back-button" onClick={onBack} aria-label="Go back">
                        ← Back
                    </button>
                    <div className="page-title">
                        <h1>Play-by-Play Review</h1>
                        <ChartHelp chartType="play-review" variant="icon" />
                    </div>
                    {/* Hand navigation */}
                    {totalHands > 1 && (
                        <div className="hand-navigation">
                            <button
                                className="hand-nav-btn"
                                onClick={onPrevHand}
                                disabled={!onPrevHand}
                                aria-label="Previous hand"
                            >
                                ◀ Prev
                            </button>
                            <div className="hand-nav-counter">
                                <span className="hand-nav-label">Hand</span>
                                <span className="hand-nav-value">{currentIndex + 1} / {totalHands}</span>
                            </div>
                            <button
                                className="hand-nav-btn"
                                onClick={onNextHand}
                                disabled={!onNextHand}
                                aria-label="Next hand"
                            >
                                Next ▶
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Contract Info Bar */}
            <div className="contract-info-bar">
                <div className="contract-info-bar-inner">
                    <span className="contract">
                        {handData?.contract || 'Unknown'}
                    </span>
                    {(() => {
                        const result = getResultForUser();
                        return (
                            <span className={`result ${result.isGood ? 'made' : 'down'}`}>
                                {result.text}
                                {result.detail && <> {result.detail}</>}
                            </span>
                        );
                    })()}
                    <span className="role-badge">{userRole}</span>
                    {handData?.par_comparison?.dd_tricks !== undefined && (
                        <span className="dd-badge" title="Perfect play tricks possible">
                            Best: {handData.par_comparison.dd_tricks}
                        </span>
                    )}
                    {handData?.hand_score !== undefined && (() => {
                        const userScore = getScoreForUser();
                        return (
                            <span className={`score-badge ${userScore >= 0 ? 'positive' : 'negative'}`}>
                                {userScore > 0 ? '+' : ''}{userScore}
                            </span>
                        );
                    })()}
                    {handData?.play_quality_summary?.has_data && (
                        <span className="accuracy-badge">{handData.play_quality_summary.accuracy_rate}% play</span>
                    )}
                    {handData?.bidding_quality_summary?.has_data && (
                        <span className="accuracy-badge bidding">{handData.bidding_quality_summary.accuracy_rate}% bid</span>
                    )}
                </div>
            </div>

            {/* Content Area */}
            <div className="page-content">
              <div className="page-content-inner">
                {/* Navigation controls */}
                {tricks.length > 0 && (
                    <div className="replay-navigation">
                        <button
                            disabled={replayPosition <= 0}
                            onClick={() => setReplayPosition(0)}
                            aria-label="Go to start"
                            title="Go to start (Home)"
                        >
                            ⏮
                        </button>
                        <button
                            disabled={replayPosition <= 0}
                            onClick={() => setReplayPosition(p => p - 1)}
                            aria-label="Previous card"
                        >
                            ← Prev
                        </button>
                        <span className="replay-counter">
                            {replayPosition === 0 ? (
                                'Start • All cards dealt'
                            ) : (
                                <>
                                    Play {replayPosition} of {totalPlays}
                                    <span className="trick-indicator"> (Trick {currentReplayTrickNumber})</span>
                                </>
                            )}
                        </span>
                        <button
                            disabled={replayPosition >= totalPlays}
                            onClick={() => setReplayPosition(p => p + 1)}
                            aria-label="Next card"
                            data-testid="replay-next-btn"
                        >
                            Next →
                        </button>
                        <button
                            disabled={replayPosition >= totalPlays}
                            onClick={() => setReplayPosition(totalPlays)}
                            aria-label="Go to end"
                            title="Go to end (End)"
                        >
                            ⏭
                        </button>
                    </div>
                )}

                {/* Main display area - compass layout with hands */}
                {remainingHands && (
                    <div className="replay-table-compass">
                        {/* North hand */}
                        <div className="replay-row replay-row-north">
                            <div className="replay-position">
                                <ReplayHandDisplay
                                    cards={remainingHands.N}
                                    position="N"
                                    trumpStrain={trumpStrain}
                                    isVertical={false}
                                />
                            </div>
                        </div>

                        {/* Middle row: West - Trick/Info - East */}
                        <div className="replay-row replay-row-middle">
                            <div className="replay-position replay-west">
                                <ReplayHandDisplay
                                    cards={remainingHands.W}
                                    position="W"
                                    trumpStrain={trumpStrain}
                                    isVertical={true}
                                />
                            </div>

                            <div className="replay-center">
                                {replayPosition === 0 ? (
                                    <div className="center-info-box">
                                        <div className="center-contract">{handData?.contract}</div>
                                        <div className="center-vulnerability">Vul: {handData?.vulnerability || 'None'}</div>
                                        <div className="center-dealer">Dealer: {handData?.dealer}</div>
                                    </div>
                                ) : (
                                    <ReplayTrickDisplay
                                        trick={currentReplayTrick}
                                        leader={currentReplayLeader}
                                    />
                                )}
                            </div>

                            <div className="replay-position replay-east">
                                <ReplayHandDisplay
                                    cards={remainingHands.E}
                                    position="E"
                                    trumpStrain={trumpStrain}
                                    isVertical={true}
                                />
                            </div>
                        </div>

                        {/* South hand */}
                        <div className="replay-row replay-row-south">
                            <div className="replay-position">
                                <ReplayHandDisplay
                                    cards={remainingHands.S}
                                    position="S"
                                    trumpStrain={trumpStrain}
                                    isVertical={false}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Feedback panel */}
                {tricks.length > 0 && (
                    <div className="trick-feedback-container" data-testid="trick-feedback-container">
                        {replayPosition === 0 ? (
                            <div className="replay-start-hint" data-testid="replay-start-hint">
                                <p>Press <strong>Next →</strong> or use arrow keys to step through each play and see feedback.</p>
                            </div>
                        ) : currentReplayDecision ? (
                            <TrickFeedbackPanel decision={currentReplayDecision} />
                        ) : (
                            <div className="trick-feedback-panel no-data" data-testid="trick-feedback-ai-play">
                                <p>AI play - no feedback recorded</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Decay Chart */}
                {handData?.decay_curve && (
                    <DecayChart
                        data={handData.decay_curve}
                        replayPosition={replayPosition}
                        onPositionChange={setReplayPosition}
                    />
                )}
              </div>
            </div>
        </div>
    );
};

export default HandReviewPage;
