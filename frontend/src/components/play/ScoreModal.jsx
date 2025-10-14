import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

/**
 * ScoreModal - Display final score after 13 tricks
 * Follows "Rule of Three" and senior-friendly UX principles
 * Designed as SECONDARY visual hierarchy (celebratory but not overwhelming)
 * Enhanced with session scoring context
 */
export function ScoreModal({ isOpen, onClose, scoreData, onDealNewHand, sessionData, onShowLearningDashboard }) {
  if (!scoreData) return null;

  const { contract, tricks_taken, result, score, made } = scoreData;
  const doubledText = contract.doubled === 2 ? 'XX' : contract.doubled === 1 ? 'X' : '';

  // Session context
  const hasSession = sessionData && sessionData.active;
  const session = sessionData?.session;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-2xl text-center">
            Hand Complete!
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4">
          {/* Contract row */}
          <div className="flex items-center justify-between px-4 py-3 rounded-md bg-gray-50">
            <span className="text-base font-medium text-gray-700">Contract:</span>
            <span className="text-lg font-bold text-gray-900">
              {contract.level}{contract.strain}
              {doubledText}
              {' by '}{contract.declarer}
            </span>
          </div>

          {/* Tricks taken row */}
          <div className="flex items-center justify-between px-4 py-3 rounded-md bg-gray-50">
            <span className="text-base font-medium text-gray-700">Tricks Taken:</span>
            <span className="text-lg font-bold text-gray-900">{tricks_taken}</span>
          </div>

          {/* Result row */}
          <div className="flex items-center justify-between px-4 py-3 rounded-md bg-gray-50">
            <span className="text-base font-medium text-gray-700">Result:</span>
            <span className={cn(
              "text-lg font-bold",
              made ? "text-success" : "text-danger"
            )}>
              {result}
            </span>
          </div>

          {/* Score row (larger, highlighted) */}
          <div className={cn(
            "flex items-center justify-between px-6 py-4 rounded-lg border-2",
            score >= 0 ? "bg-green-50 border-success" : "bg-red-50 border-danger"
          )}>
            <span className="text-xl font-bold text-gray-900">Score:</span>
            <span className={cn(
              "text-3xl font-bold",
              score >= 0 ? "text-success" : "text-danger"
            )}>
              {score >= 0 ? '+' : ''}{score}
            </span>
          </div>

          {/* Session Summary (if in session) */}
          {hasSession && (
            <div className="mt-4 p-4 rounded-lg bg-blue-50 border-2 border-blue-200">
              <div className="text-center mb-3">
                <h3 className="text-lg font-bold text-blue-900">
                  Session Standings
                </h3>
                <p className="text-sm text-blue-700">
                  Hand {session.hands_completed} of {session.max_hands} complete
                </p>
              </div>

              <div className="flex justify-around items-center gap-4">
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-700">North-South</div>
                  <div className={cn(
                    "text-2xl font-bold",
                    session.ns_score > session.ew_score ? "text-success" : "text-gray-900"
                  )}>
                    {session.ns_score}
                  </div>
                </div>

                <div className="text-gray-400 font-bold text-xl">vs</div>

                <div className="text-center">
                  <div className="text-sm font-medium text-gray-700">East-West</div>
                  <div className={cn(
                    "text-2xl font-bold",
                    session.ew_score > session.ns_score ? "text-success" : "text-gray-900"
                  )}>
                    {session.ew_score}
                  </div>
                </div>
              </div>

              {session.is_complete && (
                <div className="mt-3 text-center p-3 bg-yellow-100 rounded-md">
                  <p className="text-lg font-bold text-yellow-900">
                    🎉 Session Complete!
                  </p>
                  <p className="text-base text-yellow-800">
                    Winner: {session.winner === 'Tied' ? 'Tied Game' : session.winner}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="flex flex-col gap-3 sm:flex-col">
          {/* Primary actions row */}
          <div className="flex gap-3 w-full">
            <Button
              onClick={() => {
                onDealNewHand();
                onClose();
              }}
              className="flex-1"
              size="lg"
              variant="default"
            >
              New Hand to Bid
            </Button>
            {onShowLearningDashboard && (
              <Button
                onClick={() => {
                  onShowLearningDashboard();
                  onClose();
                }}
                className="flex-1"
                size="lg"
                variant="default"
              >
                📊 My Progress
              </Button>
            )}
          </div>
          {/* Close button */}
          <Button
            onClick={onClose}
            className="w-full"
            size="lg"
            variant="outline"
          >
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
