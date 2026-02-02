import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../ui/collapsible";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { cn } from "../../lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";

/**
 * ScoreModal - Display final score after 13 tricks
 * Follows "Rule of Three" and senior-friendly UX principles
 * Designed as SECONDARY visual hierarchy (celebratory but not overwhelming)
 * Enhanced with session scoring context
 */
export function ScoreModal({ isOpen, onClose, scoreData, onDealNewHand, sessionData, onShowLearningDashboard, onPlayAnotherHand, onReplayHand, onReviewHand }) {
  // State for collapsible breakdown (must be before any early returns)
  const [isBreakdownOpen, setIsBreakdownOpen] = React.useState(false);

  if (!scoreData) return null;

  const { contract, tricks_taken, tricks_needed, result, score, made, breakdown, overtricks, undertricks } = scoreData;
  const doubledText = contract.doubled === 2 ? 'XX' : contract.doubled === 1 ? 'X' : '';

  // CRITICAL SCORING PERSPECTIVE LOGIC (MUST match ContractHeader.jsx):
  // - Backend returns scores from DECLARER's perspective (positive = made, negative = went down)
  // - User always plays South (NS team)
  // - MUST convert to user's NS perspective for display:
  //   * If NS declares and makes: show positive (correct)
  //   * If NS declares and goes down: show negative (correct)
  //   * If EW declares and makes: show NEGATIVE (we lost, so flip sign)
  //   * If EW declares and goes down: show POSITIVE (we set them, so flip sign)
  const declarerIsNS = contract.declarer === 'N' || contract.declarer === 'S';
  const userScore = declarerIsNS ? score : -score;

  // Update breakdown to reflect user's perspective
  const userBreakdown = declarerIsNS ? breakdown : {
    ...breakdown,
    // Note: breakdown is from declarer's perspective, so no change needed
    // The display will show "EW made their contract" with negative score for NS
  };

  // Session context
  const hasSession = sessionData && sessionData.active;
  const session = sessionData?.session;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-full max-w-[360px] sm:max-w-[440px] p-4 sm:p-6 overflow-visible">
        <DialogHeader>
          <DialogTitle className="text-2xl text-center">
            Hand Complete!
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4 overflow-hidden">
          {/* Contract row */}
          <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-md bg-gray-50 overflow-hidden">
            <span className="text-sm font-medium text-gray-700 shrink-0">Contract:</span>
            <span className="text-base font-bold text-gray-900 text-right truncate min-w-0">
              {contract?.level || '?'}{contract?.strain || '?'}
              {doubledText}
              {contract?.declarer ? ` by ${contract.declarer}` : ''}
            </span>
          </div>

          {/* Tricks taken row */}
          <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-md bg-gray-50 overflow-hidden">
            <span className="text-sm font-medium text-gray-700 shrink-0">Tricks Taken:</span>
            <span className="text-base font-bold text-gray-900 text-right truncate min-w-0">{tricks_taken ?? '?'} of {tricks_needed ?? '?'}</span>
          </div>

          {/* Result row */}
          <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-md bg-gray-50 overflow-hidden">
            <span className="text-sm font-medium text-gray-700 shrink-0">Result:</span>
            <span className={cn(
              "text-base font-bold text-right truncate min-w-0",
              made ? "text-green-600" : "text-red-600"
            )}>
              {result || (made ? 'Made' : 'Down')}
            </span>
          </div>

          {/* Score row (larger, highlighted) - Shows score from user's (NS) perspective */}
          <div className={cn(
            "flex items-center justify-between gap-2 px-3 py-3 rounded-lg border-2 overflow-hidden",
            userScore >= 0 ? "bg-green-50 border-green-500" : "bg-red-50 border-red-500"
          )}>
            <span className="text-base font-bold text-gray-900 shrink-0">Your Score:</span>
            <span className={cn(
              "text-xl font-bold text-right truncate min-w-0",
              userScore >= 0 ? "text-green-600" : "text-red-600"
            )}>
              {userScore >= 0 ? '+' : ''}{userScore}
            </span>
          </div>

          {/* Expandable Score Breakdown */}
          {breakdown && (
            <Collapsible
              open={isBreakdownOpen}
              onOpenChange={setIsBreakdownOpen}
              className="w-full"
            >
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full flex items-center justify-center gap-2 text-base font-medium text-blue-700 hover:text-blue-900 hover:bg-blue-50"
                >
                  📊 How was this calculated?
                  {isBreakdownOpen ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-3">
                <ScoreBreakdown
                  breakdown={userBreakdown}
                  contract={contract}
                  made={made}
                  overtricks={overtricks || 0}
                  undertricks={undertricks || 0}
                  tricksNeeded={tricks_needed}
                  userPerspective={!declarerIsNS}
                />
              </CollapsibleContent>
            </Collapsible>
          )}

          {/* Session Summary (if in session) */}
          {hasSession && (
            <div className="mt-2 p-3 rounded-lg bg-blue-50 border border-blue-200">
              <div className="text-center mb-2">
                <h3 className="text-sm font-bold text-blue-900">Session Standings</h3>
                <p className="text-xs text-blue-700">
                  Hand {session.hands_completed} of {session.max_hands} complete
                </p>
              </div>

              <div className="flex justify-center items-center gap-4">
                <div className="text-center">
                  <div className="text-xs font-medium text-gray-600">N-S</div>
                  <div className={cn(
                    "text-lg font-bold",
                    session.ns_score > session.ew_score ? "text-green-600" : "text-gray-900"
                  )}>
                    {session.ns_score}
                  </div>
                </div>

                <div className="text-gray-400 font-bold text-sm">vs</div>

                <div className="text-center">
                  <div className="text-xs font-medium text-gray-600">E-W</div>
                  <div className={cn(
                    "text-lg font-bold",
                    session.ew_score > session.ns_score ? "text-green-600" : "text-gray-900"
                  )}>
                    {session.ew_score}
                  </div>
                </div>
              </div>

              {session.is_complete && (
                <div className="mt-2 text-center p-2 bg-yellow-100 rounded-md">
                  <p className="text-sm font-bold text-yellow-900">🎉 Session Complete!</p>
                  <p className="text-xs text-yellow-800">
                    Winner: {session.winner === 'Tied' ? 'Tied' : session.winner}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="flex flex-col gap-2 pt-2">
          {/* Primary action: Play Another Hand */}
          {onPlayAnotherHand && (
            <Button
              onClick={() => {
                onPlayAnotherHand();
                onClose();
              }}
              className="w-full h-9 text-sm"
              variant="default"
            >
              Play Another Hand
            </Button>
          )}

          {/* Secondary actions row */}
          <div className="flex flex-wrap gap-2 w-full">
            {onReviewHand && (
              <Button
                onClick={() => {
                  onReviewHand();
                  onClose();
                }}
                className="flex-1 h-8 text-xs min-w-[80px]"
                variant="outline"
              >
                Review Hand
              </Button>
            )}
            {onShowLearningDashboard && (
              <Button
                onClick={() => {
                  onShowLearningDashboard();
                  onClose();
                }}
                className="flex-1 h-8 text-xs min-w-[80px]"
                variant="outline"
              >
                📊 My Progress
              </Button>
            )}
          </div>

          {/* Tertiary actions row */}
          <div className="flex flex-wrap gap-2 w-full">
            {onReplayHand && (
              <Button
                onClick={() => {
                  onReplayHand();
                  onClose();
                }}
                className="flex-1 h-8 text-xs min-w-[80px]"
                variant="outline"
              >
                Replay Hand
              </Button>
            )}
            <Button
              onClick={() => {
                onDealNewHand();
                onClose();
              }}
              className="flex-1 h-8 text-xs min-w-[80px]"
              variant="outline"
            >
              Bid New Hand
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
