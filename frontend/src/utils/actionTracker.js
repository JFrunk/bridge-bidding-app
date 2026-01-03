/**
 * User Action Trail Tracker
 *
 * Tracks user interactions (clicks, inputs, navigation) to provide
 * reproduction steps when users report issues.
 */

const ACTION_BUFFER_SIZE = 30;
const actionBuffer = [];

/**
 * Get a readable selector for an element
 */
function getElementSelector(element) {
  if (!element || !element.tagName) return 'unknown';

  const tag = element.tagName.toLowerCase();

  // Priority: data-testid > id > class + tag
  if (element.dataset?.testid) {
    return `[data-testid="${element.dataset.testid}"]`;
  }

  if (element.id) {
    return `#${element.id}`;
  }

  // Build a meaningful selector
  let selector = tag;

  // Add meaningful classes (skip utility classes)
  const meaningfulClasses = Array.from(element.classList || [])
    .filter(cls =>
      !cls.match(/^(w-|h-|p-|m-|flex|grid|text-|bg-|border-|rounded|hover:|focus:)/) &&
      cls.length < 30
    )
    .slice(0, 2);

  if (meaningfulClasses.length > 0) {
    selector += '.' + meaningfulClasses.join('.');
  }

  // Add type for inputs
  if (tag === 'input' && element.type) {
    selector += `[type="${element.type}"]`;
  }

  // Add name if present
  if (element.name) {
    selector += `[name="${element.name}"]`;
  }

  // Add button/link text for context
  if ((tag === 'button' || tag === 'a') && element.textContent) {
    const text = element.textContent.trim().slice(0, 20);
    if (text) {
      selector += ` "${text}"`;
    }
  }

  return selector;
}

/**
 * Record an action to the buffer
 */
function recordAction(action) {
  const entry = {
    ...action,
    timestamp: new Date().toISOString(),
    url: window.location.pathname,
  };

  actionBuffer.push(entry);

  if (actionBuffer.length > ACTION_BUFFER_SIZE) {
    actionBuffer.shift();
  }
}

/**
 * Click handler
 */
function handleClick(event) {
  const target = event.target.closest('button, a, [role="button"], input[type="submit"], [data-testid]') || event.target;

  recordAction({
    type: 'click',
    target: getElementSelector(target),
    text: target.textContent?.trim().slice(0, 30) || null,
  });
}

/**
 * Input change handler (debounced per element)
 */
const inputDebounceMap = new Map();

function handleInput(event) {
  const target = event.target;
  if (!target.tagName) return;

  const tag = target.tagName.toLowerCase();
  if (!['input', 'textarea', 'select'].includes(tag)) return;

  // Debounce per element to avoid flooding on typing
  const key = getElementSelector(target);
  if (inputDebounceMap.has(key)) {
    clearTimeout(inputDebounceMap.get(key));
  }

  inputDebounceMap.set(key, setTimeout(() => {
    // Don't log sensitive field values
    const isSensitive = target.type === 'password' ||
      target.name?.toLowerCase().includes('password') ||
      target.name?.toLowerCase().includes('token');

    recordAction({
      type: 'input',
      target: key,
      inputType: target.type || 'text',
      value: isSensitive ? '[redacted]' : (target.value?.slice(0, 50) || ''),
    });

    inputDebounceMap.delete(key);
  }, 500));
}

/**
 * Track navigation/route changes
 */
let lastPathname = window.location.pathname;

function checkNavigation() {
  if (window.location.pathname !== lastPathname) {
    recordAction({
      type: 'navigation',
      from: lastPathname,
      to: window.location.pathname,
    });
    lastPathname = window.location.pathname;
  }
}

/**
 * Track errors
 */
function handleError(event) {
  recordAction({
    type: 'error',
    message: event.message || 'Unknown error',
    filename: event.filename?.split('/').pop() || null,
    line: event.lineno || null,
  });
}

/**
 * Track unhandled promise rejections
 */
function handleUnhandledRejection(event) {
  recordAction({
    type: 'unhandled_rejection',
    reason: event.reason?.message || event.reason?.toString()?.slice(0, 100) || 'Unknown',
  });
}

/**
 * Initialize action tracking
 * Call this once at app startup
 */
export function initActionTracker() {
  // Click tracking
  document.addEventListener('click', handleClick, { capture: true, passive: true });

  // Input tracking
  document.addEventListener('input', handleInput, { capture: true, passive: true });
  document.addEventListener('change', handleInput, { capture: true, passive: true });

  // Navigation tracking (poll-based for SPA compatibility)
  setInterval(checkNavigation, 500);

  // Error tracking
  window.addEventListener('error', handleError);
  window.addEventListener('unhandledrejection', handleUnhandledRejection);

  // Record initial page load
  recordAction({
    type: 'page_load',
    to: window.location.pathname,
  });

  console.info('[ActionTracker] Initialized - tracking last', ACTION_BUFFER_SIZE, 'user actions');
}

/**
 * Get recent user actions
 * @param {number} count - Number of actions to retrieve (default: 20)
 * @returns {Array} Array of action entries
 */
export function getRecentActions(count = 20) {
  return actionBuffer.slice(-count);
}

/**
 * Get recent actions formatted as readable steps
 * @param {number} count - Number of actions to retrieve
 * @returns {string} Formatted action trail
 */
export function getRecentActionsFormatted(count = 20) {
  return getRecentActions(count)
    .map((action, i) => {
      const time = action.timestamp.split('T')[1].split('.')[0];
      switch (action.type) {
        case 'click':
          return `${i + 1}. [${time}] Clicked: ${action.target}${action.text ? ` ("${action.text}")` : ''}`;
        case 'input':
          return `${i + 1}. [${time}] Input: ${action.target} = "${action.value}"`;
        case 'navigation':
          return `${i + 1}. [${time}] Navigated: ${action.from} → ${action.to}`;
        case 'error':
          return `${i + 1}. [${time}] ERROR: ${action.message}`;
        case 'unhandled_rejection':
          return `${i + 1}. [${time}] Promise Rejected: ${action.reason}`;
        case 'page_load':
          return `${i + 1}. [${time}] Page loaded: ${action.to}`;
        default:
          return `${i + 1}. [${time}] ${action.type}`;
      }
    })
    .join('\n');
}

/**
 * Manually record a custom action (for components to call)
 * @param {string} type - Action type
 * @param {Object} data - Additional data
 */
export function trackAction(type, data = {}) {
  recordAction({ type, ...data });
}

/**
 * Clear the action buffer (useful for testing)
 */
export function clearActionBuffer() {
  actionBuffer.length = 0;
}
