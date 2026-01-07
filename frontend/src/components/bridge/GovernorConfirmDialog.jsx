import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";

/**
 * GovernorConfirmDialog Component
 *
 * A confirmation dialog shown when the Governor system detects a potentially
 * dangerous bid (critical or significant impact). Gives the user the option
 * to proceed anyway or choose a different bid.
 *
 * This is part of the "Safety Guard" feature that helps users avoid
 * physics-violating or severely suboptimal bids.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Controls dialog visibility
 * @param {function} props.onClose - Callback when user chooses "Choose Different Bid"
 * @param {function} props.onProceed - Callback when user chooses "Proceed Anyway"
 * @param {string} props.bid - The bid being attempted
 * @param {string} props.impact - 'critical' or 'significant'
 * @param {string} props.reasoning - The Governor warning explanation
 * @param {string} props.optimalBid - The recommended optimal bid (if available)
 */
export function GovernorConfirmDialog({
  isOpen,
  onClose,
  onProceed,
  bid,
  impact,
  reasoning,
  optimalBid,
}) {
  const isCritical = impact === "critical";

  // Determine header based on severity
  const headerText = isCritical
    ? "Critical Warning"
    : "Significant Warning";

  const headerIcon = isCritical ? "🚨" : "⚠️";

  const borderColor = isCritical
    ? "border-red-500"
    : "border-amber-500";

  const headerBgColor = isCritical
    ? "bg-red-50"
    : "bg-amber-50";

  const headerTextColor = isCritical
    ? "text-red-800"
    : "text-amber-800";

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className={`sm:max-w-md border-2 ${borderColor}`}
        data-testid="governor-confirm-dialog"
      >
        <DialogHeader className={`${headerBgColor} -m-6 mb-4 p-4 rounded-t-lg`}>
          <DialogTitle className={`text-xl ${headerTextColor} flex items-center gap-2`}>
            <span>{headerIcon}</span>
            <span>{headerText}</span>
          </DialogTitle>
          <DialogDescription className={`text-sm ${headerTextColor}`}>
            The Governor has flagged this bid as potentially problematic.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 my-2">
          {/* The bid being attempted */}
          <div className="text-center">
            <span className="text-sm text-gray-600">You selected:</span>
            <div className="text-3xl font-bold text-gray-900 mt-1" data-testid="governor-selected-bid">
              {bid}
            </div>
          </div>

          {/* Warning explanation */}
          <div
            className={`p-4 rounded-lg ${isCritical ? "bg-red-50 border border-red-200" : "bg-amber-50 border border-amber-200"}`}
            data-testid="governor-reasoning"
          >
            <p className={`text-sm ${isCritical ? "text-red-800" : "text-amber-800"}`}>
              {reasoning || "This bid may violate bridge physics or lead to poor results."}
            </p>
          </div>

          {/* Optimal bid suggestion */}
          {optimalBid && optimalBid !== bid && (
            <div className="text-center p-3 bg-green-50 border border-green-200 rounded-lg">
              <span className="text-sm text-green-700">Recommended bid:</span>
              <div className="text-2xl font-bold text-green-800 mt-1">
                {optimalBid}
              </div>
            </div>
          )}

          {/* Explanation of consequences */}
          <div className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg">
            <strong className="text-gray-700">What this means:</strong>
            <p className="mt-1">
              {isCritical
                ? "This bid is likely to result in a very poor contract that cannot be made. Consider choosing a different bid."
                : "This bid may not be optimal and could lead to a suboptimal contract. You might want to reconsider."}
            </p>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0 flex-col sm:flex-row">
          <Button
            onClick={onClose}
            variant="default"
            className="w-full sm:w-auto"
            data-testid="governor-choose-different"
          >
            Choose Different Bid
          </Button>
          <Button
            onClick={onProceed}
            variant={isCritical ? "destructive" : "outline"}
            className="w-full sm:w-auto"
            data-testid="governor-proceed-anyway"
          >
            Proceed Anyway
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

GovernorConfirmDialog.displayName = "GovernorConfirmDialog";
