/**
 * ConventionReference - Quick SAYC Rule Lookup
 *
 * P1 Feature: Hot-key reference button in South affordance zone.
 * Shows the SAYC rule for the last bid made in the auction.
 *
 * Usage: Click the 📖 icon to see convention reference for last bid.
 */

import React, { useMemo } from 'react';
import './ConventionReference.css';

// SAYC Convention Rules Database
const SAYC_RULES = {
  // Opening bids
  '1♣': {
    title: '1♣ Opening',
    requirement: '12-21 HCP, 3+ clubs (may be shorter with 4-4-3-2)',
    meaning: 'Opening bid showing club length. Could be as few as 2 clubs with 4-4-3-2 shape.',
    responses: ['1♦/1♥/1♠: 6+ HCP, 4+ cards', '1NT: 6-10 HCP, balanced', '2♣: 10+ HCP, 5+ clubs'],
  },
  '1♦': {
    title: '1♦ Opening',
    requirement: '12-21 HCP, 4+ diamonds (3+ if no 5-card major)',
    meaning: 'Natural opening showing diamond length.',
    responses: ['1♥/1♠: 6+ HCP, 4+ cards', '1NT: 6-10 HCP, balanced', '2♦: 10+ HCP, 5+ diamonds'],
  },
  '1♥': {
    title: '1♥ Opening',
    requirement: '12-21 HCP, 5+ hearts',
    meaning: 'Natural opening showing a 5-card heart suit.',
    responses: ['1♠: 6+ HCP, 4+ spades', '1NT: 6-10 HCP, denies 3 hearts', '2♥: 6-10 HCP, 3+ hearts', '3♥: 10-12 HCP, 4+ hearts (limit raise)'],
  },
  '1♠': {
    title: '1♠ Opening',
    requirement: '12-21 HCP, 5+ spades',
    meaning: 'Natural opening showing a 5-card spade suit.',
    responses: ['1NT: 6-10 HCP, denies 3 spades', '2♠: 6-10 HCP, 3+ spades', '3♠: 10-12 HCP, 4+ spades (limit raise)'],
  },
  '1NT': {
    title: '1NT Opening',
    requirement: '15-17 HCP, balanced',
    meaning: 'Shows a balanced hand with 15-17 HCP. No 5-card major.',
    responses: ['2♣: Stayman (asks for 4-card major)', '2♦: Transfer to hearts', '2♥: Transfer to spades', '2NT: 8-9 HCP, invitational', '3NT: 10-15 HCP, to play'],
  },
  '2♣': {
    title: 'Strong 2♣ Opening',
    requirement: '22+ HCP, or 9+ tricks',
    meaning: 'Artificial and forcing. Shows a very strong hand.',
    responses: ['2♦: Waiting (negative or neutral)', '2NT: 8+ HCP, balanced positive', '2♥/2♠/3♣/3♦: Natural positive, 5+ cards'],
  },
  '2♦': {
    title: 'Weak Two in Diamonds',
    requirement: '5-11 HCP, 6 diamonds',
    meaning: 'Preemptive opening showing a weak hand with a 6-card diamond suit.',
    responses: ['2NT: Forcing, asks for feature', '3♦: Preemptive raise', '4♦: Preemptive raise'],
  },
  '2♥': {
    title: 'Weak Two in Hearts',
    requirement: '5-11 HCP, 6 hearts',
    meaning: 'Preemptive opening showing a weak hand with a 6-card heart suit.',
    responses: ['2NT: Forcing, asks for feature', '3♥: Preemptive raise', '4♥: To play'],
  },
  '2♠': {
    title: 'Weak Two in Spades',
    requirement: '5-11 HCP, 6 spades',
    meaning: 'Preemptive opening showing a weak hand with a 6-card spade suit.',
    responses: ['2NT: Forcing, asks for feature', '3♠: Preemptive raise', '4♠: To play'],
  },
  '2NT': {
    title: '2NT Opening',
    requirement: '20-21 HCP, balanced',
    meaning: 'Shows a balanced hand with 20-21 HCP.',
    responses: ['3♣: Stayman', '3♦: Transfer to hearts', '3♥: Transfer to spades', '3NT: To play'],
  },
  // Conventions
  'Stayman': {
    title: 'Stayman Convention (2♣)',
    requirement: 'Response to 1NT/2NT, 8+ HCP',
    meaning: 'Asks opener if they have a 4-card major.',
    responses: ['2♦: No 4-card major', '2♥: 4+ hearts', '2♠: 4+ spades'],
  },
  'Transfer': {
    title: 'Jacoby Transfer',
    requirement: 'Response to 1NT, 5+ card major',
    meaning: '2♦ = transfer to hearts (2♥), 2♥ = transfer to spades (2♠).',
    responses: ['Opener bids the major at the 2-level'],
  },
  'Blackwood': {
    title: 'Blackwood (4NT)',
    requirement: 'Asks for aces when slam is possible',
    meaning: 'Conventional ace-asking bid.',
    responses: ['5♣: 0 or 4 aces', '5♦: 1 ace', '5♥: 2 aces', '5♠: 3 aces'],
  },
  // Passes and doubles
  'Pass': {
    title: 'Pass',
    requirement: 'No forcing obligation to bid',
    meaning: 'Shows inability or unwillingness to bid at this time.',
    responses: [],
  },
  'X': {
    title: 'Double',
    requirement: 'Context-dependent',
    meaning: 'Takeout double (of opening bid) shows 12+ HCP and support for unbid suits, OR penalty double (late in auction).',
    responses: ['Partner should bid their best suit (takeout)', 'Pass if penalty expected'],
  },
  'XX': {
    title: 'Redouble',
    requirement: 'After partner opens and opponent doubles',
    meaning: 'Shows 10+ HCP, suggests penalty possibilities.',
    responses: [],
  },
};

// Get rule for a bid
function getRuleForBid(bid) {
  if (!bid) return null;

  // Direct match
  if (SAYC_RULES[bid]) return SAYC_RULES[bid];

  // Check for suit bid patterns
  const level = bid.match(/^(\d)/)?.[1];
  const strain = bid.replace(/^\d/, '');

  // Map to base rules
  if (level === '1' && ['♣', '♦', '♥', '♠'].includes(strain)) {
    return SAYC_RULES[bid] || null;
  }

  // Check for NT bids
  if (strain === 'NT') {
    return SAYC_RULES[bid] || null;
  }

  return null;
}

export default function ConventionReference({ lastBid, onClose }) {
  const rule = useMemo(() => getRuleForBid(lastBid), [lastBid]);

  if (!rule) {
    return (
      <div className="convention-ref-panel">
        <div className="convention-ref-header">
          <h4>Convention Reference</h4>
          <button className="ref-close" onClick={onClose}>×</button>
        </div>
        <div className="convention-ref-content empty">
          <p>No reference available for "{lastBid || 'no bid'}".</p>
          <p className="ref-hint">Click on a bid in the auction to see its meaning.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="convention-ref-panel">
      <div className="convention-ref-header">
        <h4>{rule.title}</h4>
        <button className="ref-close" onClick={onClose}>×</button>
      </div>

      <div className="convention-ref-content">
        <div className="ref-section">
          <span className="ref-label">Requirement</span>
          <span className="ref-value">{rule.requirement}</span>
        </div>

        <div className="ref-section">
          <span className="ref-label">Meaning</span>
          <p className="ref-text">{rule.meaning}</p>
        </div>

        {rule.responses && rule.responses.length > 0 && (
          <div className="ref-section">
            <span className="ref-label">Responses</span>
            <ul className="ref-responses">
              {rule.responses.map((resp, i) => (
                <li key={i}>{resp}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// Button to trigger reference popup
export function ConventionReferenceButton({ onClick, disabled }) {
  return (
    <button
      className="convention-ref-button"
      onClick={onClick}
      disabled={disabled}
      title="Convention Reference (last bid)"
      aria-label="Show convention reference"
    >
      📖
    </button>
  );
}
