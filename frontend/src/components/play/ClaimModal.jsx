import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

/**
 * ClaimModal - Dialog for claiming remaining tricks
 * Follows app styling standards (shadcn Dialog, dark theme compatible)
 */
export function ClaimModal({
  isOpen,
  onClose,
  tricksRemaining,
  tricksWonNS,
  tricksWonEW,
  tricksNeeded,
  onSubmitClaim,
  isValidating = false,
  validationResult = null,
}) {
  const [claimedTricks, setClaimedTricks] = React.useState(tricksRemaining);
  const [error, setError] = React.useState(null);

  // Reset state when modal opens
  React.useEffect(() => {
    if (isOpen) {
      setClaimedTricks(tricksRemaining);
      setError(null);
    }
  }, [isOpen, tricksRemaining]);

  const handleIncrement = () => {
    if (claimedTricks < tricksRemaining) {
      setClaimedTricks(claimedTricks + 1);
      setError(null);
    }
  };

  const handleDecrement = () => {
    if (claimedTricks > 0) {
      setClaimedTricks(claimedTricks - 1);
      setError(null);
    }
  };

  const handleSubmit = () => {
    if (claimedTricks < 0 || claimedTricks > tricksRemaining) {
      setError(`Please select a number between 0 and ${tricksRemaining}`);
      return;
    }
    onSubmitClaim(claimedTricks);
  };

  // Calculate what the final trick count would be
  const projectedTotalNS = tricksWonNS + claimedTricks;
  const projectedTotalEW = tricksWonEW + (tricksRemaining - claimedTricks);

  // Show result view if we have a validation result
  if (validationResult) {
    const isAccepted = validationResult.valid;

    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="w-full max-w-[400px] sm:max-w-[450px] p-4 sm:p-6">
          <DialogHeader>
            <DialogTitle className={cn(
              "text-2xl text-center",
              isAccepted ? "text-green-600" : "text-red-600"
            )}>
              {isAccepted ? "Claim Accepted!" : "Claim Rejected"}
            </DialogTitle>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            {/* Result message */}
            <div className={cn(
              "px-4 py-3 rounded-lg text-center",
              isAccepted ? "bg-green-50 text-green-800 border border-green-200" : "bg-red-50 text-red-800 border border-red-200"
            )}>
              <p className="text-sm font-medium">{validationResult.message}</p>
            </div>

            {/* Details */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between px-3 py-2 bg-gray-50 rounded">
                <span className="text-gray-600">Tricks Claimed:</span>
                <span className="font-semibold">{validationResult.claimed}</span>
              </div>
              {validationResult.max_possible !== null && (
                <div className="flex justify-between px-3 py-2 bg-gray-50 rounded">
                  <span className="text-gray-600">Max Possible (DDS):</span>
                  <span className="font-semibold">{validationResult.max_possible}</span>
                </div>
              )}
              {!validationResult.dds_available && (
                <p className="text-xs text-gray-500 text-center italic">
                  DDS validation unavailable - claim accepted on good faith
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              onClick={onClose}
              className="w-full"
              variant={isAccepted ? "default" : "outline"}
            >
              {isAccepted ? "Continue" : "Try Again"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-full max-w-[400px] sm:max-w-[450px] p-4 sm:p-6">
        <DialogHeader>
          <DialogTitle className="text-2xl text-center">
            Claim Tricks
          </DialogTitle>
          <DialogDescription className="text-center text-gray-500">
            How many of the remaining {tricksRemaining} tricks do you claim?
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4">
          {/* Current score summary */}
          <div className="flex items-center justify-between px-3 py-2 rounded-md bg-gray-50">
            <span className="text-sm text-gray-600">Current Score:</span>
            <span className="text-sm font-medium">
              <span className="text-green-600">NS: {tricksWonNS}</span>
              {" / "}
              <span className="text-red-600">EW: {tricksWonEW}</span>
            </span>
          </div>

          {/* Contract target */}
          <div className="flex items-center justify-between px-3 py-2 rounded-md bg-gray-50">
            <span className="text-sm text-gray-600">Need to Make:</span>
            <span className="text-sm font-bold">{tricksNeeded} tricks</span>
          </div>

          {/* Claim selector */}
          <div className="flex flex-col items-center gap-3 py-4">
            <span className="text-sm text-gray-600">Claiming:</span>
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={handleDecrement}
                disabled={claimedTricks <= 0 || isValidating}
                className="h-12 w-12 text-xl"
              >
                -
              </Button>
              <div className="flex flex-col items-center min-w-[80px]">
                <span className="text-4xl font-bold text-gray-900">{claimedTricks}</span>
                <span className="text-xs text-gray-500">of {tricksRemaining}</span>
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={handleIncrement}
                disabled={claimedTricks >= tricksRemaining || isValidating}
                className="h-12 w-12 text-xl"
              >
                +
              </Button>
            </div>
          </div>

          {/* Projected outcome */}
          <div className={cn(
            "flex items-center justify-between px-3 py-3 rounded-lg border-2",
            projectedTotalNS >= tricksNeeded
              ? "bg-green-50 border-green-300"
              : "bg-red-50 border-red-300"
          )}>
            <span className="text-sm font-medium text-gray-700">If Accepted:</span>
            <span className={cn(
              "text-sm font-bold",
              projectedTotalNS >= tricksNeeded ? "text-green-700" : "text-red-700"
            )}>
              NS: {projectedTotalNS} / EW: {projectedTotalEW}
              {projectedTotalNS >= tricksNeeded
                ? ` (Made +${projectedTotalNS - tricksNeeded})`
                : ` (Down ${tricksNeeded - projectedTotalNS})`
              }
            </span>
          </div>

          {/* Error message */}
          {error && (
            <p className="text-sm text-red-600 text-center">{error}</p>
          )}
        </div>

        <DialogFooter className="flex flex-col gap-2 sm:flex-row">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isValidating}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isValidating}
            className="w-full sm:w-auto"
          >
            {isValidating ? "Validating..." : "Submit Claim"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
