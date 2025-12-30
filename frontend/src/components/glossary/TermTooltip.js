/**
 * TermTooltip Component
 *
 * Provides contextual definitions for bridge terms inline in text.
 *
 * Features:
 * - Desktop: Hover to preview, click to pin
 * - Mobile: Tap to show, tap outside to dismiss
 * - Links to full glossary entry
 * - Senior-friendly option with larger text
 *
 * Usage:
 *   <TermTooltip term="stayman">Stayman</TermTooltip>
 *   <TermTooltip term="hcp" showIcon>HCP</TermTooltip>
 */

import React, { useState, useRef, useEffect } from 'react';
import './TermTooltip.css';
import { getTermById, DIFFICULTY_LEVELS } from '../../data/bridgeGlossary';

const TermTooltip = ({
  term,           // Term ID to look up in glossary
  children,       // Display text (usually the term name)
  showIcon = false, // Show (?) icon after text
  onOpenGlossary, // Optional callback to open glossary drawer
  seniorMode = false,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef(null);
  const tooltipRef = useRef(null);

  // Get term data from glossary
  const termData = getTermById(term);

  // Calculate tooltip position
  const calculatePosition = () => {
    if (!triggerRef.current) return;

    const rect = triggerRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const tooltipWidth = 280;
    const tooltipHeight = 150; // Approximate

    let top = rect.bottom + 8;
    let left = rect.left;

    // Adjust horizontal position if needed
    if (left + tooltipWidth > viewportWidth - 20) {
      left = viewportWidth - tooltipWidth - 20;
    }
    if (left < 20) {
      left = 20;
    }

    // Flip to top if not enough space below
    if (top + tooltipHeight > viewportHeight - 20) {
      top = rect.top - tooltipHeight - 8;
    }

    setPosition({ top, left });
  };

  // Handle mouse enter (desktop)
  const handleMouseEnter = () => {
    if (!isPinned) {
      calculatePosition();
      setIsVisible(true);
    }
  };

  // Handle mouse leave (desktop)
  const handleMouseLeave = () => {
    if (!isPinned) {
      setIsVisible(false);
    }
  };

  // Handle click (toggle pin)
  const handleClick = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (isPinned) {
      setIsPinned(false);
      setIsVisible(false);
    } else {
      calculatePosition();
      setIsPinned(true);
      setIsVisible(true);
    }
  };

  // Close on click outside when pinned
  useEffect(() => {
    if (!isPinned) return;

    const handleClickOutside = (e) => {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(e.target) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target)
      ) {
        setIsPinned(false);
        setIsVisible(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isPinned]);

  // Close on escape key
  useEffect(() => {
    if (!isPinned) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsPinned(false);
        setIsVisible(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isPinned]);

  // If term not found, just render children
  if (!termData) {
    return <span>{children}</span>;
  }

  return (
    <>
      {/* Trigger Element */}
      <span
        ref={triggerRef}
        className={`term-trigger ${seniorMode ? 'senior-mode' : ''}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-describedby={isVisible ? `tooltip-${term}` : undefined}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleClick(e);
          }
        }}
      >
        {children}
        {showIcon && <span className="help-icon">?</span>}
      </span>

      {/* Tooltip */}
      {isVisible && (
        <div
          ref={tooltipRef}
          id={`tooltip-${term}`}
          className={`term-tooltip ${seniorMode ? 'senior-mode' : ''} ${isPinned ? 'pinned' : ''}`}
          style={{
            top: position.top,
            left: position.left,
          }}
          role="tooltip"
        >
          {/* Header */}
          <div className="tooltip-header">
            <span className="tooltip-term">{termData.term}</span>
            <span className={`tooltip-difficulty ${termData.difficulty}`}>
              {DIFFICULTY_LEVELS[termData.difficulty].label}
            </span>
          </div>

          {/* Definition */}
          <p className="tooltip-definition">{termData.definition}</p>

          {/* Example (if available) */}
          {termData.example && (
            <p className="tooltip-example">
              <em>Ex: {termData.example}</em>
            </p>
          )}

          {/* Footer with link to glossary */}
          {onOpenGlossary && (
            <button
              className="tooltip-more-link"
              onClick={(e) => {
                e.stopPropagation();
                setIsPinned(false);
                setIsVisible(false);
                onOpenGlossary(term);
              }}
            >
              See more in glossary →
            </button>
          )}

          {/* Close hint for pinned state */}
          {isPinned && (
            <span className="tooltip-hint">Click outside or press Esc to close</span>
          )}
        </div>
      )}
    </>
  );
};

/**
 * TermHighlight Component
 *
 * Auto-highlights recognized bridge terms in a text string.
 * Useful for paragraphs with multiple terms to highlight.
 *
 * Usage:
 *   <TermHighlight text="Count your HCP and check for a balanced hand." />
 */
export const TermHighlight = ({ text, onOpenGlossary, seniorMode }) => {
  // Comprehensive list of bridge terms to auto-detect
  // Ordered from most specific (multi-word) to least specific (single word) to avoid partial matches
  const detectableTerms = [
    // Multi-word terms first (more specific patterns)
    { pattern: /\brule of eleven\b/gi, termId: 'rule_of_eleven' },
    { pattern: /\brule of 11\b/gi, termId: 'rule_of_eleven' },
    { pattern: /\b4th best\b/gi, termId: 'fourth_best' },
    { pattern: /\bfourth best\b/gi, termId: 'fourth_best' },
    { pattern: /\btop of sequence\b/gi, termId: 'top_of_sequence' },
    { pattern: /\btop of nothing\b/gi, termId: 'top_of_nothing' },
    { pattern: /\bhigh card points?\b/gi, termId: 'hcp' },
    { pattern: /\bdistribution points?\b/gi, termId: 'distribution_points' },
    { pattern: /\btotal points?\b/gi, termId: 'total_points' },
    { pattern: /\bmajor suits?\b/gi, termId: 'major_suit' },
    { pattern: /\bminor suits?\b/gi, termId: 'minor_suit' },
    { pattern: /\btakeout doubles?\b/gi, termId: 'takeout_double' },
    { pattern: /\bnegative doubles?\b/gi, termId: 'negative_double' },
    { pattern: /\bpenalty doubles?\b/gi, termId: 'penalty_double' },
    { pattern: /\bopening leads?\b/gi, termId: 'opening_lead' },
    { pattern: /\bopening bids?\b/gi, termId: 'opening_bid' },
    { pattern: /\bhold[- ]?ups?\b/gi, termId: 'holdup' },
    { pattern: /\bfollow suits?\b/gi, termId: 'follow_suit' },
    { pattern: /\bdraw(ing)? trumps?\b/gi, termId: 'draw_trumps' },
    { pattern: /\bcross[- ]?ruffs?\b/gi, termId: 'cross_ruff' },
    { pattern: /\bsafety plays?\b/gi, termId: 'safety_play' },
    { pattern: /\bpercentage plays?\b/gi, termId: 'percentage_play' },
    { pattern: /\bstrip and endplay\b/gi, termId: 'strip_and_endplay' },
    { pattern: /\bdanger hands?\b/gi, termId: 'danger_hand' },
    { pattern: /\bgrand slams?\b/gi, termId: 'grand_slam' },
    { pattern: /\bsmall slams?\b/gi, termId: 'small_slam' },
    { pattern: /\bpart[- ]?scores?\b/gi, termId: 'part_score' },
    { pattern: /\bweak twos?\b/gi, termId: 'weak_two' },
    { pattern: /\bjump bids?\b/gi, termId: 'jump_bid' },
    { pattern: /\bjump shifts?\b/gi, termId: 'jump_shift' },
    { pattern: /\bcue[- ]?bids?\b/gi, termId: 'cue_bid' },
    { pattern: /\bcontrol bids?\b/gi, termId: 'control_bid' },
    { pattern: /\bsign[- ]?offs?\b/gi, termId: 'sign_off' },
    { pattern: /\blong suits?\b/gi, termId: 'long_suit' },
    { pattern: /\bshort suits?\b/gi, termId: 'short_suit' },
    { pattern: /\bflat hands?\b/gi, termId: 'flat_hand' },
    { pattern: /\bgolden fits?\b/gi, termId: 'golden_fit' },
    { pattern: /\bface cards?\b/gi, termId: 'face_card' },
    { pattern: /\bspot cards?\b/gi, termId: 'spot_card' },
    { pattern: /\bhonor cards?\b/gi, termId: 'honor' },
    { pattern: /\bcount signals?\b/gi, termId: 'count_signal' },
    { pattern: /\battitude signals?\b/gi, termId: 'attitude' },
    { pattern: /\bdouble dummy\b/gi, termId: 'double_dummy' },
    { pattern: /\broman keycard\b/gi, termId: 'roman_keycard' },
    { pattern: /\bnew minor forcing\b/gi, termId: 'new_minor_forcing' },
    { pattern: /\bfourth suit forcing\b/gi, termId: 'fourth_suit_forcing' },
    { pattern: /\bunusual 2NT\b/gi, termId: 'unusual_2nt' },
    { pattern: /\bmichaels cue[- ]?bid\b/gi, termId: 'michaels_cuebid' },
    { pattern: /\bJacoby transfers?\b/gi, termId: 'jacoby_transfer' },
    { pattern: /\bwaiting bids?\b/gi, termId: 'waiting_bid' },
    { pattern: /\b2♦ waiting\b/gi, termId: 'waiting_bid' },
    { pattern: /\bcommunications?\b/gi, termId: 'communication' },
    { pattern: /\bestablish(ing|ed)? (a |the )?suits?\b/gi, termId: 'long_suit' },
    { pattern: /\bclear(ing|ed)? (the )?suits?\b/gi, termId: 'long_suit' },

    // Convention names
    { pattern: /\bStayman\b/gi, termId: 'stayman' },
    { pattern: /\bJacoby\b/gi, termId: 'jacoby_transfer' },
    { pattern: /\bBlackwood\b/gi, termId: 'blackwood' },
    { pattern: /\bGerber\b/gi, termId: 'gerber' },
    { pattern: /\bLebensohl\b/gi, termId: 'lebensohl' },
    { pattern: /\bDrury\b/gi, termId: 'drury' },
    { pattern: /\bMichaels\b/gi, termId: 'michaels_cuebid' },
    { pattern: /\bRKCB\b/gi, termId: 'roman_keycard' },

    // Acronyms and abbreviations
    { pattern: /\bHCP\b/g, termId: 'hcp' },
    { pattern: /\bMUD\b/g, termId: 'mud' },
    { pattern: /\bNT\b/g, termId: 'notrump' },
    { pattern: /\b[1-7]NT\b/gi, termId: 'notrump' },
    { pattern: /\bIMPs?\b/g, termId: 'imps' },
    { pattern: /\bLHO\b/g, termId: 'lho' },
    { pattern: /\bRHO\b/g, termId: 'rho' },
    { pattern: /\bleft[- ]?hand opponents?\b/gi, termId: 'lho' },
    { pattern: /\bright[- ]?hand opponents?\b/gi, termId: 'rho' },

    // Single-word terms (alphabetical for easier maintenance)
    { pattern: /\badvancer\b/gi, termId: 'advancer' },
    { pattern: /\bauctions?\b/gi, termId: 'auction' },
    { pattern: /\bavoidance\b/gi, termId: 'avoidance' },
    { pattern: /\bbalanced\b/gi, termId: 'balanced' },
    { pattern: /\bbalancing\b/gi, termId: 'balancing' },
    { pattern: /\bbonus(es)?\b/gi, termId: 'bonus' },
    { pattern: /\bcash(ing|ed)?\b/gi, termId: 'cash' },
    { pattern: /\bcontracts?\b/gi, termId: 'contract' },
    { pattern: /\bconventions?\b/gi, termId: 'convention' },
    { pattern: /\bcover(ing|ed)?\b/gi, termId: 'cover' },
    { pattern: /\bdealers?\b/gi, termId: 'dealer' },
    { pattern: /\bdeclarers?\b/gi, termId: 'declarer' },
    { pattern: /\bdefenders?\b/gi, termId: 'defender' },
    { pattern: /\bdiscards?\b/gi, termId: 'discard' },
    { pattern: /\bdouble(d|s)?\b/gi, termId: 'double' },
    { pattern: /\bdoubletons?\b/gi, termId: 'doubleton' },
    { pattern: /\bduck(ing|ed|s)?\b/gi, termId: 'duck' },
    { pattern: /\bdummy('s|ies)?\b/gi, termId: 'dummy' },
    { pattern: /\beliminations?\b/gi, termId: 'elimination' },
    { pattern: /\bendplays?\b/gi, termId: 'endplay' },
    { pattern: /\bentr(y|ies)\b/gi, termId: 'entry' },
    { pattern: /\bfinesses?\b/gi, termId: 'finesse' },
    { pattern: /\bfinessing\b/gi, termId: 'finesse' },
    { pattern: /\bfits?\b/gi, termId: 'fit' },
    { pattern: /\bforcing\b/gi, termId: 'forcing' },
    { pattern: /\bhonors?\b/gi, termId: 'honor' },
    { pattern: /\binferences?\b/gi, termId: 'inference' },
    { pattern: /\binvitational\b/gi, termId: 'invitational' },
    { pattern: /\blosers?\b/gi, termId: 'loser' },
    { pattern: /\bnotrump\b/gi, termId: 'notrump' },
    { pattern: /\bopeners?\b/gi, termId: 'opener' },
    { pattern: /\bovercalls?\b/gi, termId: 'overcall' },
    { pattern: /\bovertricks?\b/gi, termId: 'overtrick' },
    { pattern: /\bpenalt(y|ies)\b/gi, termId: 'penalty' },
    { pattern: /\bpreempts?\b/gi, termId: 'preempt' },
    { pattern: /\braises?\b/gi, termId: 'raise' },
    { pattern: /\brebids?\b/gi, termId: 'rebid' },
    { pattern: /\bredouble(d|s)?\b/gi, termId: 'redouble' },
    { pattern: /\bresponders?\b/gi, termId: 'responder' },
    { pattern: /\bresponses?\b/gi, termId: 'response' },
    { pattern: /\breverse(d|s)?\b/gi, termId: 'reverse' },
    { pattern: /\brevokes?\b/gi, termId: 'revoke' },
    { pattern: /\bruff(s|ing|ed)?\b/gi, termId: 'ruff' },
    { pattern: /\bsacrifices?\b/gi, termId: 'sacrifice' },
    { pattern: /\bsequences?\b/gi, termId: 'sequence' },
    { pattern: /\bsignals?\b/gi, termId: 'signal' },
    { pattern: /\bsingletons?\b/gi, termId: 'singleton' },
    { pattern: /\bslams?\b/gi, termId: 'slam' },
    { pattern: /\bsluffs?\b/gi, termId: 'sluff' },
    { pattern: /\bsplinters?\b/gi, termId: 'splinter' },
    { pattern: /\bsqueezes?\b/gi, termId: 'squeeze' },
    { pattern: /\bstoppers?\b/gi, termId: 'stopper' },
    { pattern: /\bsupport(s|ing|ed)?\b/gi, termId: 'support' },
    { pattern: /\btenaces?\b/gi, termId: 'tenace' },
    { pattern: /\bthrow[- ]?ins?\b/gi, termId: 'throw_in' },
    { pattern: /\btricks?\b/gi, termId: 'trick' },
    { pattern: /\btrumps?\b/gi, termId: 'trump' },
    { pattern: /\bunbalanced\b/gi, termId: 'unbalanced' },
    { pattern: /\bunblocks?\b/gi, termId: 'unblock' },
    { pattern: /\bundertricks?\b/gi, termId: 'undertrick' },
    { pattern: /\bvoids?\b/gi, termId: 'void' },
    { pattern: /\bvulnerable\b/gi, termId: 'vulnerable' },
    { pattern: /\bwinners?\b/gi, termId: 'winner' },
  ];

  // Split text and identify terms
  let segments = [{ type: 'text', content: text }];

  detectableTerms.forEach(({ pattern, termId }) => {
    const newSegments = [];

    segments.forEach((segment) => {
      if (segment.type === 'term') {
        newSegments.push(segment);
        return;
      }

      const parts = segment.content.split(pattern);
      const matches = segment.content.match(pattern) || [];

      parts.forEach((part, index) => {
        if (part) {
          newSegments.push({ type: 'text', content: part });
        }
        if (matches[index]) {
          newSegments.push({
            type: 'term',
            content: matches[index],
            termId,
          });
        }
      });
    });

    segments = newSegments;
  });

  return (
    <span className="term-highlight-text">
      {segments.map((segment, index) =>
        segment.type === 'term' ? (
          <TermTooltip
            key={index}
            term={segment.termId}
            onOpenGlossary={onOpenGlossary}
            seniorMode={seniorMode}
          >
            {segment.content}
          </TermTooltip>
        ) : (
          <span key={index}>{segment.content}</span>
        )
      )}
    </span>
  );
};

export default TermTooltip;
