/**
 * BeliefPanel Component
 *
 * Displays inferred beliefs about partner's and opponents' hands
 * based on the bidding auction. Collapsed by default; expands to
 * show HCP ranges, suit lengths, convention tags, combined HCP
 * estimate, and an optional "How?" reasoning timeline.
 */

import React, { useState } from 'react';
import './BeliefPanel.css';

// ── Seat name mapping ──

const SEAT_FULL_NAMES = {
  'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West',
  'North': 'North', 'East': 'East', 'South': 'South', 'West': 'West',
};

function seatName(seat) {
  return SEAT_FULL_NAMES[seat] || seat;
}

// ── Suit display helpers ──

const SUIT_SYMBOLS = {
  '\u2660': { sym: '\u2660', color: 'black' },  // ♠
  '\u2665': { sym: '\u2665', color: 'red' },     // ♥
  '\u2666': { sym: '\u2666', color: 'red' },     // ♦
  '\u2663': { sym: '\u2663', color: 'black' },   // ♣
};

const SUIT_ORDER = ['\u2660', '\u2665', '\u2666', '\u2663'];

// Convention-related tags (displayed with cyan styling)
const CONVENTION_TAGS = new Set([
  'stayman_asked', 'stayman_no_major', 'stayman_hearts', 'stayman_spades',
  'jacoby_hearts', 'jacoby_spades', 'blackwood_asked', 'blackwood_response',
]);

// Weakness tags
const WEAK_TAGS = new Set(['weak_two', 'preempt', 'preemptive_raise']);

// Limited tags
const LIMITED_TAGS = new Set(['passed_opening', 'passed_response', 'limit_raise']);

function getTagClass(tag) {
  if (CONVENTION_TAGS.has(tag)) return 'convention';
  if (WEAK_TAGS.has(tag)) return 'weak';
  if (LIMITED_TAGS.has(tag)) return 'limited';
  return 'hand-type';
}

function formatTag(tag) {
  return tag.replace(/_/g, ' ');
}

// ── HCP bar helpers ──

function getHcpBarClass(min, max) {
  const spread = max - min;
  if (spread <= 5) return 'tight';
  if (spread <= 12) return 'medium';
  return 'wide';
}

function getHcpBarStyle(min, max) {
  const left = (min / 40) * 100;
  const width = ((max - min) / 40) * 100;
  return { left: `${left}%`, width: `${Math.max(width, 2)}%` };
}

// ── Suit cell helpers ──

function isSuitConstrained(suitData) {
  return suitData.min > 0 || suitData.max < 13;
}

function getSuitCellClass(suitData, tags) {
  if (!isSuitConstrained(suitData)) return '';
  // Check if constraint came from a convention
  const hasConventionTag = tags && tags.some(t => CONVENTION_TAGS.has(t));
  return hasConventionTag ? 'convention-constrained' : 'constrained';
}

function getSuitRangeClass(suitData, tags) {
  if (!isSuitConstrained(suitData)) return '';
  const hasConventionTag = tags && tags.some(t => CONVENTION_TAGS.has(t));
  return hasConventionTag ? 'convention-known' : 'known';
}

// ── Bid tag color helper ──

function getBidTagClass(bid) {
  if (!bid || bid === 'Pass') return 'pass';
  if (bid.includes('\u2665') || bid.includes('\u2666')) return 'red';
  return 'black';
}

// ── Field label formatter ──

function formatFieldLabel(field) {
  if (field === 'hcp') return 'HCP';
  if (field.startsWith('suit:')) {
    const suit = field.slice(5);
    const info = SUIT_SYMBOLS[suit];
    return info ? info.sym : suit;
  }
  return field;
}

function formatRange(rangeObj) {
  return `${rangeObj.min}\u2013${rangeObj.max}`;
}

// ── Combined HCP verdict ──

function getCombinedVerdict(min, max) {
  const mid = Math.round((min + max) / 2);
  if (mid >= 33) return { label: 'Slam Zone', cls: 'slam' };
  if (mid >= 25) return { label: 'Game', cls: 'game' };
  if (mid >= 23) return { label: 'Invite', cls: 'invite' };
  return null;
}

// ═══════════════════════════════════════════
// SeatBeliefView — renders one seat's beliefs
// ═══════════════════════════════════════════

function SeatBeliefView({ belief, showHow = true }) {
  const [showReasoning, setShowReasoning] = useState(false);

  if (!belief) return null;

  const hcp = belief.hcp || { min: 0, max: 40 };
  const suits = belief.suits || {};
  const tags = belief.tags || [];
  const reasoning = belief.reasoning || [];
  const hasReasoning = reasoning.length > 0;

  return (
    <>
      {/* Tags */}
      {tags.length > 0 && (
        <div className="beliefs-tags-row">
          {tags.map((tag, i) => (
            <span key={i} className={`belief-tag ${getTagClass(tag)}`}>
              {formatTag(tag)}
            </span>
          ))}
        </div>
      )}

      {/* HCP range */}
      <div className="beliefs-hcp-section">
        <div className="beliefs-hcp-label">HCP Range</div>
        <div className="beliefs-hcp-range-row">
          <div className="beliefs-hcp-bar-track">
            <div
              className={`beliefs-hcp-bar-fill ${getHcpBarClass(hcp.min, hcp.max)}`}
              style={getHcpBarStyle(hcp.min, hcp.max)}
            />
          </div>
          <div className="beliefs-hcp-values">
            {hcp.min}<span className="sep">&ndash;</span>{hcp.max}
          </div>
        </div>
      </div>

      {/* Suit lengths */}
      <div className="beliefs-suits-section">
        <div className="beliefs-suits-label">Suit Lengths</div>
        <div className="beliefs-suits-grid">
          {SUIT_ORDER.map(suit => {
            const suitData = suits[suit] || { min: 0, max: 13 };
            const info = SUIT_SYMBOLS[suit];
            const constrained = isSuitConstrained(suitData);
            return (
              <div key={suit} className={`beliefs-suit-cell ${getSuitCellClass(suitData, tags)}`}>
                <div className={`beliefs-suit-icon ${info.color}`}>{info.sym}</div>
                <div className="beliefs-suit-range">
                  {constrained ? (
                    <span className={getSuitRangeClass(suitData, tags)}>
                      {suitData.min === suitData.max ? suitData.min : `${suitData.min}\u2013${suitData.max}`}
                    </span>
                  ) : (
                    '0\u201313'
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* How? button + reasoning timeline */}
      {showHow && hasReasoning && (
        <>
          <button
            className={`beliefs-how-button ${showReasoning ? 'active' : ''}`}
            onClick={() => setShowReasoning(!showReasoning)}
          >
            {showReasoning ? 'Hide' : 'How?'}
          </button>

          {showReasoning && (
            <div className="beliefs-reasoning-panel">
              <div className="beliefs-reasoning-title">Reasoning Chain</div>
              <div className="beliefs-reasoning-timeline">
                {reasoning.map((step, i) => (
                  <div key={i} className="beliefs-reasoning-step">
                    <span className={`beliefs-step-bid-tag ${getBidTagClass(step.bid)}`}>
                      {step.bid || '?'}
                    </span>
                    <span className="beliefs-step-reason">{step.reason}</span>
                    <div className="beliefs-step-change">
                      <span className="field-label">{formatFieldLabel(step.field)}</span>
                      <span className="before">{formatRange(step.before)}</span>
                      <span className="arrow">&rarr;</span>
                      <span className="after">{formatRange(step.after)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
}

// ═══════════════════════════════════════════
// BeliefPanel — main export
// ═══════════════════════════════════════════

const BeliefPanel = ({ beliefs, myHcp }) => {
  const [partnerExpanded, setPartnerExpanded] = useState(false);
  const [opponentsExpanded, setOpponentsExpanded] = useState(false);

  if (!beliefs) return null;

  const partner = beliefs.partner;
  const lho = beliefs.lho;
  const rho = beliefs.rho;

  // Check if any seat has non-default beliefs (at least one narrowing happened)
  const hasPartnerBeliefs = partner && (
    partner.hcp?.min > 0 || partner.hcp?.max < 40 ||
    (partner.tags && partner.tags.length > 0)
  );
  const hasOpponentBeliefs = (lho && (lho.hcp?.min > 0 || lho.hcp?.max < 40 || (lho.tags && lho.tags.length > 0))) ||
    (rho && (rho.hcp?.min > 0 || rho.hcp?.max < 40 || (rho.tags && rho.tags.length > 0)));

  if (!hasPartnerBeliefs && !hasOpponentBeliefs) return null;

  // Combined HCP for partner panel
  const partnerMid = partner ? Math.round((partner.hcp.min + partner.hcp.max) / 2) : 0;
  const combinedMin = (myHcp || 0) + (partner?.hcp?.min || 0);
  const combinedMax = (myHcp || 0) + (partner?.hcp?.max || 0);
  const combinedMid = (myHcp || 0) + partnerMid;
  const verdict = getCombinedVerdict(combinedMin, combinedMax);

  return (
    <>
      {/* ── Partner panel ── */}
      {hasPartnerBeliefs && (
        partnerExpanded ? (
          <div className="beliefs-panel partner">
            <div className="beliefs-header">
              <div className="beliefs-title">
                <span className="beliefs-title-icon">{'\u265F'}</span>
                Partner&apos;s Likely Hand ({seatName(partner?.seat)})
              </div>
              <div className="beliefs-header-buttons">
                <button className="beliefs-toggle" onClick={() => setPartnerExpanded(false)}>
                  Collapse {'\u25B4'}
                </button>
              </div>
            </div>

            <SeatBeliefView belief={partner} />

            {/* Combined footer */}
            {myHcp != null && (
              <div className="beliefs-combined-footer">
                <span className="beliefs-combined-label">Combined HCP (you + partner)</span>
                <span className={`beliefs-combined-value ${verdict?.cls || ''}`}>
                  {combinedMin}&ndash;{combinedMax} (~{combinedMid})
                </span>
                {verdict && (
                  <span className={`beliefs-verdict-chip ${verdict.cls}`}>
                    {verdict.label}
                  </span>
                )}
              </div>
            )}
          </div>
        ) : (
          <div
            className="beliefs-collapsed partner"
            onClick={() => setPartnerExpanded(true)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && setPartnerExpanded(true)}
          >
            <div className="beliefs-collapsed-left">
              <span className="beliefs-collapsed-icon">{'\u265F'}</span>
              <span className="beliefs-collapsed-label">Partner&apos;s Likely Hand</span>
            </div>
            <span className="beliefs-collapsed-expand">Expand {'\u25BE'}</span>
          </div>
        )
      )}

      {/* ── Opponents panel ── */}
      {hasOpponentBeliefs && (
        opponentsExpanded ? (
          <div className="beliefs-panel opponents">
            <div className="beliefs-header">
              <div className="beliefs-title">
                <span className="beliefs-title-icon">{'\u2694'}</span>
                Opponents&apos; Likely Hands
              </div>
              <div className="beliefs-header-buttons">
                <button className="beliefs-toggle" onClick={() => setOpponentsExpanded(false)}>
                  Collapse {'\u25B4'}
                </button>
              </div>
            </div>

            {/* LHO */}
            {lho && (lho.hcp?.min > 0 || lho.hcp?.max < 40 || (lho.tags && lho.tags.length > 0)) && (
              <div className="beliefs-opponent-seat">
                <div className="beliefs-seat-label">
                  Left-Hand Opponent ({lho.seat})
                </div>
                <SeatBeliefView belief={lho} />
              </div>
            )}

            {/* Divider between opponents if both have beliefs */}
            {lho && rho &&
              (lho.hcp?.min > 0 || lho.hcp?.max < 40 || (lho.tags && lho.tags.length > 0)) &&
              (rho.hcp?.min > 0 || rho.hcp?.max < 40 || (rho.tags && rho.tags.length > 0)) && (
              <hr className="beliefs-opponent-divider" />
            )}

            {/* RHO */}
            {rho && (rho.hcp?.min > 0 || rho.hcp?.max < 40 || (rho.tags && rho.tags.length > 0)) && (
              <div className="beliefs-opponent-seat">
                <div className="beliefs-seat-label">
                  Right-Hand Opponent ({rho.seat})
                </div>
                <SeatBeliefView belief={rho} />
              </div>
            )}
          </div>
        ) : (
          <div
            className="beliefs-collapsed opponents"
            onClick={() => setOpponentsExpanded(true)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && setOpponentsExpanded(true)}
          >
            <div className="beliefs-collapsed-left">
              <span className="beliefs-collapsed-icon">{'\u2694'}</span>
              <span className="beliefs-collapsed-label">Opponents&apos; Likely Hands</span>
            </div>
            <span className="beliefs-collapsed-expand">Expand {'\u25BE'}</span>
          </div>
        )
      )}
    </>
  );
};

export default BeliefPanel;

// Export SeatBeliefView for use in other components (e.g., CoachPanel)
export { SeatBeliefView, SUIT_SYMBOLS, SUIT_ORDER };
