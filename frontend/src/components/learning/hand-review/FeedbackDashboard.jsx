/**
 * FeedbackDashboard - Learning Coach Component
 *
 * Displays play quality feedback with visual hierarchy based on grade.
 * Replaces the simple text-based feedback with an educational coach interface.
 *
 * Grades:
 * - optimal: Perfect play (green)
 * - reasonable: Good enough (blue)
 * - questionable: Suboptimal choice (orange)
 * - blunder: Significant error (red)
 *
 * Features:
 * - Ghost card pattern: isVisible=false returns fixed-height invisible placeholder
 * - Comparison pattern: Shows played card vs suggested card with arrow
 */

import React from 'react';
import { Check, Info, AlertTriangle, XCircle, ArrowRight } from 'lucide-react';

const GRADE_CONFIG = {
  optimal: {
    label: 'Optimal',
    icon: Check,
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300',
    iconBg: 'bg-green-200',
  },
  reasonable: {
    label: 'Reasonable',
    icon: Info,
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-300',
    iconBg: 'bg-blue-200',
  },
  questionable: {
    label: 'Questionable',
    icon: AlertTriangle,
    bg: 'bg-orange-100',
    text: 'text-orange-800',
    border: 'border-orange-300',
    iconBg: 'bg-orange-200',
  },
  blunder: {
    label: 'Blunder',
    icon: XCircle,
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-300',
    iconBg: 'bg-red-200',
  },
  'no-data': {
    label: 'No Analysis',
    icon: Info,
    bg: 'bg-gray-50',
    text: 'text-gray-500',
    border: 'border-gray-200',
    iconBg: 'bg-gray-100',
  },
};

/**
 * CardChip - Styled card display for comparison view
 */
const CardChip = ({ card, variant = 'default' }) => {
  if (!card) return null;
  const rank = card.rank || card.r;
  const suit = card.suit || card.s;
  if (!rank || !suit) return null;

  const suitSymbols = { S: '♠', H: '♥', D: '♦', C: '♣' };
  const suitSymbol = suitSymbols[suit.toUpperCase()] || suit;
  const isRed = ['H', 'D', '♥', '♦'].includes(suit.toUpperCase());

  const baseClasses = 'inline-flex items-center px-2.5 py-1 rounded font-bold text-base';
  const variantClasses = variant === 'better'
    ? 'bg-green-50 border-2 border-green-400 shadow-sm'
    : 'bg-white border border-gray-300 shadow-sm';

  return (
    <span className={`${baseClasses} ${variantClasses}`}>
      <span className={isRed ? 'text-red-600' : 'text-gray-900'}>
        {rank}{suitSymbol}
      </span>
    </span>
  );
};

/**
 * Format a card for inline display (e.g., "A♠" or "10♥")
 */
const formatCard = (card) => {
  if (!card) return null;
  const rank = card.rank || card.r;
  const suit = card.suit || card.s;
  if (!rank || !suit) return null;

  const suitSymbols = { S: '♠', H: '♥', D: '♦', C: '♣' };
  const suitSymbol = suitSymbols[suit.toUpperCase()] || suit;
  const isRed = ['H', 'D', '♥', '♦'].includes(suit.toUpperCase());

  return (
    <span className={`font-bold ${isRed ? 'text-red-600' : 'text-gray-900'}`}>
      {rank}{suitSymbol}
    </span>
  );
};

/**
 * ComparisonView - Split view showing played card vs better card
 */
const ComparisonView = ({ playedCard, betterCard }) => {
  if (!playedCard || !betterCard) return null;

  return (
    <div className="flex items-center justify-center gap-3 py-2 px-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex flex-col items-center gap-1">
        <span className="text-xs text-gray-500 uppercase tracking-wider">You played</span>
        <CardChip card={playedCard} variant="default" />
      </div>
      <ArrowRight size={20} className="text-gray-400 flex-shrink-0" />
      <div className="flex flex-col items-center gap-1">
        <span className="text-xs text-green-600 uppercase tracking-wider font-medium">Better</span>
        <CardChip card={betterCard} variant="better" />
      </div>
    </div>
  );
};

const FeedbackDashboard = ({
  grade = 'no-data',
  analysisText,
  alternativePlay,
  playedCard,
  tricksCost,
  isStart = false,
  isAiPlay = false,
  aiPlayLabel = null,
  isVisible = true,
}) => {
  // Ghost card pattern - return invisible placeholder with fixed height
  // Uses CSS variable for consistent height with parent slot
  if (!isVisible) {
    return (
      <div className="feedback-dashboard ghost-placeholder" style={{ minHeight: 'var(--feedback-slot-height, 4.5em)', visibility: 'hidden' }}>
        {/* Invisible placeholder to prevent layout bounce */}
      </div>
    );
  }

  // Start state - show navigation hint
  if (isStart) {
    return (
      <div className="feedback-dashboard start-hint">
        <div className="flex items-center justify-center gap-3 py-2 h-full">
          <span className="text-gray-600 text-sm">
            Press <kbd className="px-2 py-0.5 bg-gray-200 rounded text-xs font-mono">→</kbd> or click <span className="font-semibold text-emerald-700">Next</span> to step through each play
          </span>
        </div>
      </div>
    );
  }

  // AI play/bid - minimal display
  if (isAiPlay) {
    return (
      <div className="feedback-dashboard ai-play">
        <div className="flex items-center justify-center gap-2 py-2 text-gray-500">
          <Info size={16} />
          <span className="text-sm">{aiPlayLabel || 'AI play — no analysis for this card'}</span>
        </div>
      </div>
    );
  }

  // No analysis available - show neutral state
  if (grade === 'no-data' || (!analysisText && !grade)) {
    return (
      <div className="feedback-dashboard no-data-state">
        <div className="flex flex-col items-center gap-2 p-4 text-center">
          <div className="p-2 rounded-full bg-gray-100">
            <Info size={20} className="text-gray-400" />
          </div>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-semibold bg-gray-100 text-gray-500">
              No Analysis
            </span>
            {playedCard && (
              <span className="text-sm text-gray-500">
                You played: {formatCard(playedCard)}
              </span>
            )}
          </div>
          <p className="text-gray-500 text-sm leading-relaxed">
            Play analysis was not recorded for this card.
          </p>
        </div>
      </div>
    );
  }

  const config = GRADE_CONFIG[grade] || GRADE_CONFIG['no-data'];
  const Icon = config.icon;
  const showComparison = (grade === 'questionable' || grade === 'blunder') && alternativePlay && playedCard;

  return (
    <div className={`feedback-dashboard ${config.bg} ${config.border} border-l-4 rounded-lg`}>
      <div className="flex flex-col items-center gap-2 p-4 text-center">
        {/* Icon */}
        <div className={`p-2 rounded-full ${config.iconBg}`}>
          <Icon size={20} className={config.text} />
        </div>

        {/* Grade Badge + Trick Cost */}
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-semibold ${config.bg} ${config.text}`}>
            {config.label}
          </span>
          {/* Only show played card inline for optimal/reasonable (no comparison needed) */}
          {playedCard && !showComparison && (
            <span className="text-sm text-gray-600">
              You played: {formatCard(playedCard)}
            </span>
          )}
          {tricksCost > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs font-semibold">
              -{tricksCost} trick{tricksCost > 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Comparison View - Split display for questionable/blunder */}
        {showComparison && (
          <ComparisonView playedCard={playedCard} betterCard={alternativePlay} />
        )}

        {/* Analysis Text */}
        {analysisText && (
          <p className="text-gray-800 text-base leading-relaxed">
            {analysisText}
          </p>
        )}
      </div>
    </div>
  );
};

export default FeedbackDashboard;
