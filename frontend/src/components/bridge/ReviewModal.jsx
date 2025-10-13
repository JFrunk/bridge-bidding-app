import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";

/**
 * ReviewModal Component
 *
 * Modal for requesting AI review of bidding/play.
 * Designed to be SECONDARY to main UI - only shows when explicitly requested.
 * Uses minimal, non-distracting design.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Controls modal visibility
 * @param {function} props.onClose - Callback to close modal
 * @param {function} props.onSubmit - Callback when "Save & Generate Prompt" clicked
 * @param {string} props.userConcern - User's concern text
 * @param {function} props.setUserConcern - Update user concern
 * @param {string} props.reviewPrompt - Generated prompt (if available)
 * @param {string} props.reviewFilename - Generated filename
 * @param {string} props.gamePhase - 'bidding' or 'playing'
 * @param {function} props.onCopyPrompt - Callback to copy prompt to clipboard
 */
export function ReviewModal({
  isOpen,
  onClose,
  onSubmit,
  userConcern,
  setUserConcern,
  reviewPrompt,
  reviewFilename,
  gamePhase,
  onCopyPrompt
}) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl">Request AI Review</DialogTitle>
          <DialogDescription className="text-sm text-gray-600">
            {gamePhase === 'playing'
              ? 'Hand data including auction and card play will be saved to: '
              : 'Hand data will be saved to: '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-info text-xs">
              backend/review_requests/{reviewFilename || 'hand_[timestamp].json'}
            </code>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 my-4">
          <div>
            <label
              htmlFor="user-concern"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              What concerns you about this hand? (Optional)
            </label>
            <Textarea
              id="user-concern"
              value={userConcern}
              onChange={(e) => setUserConcern(e.target.value)}
              placeholder={
                gamePhase === 'playing'
                  ? "e.g., 'Should declarer have led a different suit?'"
                  : "e.g., 'Why did North bid 3NT here?'"
              }
              rows={3}
              className="w-full"
            />
          </div>

          {reviewPrompt && (
            <div className="border-t pt-4">
              <h3 className="text-base font-semibold text-gray-900 mb-2">
                Copy this prompt to Claude Code:
              </h3>
              <div className="bg-gray-50 border border-gray-200 rounded p-4 max-h-48 overflow-y-auto mb-4">
                <pre className="text-xs text-gray-800 whitespace-pre-wrap font-mono">
                  {reviewPrompt}
                </pre>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          {!reviewPrompt ? (
            <>
              <Button onClick={onSubmit} variant="default">
                Save & Generate Prompt
              </Button>
              <Button onClick={onClose} variant="outline">
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button onClick={onCopyPrompt} variant="default">
                📋 Copy to Clipboard
              </Button>
              <Button onClick={onClose} variant="outline">
                Close
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

ReviewModal.displayName = "ReviewModal";
