/**
 * Screenshot Capture Utility
 *
 * Captures a screenshot of the current viewport using html2canvas.
 * Used by the feedback system to capture visual context when users report issues.
 */

import html2canvas from 'html2canvas';

/**
 * Capture a screenshot of the current viewport
 * @param {Object} options - Capture options
 * @param {number} options.quality - JPEG quality (0-1), default 0.7
 * @param {number} options.maxWidth - Max width to scale down to, default 1200
 * @param {boolean} options.ignoreModals - Whether to hide modals before capture, default true
 * @returns {Promise<string|null>} Base64 encoded JPEG image or null if capture fails
 */
export async function captureScreenshot(options = {}) {
  const {
    quality = 0.7,
    maxWidth = 1200,
    ignoreModals = true,
  } = options;

  try {
    // Optionally hide modal overlays during capture to show underlying UI
    const modalElements = ignoreModals
      ? document.querySelectorAll('[role="dialog"], .modal-overlay, [data-radix-portal]')
      : [];

    const originalVisibility = [];
    modalElements.forEach((el, i) => {
      originalVisibility[i] = el.style.visibility;
      el.style.visibility = 'hidden';
    });

    const canvas = await html2canvas(document.body, {
      logging: false,
      useCORS: true,
      allowTaint: true,
      scale: window.devicePixelRatio > 1 ? 1 : window.devicePixelRatio, // Limit scale for performance
      windowWidth: document.documentElement.scrollWidth,
      windowHeight: document.documentElement.scrollHeight,
    });

    // Restore modal visibility
    modalElements.forEach((el, i) => {
      el.style.visibility = originalVisibility[i];
    });

    // Scale down if too large
    let finalCanvas = canvas;
    if (canvas.width > maxWidth) {
      const scaleFactor = maxWidth / canvas.width;
      const scaledCanvas = document.createElement('canvas');
      scaledCanvas.width = maxWidth;
      scaledCanvas.height = canvas.height * scaleFactor;

      const ctx = scaledCanvas.getContext('2d');
      ctx.drawImage(canvas, 0, 0, scaledCanvas.width, scaledCanvas.height);
      finalCanvas = scaledCanvas;
    }

    // Convert to compressed JPEG
    const dataUrl = finalCanvas.toDataURL('image/jpeg', quality);

    // Return just the base64 data (without the data:image/jpeg;base64, prefix)
    // to save space, or return full dataUrl if you need it displayable
    return dataUrl;
  } catch (error) {
    console.error('[ScreenshotCapture] Failed to capture screenshot:', error);
    return null;
  }
}

/**
 * Get approximate size of base64 image in KB
 * @param {string} base64String - Base64 encoded image
 * @returns {number} Approximate size in KB
 */
export function getBase64SizeKB(base64String) {
  if (!base64String) return 0;
  // Remove data URL prefix if present
  const base64 = base64String.replace(/^data:image\/\w+;base64,/, '');
  // Base64 encodes 3 bytes as 4 characters
  const bytes = (base64.length * 3) / 4;
  return Math.round(bytes / 1024);
}
