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
 */
export function ScoreModal({ isOpen, onClose, scoreData }) {
  if (!scoreData) return null;

  const { contract, tricks_taken, result, score, made } = scoreData;
  const doubledText = contract.doubled === 2 ? 'XX' : contract.doubled === 1 ? 'X' : '';

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
        </div>

        <DialogFooter>
          <Button onClick={onClose} className="w-full" size="lg">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
