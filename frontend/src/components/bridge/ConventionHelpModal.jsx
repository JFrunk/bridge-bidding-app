import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { TermHighlight } from "../glossary";

/**
 * ConventionHelpModal Component
 *
 * Modal displaying convention information (Stayman, Jacoby Transfers, etc.)
 * Designed to be SECONDARY - provides help without blocking the main UI.
 * Uses minimal styling to avoid distraction from card play.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Controls modal visibility
 * @param {function} props.onClose - Callback to close modal
 * @param {Object} props.conventionInfo - Convention data with sections
 */
export function ConventionHelpModal({ isOpen, onClose, conventionInfo }) {
  if (!conventionInfo) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl text-gray-900">
            {conventionInfo.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 my-4">
          {/* Background */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-base font-semibold text-gray-900 mb-2 border-b border-gray-300 pb-2">
              Background
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed">
              <TermHighlight text={conventionInfo.background || ''} />
            </p>
          </div>

          {/* When to Use */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-base font-semibold text-gray-900 mb-2 border-b border-gray-300 pb-2">
              When to Use
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed">
              <TermHighlight text={conventionInfo.when_used || ''} />
            </p>
          </div>

          {/* How It Works */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-base font-semibold text-gray-900 mb-2 border-b border-gray-300 pb-2">
              How It Works
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              <TermHighlight text={conventionInfo.how_it_works || ''} />
            </p>
          </div>

          {/* As Responder */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-base font-semibold text-gray-900 mb-2 border-b border-gray-300 pb-2">
              As Responder
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              <TermHighlight text={conventionInfo.responder_actions || ''} />
            </p>
          </div>

          {/* As Opener */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-base font-semibold text-gray-900 mb-2 border-b border-gray-300 pb-2">
              As Opener
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              <TermHighlight text={conventionInfo.opener_actions || ''} />
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button onClick={onClose} variant="outline" className="w-full sm:w-auto">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

ConventionHelpModal.displayName = "ConventionHelpModal";
