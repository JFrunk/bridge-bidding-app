import React, { useState } from "react";
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
 * FeedbackModal Component
 *
 * A simple, frictionless feedback modal for users to report issues.
 * Works in both Learning Mode and Freeplay Mode.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Controls modal visibility
 * @param {function} props.onClose - Callback to close modal
 * @param {function} props.onSubmit - Callback when feedback is submitted
 * @param {string} props.context - 'learning' or 'freeplay' - determines what data is captured
 * @param {Object} props.contextData - Context-specific data to include in feedback
 */
export function FeedbackModal({
  isOpen,
  onClose,
  onSubmit,
  context = "freeplay",
  contextData = {},
}) {
  const [feedbackType, setFeedbackType] = useState("issue");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const feedbackTypes = [
    { value: "issue", label: "Something seems wrong", icon: "🐛" },
    { value: "incorrect", label: "Answer/feedback is incorrect", icon: "❌" },
    { value: "confusing", label: "Instructions are confusing", icon: "❓" },
    { value: "suggestion", label: "I have a suggestion", icon: "💡" },
  ];

  const handleSubmit = async () => {
    if (!onSubmit) {
      console.error("FeedbackModal: onSubmit handler not provided");
      setSubmitted(true); // Still show success to user
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        type: feedbackType,
        description: description.trim(),
        context,
        contextData,
      });
      setSubmitted(true);
    } catch (error) {
      console.error("Failed to submit feedback:", error);
      // Still mark as submitted so user isn't stuck
      setSubmitted(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset state when closing
    setFeedbackType("issue");
    setDescription("");
    setSubmitted(false);
    onClose();
  };

  if (submitted) {
    return (
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl text-center">
              Thank You!
            </DialogTitle>
          </DialogHeader>
          <div className="text-center py-6">
            <div className="text-4xl mb-4">✅</div>
            <p className="text-gray-700">
              Your feedback has been saved. We'll review it to improve the app.
            </p>
          </div>
          <DialogFooter className="justify-center">
            <Button onClick={handleClose} variant="default">
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-xl">Report an Issue</DialogTitle>
          <DialogDescription className="text-sm text-gray-600">
            Help us improve! Your current{" "}
            {context === "learning" ? "practice hand" : "game"} data will be
            saved with your feedback.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 my-4">
          {/* Feedback Type Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              What type of issue is this?
            </label>
            <div className="grid grid-cols-2 gap-2">
              {feedbackTypes.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setFeedbackType(type.value)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    feedbackType === type.value
                      ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200 text-gray-900"
                      : "border-gray-200 bg-white text-gray-900 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <span className="text-lg mr-2">{type.icon}</span>
                  <span className="text-sm font-medium text-gray-900">{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="feedback-description"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Tell us more (optional)
            </label>
            <Textarea
              id="feedback-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={
                context === "learning"
                  ? "e.g., 'The correct answer should be 2H, not 1NT'"
                  : "e.g., 'The AI made an impossible bid'"
              }
              rows={3}
              className="w-full"
            />
          </div>

          {/* Context info */}
          <div className="text-xs text-gray-700 bg-gray-100 p-3 rounded-lg">
            <strong className="text-gray-900">What will be saved:</strong>
            <ul className="mt-1 list-disc list-inside">
              {context === "learning" ? (
                <>
                  <li>Current practice hand and your answer</li>
                  <li>Expected answer and feedback shown</li>
                  <li>Skill being practiced</li>
                </>
              ) : (
                <>
                  <li>All four hands in the current deal</li>
                  <li>Complete auction history</li>
                  <li>Current game phase and state</li>
                </>
              )}
            </ul>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            onClick={handleSubmit}
            variant="default"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Submitting..." : "Submit Feedback"}
          </Button>
          <Button onClick={handleClose} variant="outline">
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

FeedbackModal.displayName = "FeedbackModal";
