/**
 * Console Capture Utility
 *
 * Intercepts console.log, console.error, console.warn, and console.info
 * to maintain a circular buffer of recent log entries for debugging.
 *
 * Used by the feedback system to capture context when users report issues.
 */

const LOG_BUFFER_SIZE = 50;
const logBuffer = [];

// Store original console methods
const originalConsole = {
  log: console.log.bind(console),
  error: console.error.bind(console),
  warn: console.warn.bind(console),
  info: console.info.bind(console),
  debug: console.debug.bind(console),
};

/**
 * Safely stringify a value for logging
 */
function safeStringify(arg) {
  if (arg === null) return 'null';
  if (arg === undefined) return 'undefined';

  if (arg instanceof Error) {
    return `${arg.name}: ${arg.message}${arg.stack ? '\n' + arg.stack : ''}`;
  }

  if (typeof arg === 'object') {
    try {
      // Limit depth and handle circular references
      return JSON.stringify(arg, (key, value) => {
        if (typeof value === 'object' && value !== null) {
          // Avoid circular references and DOM nodes
          if (value instanceof HTMLElement) {
            return `[HTMLElement: ${value.tagName}]`;
          }
          if (value instanceof Event) {
            return `[Event: ${value.type}]`;
          }
        }
        return value;
      }, 2).slice(0, 1000); // Limit length
    } catch (e) {
      return '[Object - unable to stringify]';
    }
  }

  return String(arg).slice(0, 500); // Limit string length
}

/**
 * Capture a log entry into the buffer
 */
function captureLog(level, ...args) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message: args.map(safeStringify).join(' '),
  };

  logBuffer.push(entry);

  // Maintain circular buffer
  if (logBuffer.length > LOG_BUFFER_SIZE) {
    logBuffer.shift();
  }

  // Call original console method
  originalConsole[level](...args);
}

/**
 * Initialize console capture by overriding console methods
 * Call this once at app startup
 */
export function initConsoleCapture() {
  console.log = (...args) => captureLog('log', ...args);
  console.error = (...args) => captureLog('error', ...args);
  console.warn = (...args) => captureLog('warn', ...args);
  console.info = (...args) => captureLog('info', ...args);
  console.debug = (...args) => captureLog('debug', ...args);

  // Log that capture is initialized (using original to avoid recursion issues)
  originalConsole.info('[ConsoleCapture] Initialized - capturing last', LOG_BUFFER_SIZE, 'log entries');
}

/**
 * Get recent log entries
 * @param {number} count - Number of entries to retrieve (default: 30)
 * @returns {Array} Array of log entries with timestamp, level, and message
 */
export function getRecentLogs(count = 30) {
  return logBuffer.slice(-count);
}

/**
 * Get recent logs formatted as a string for display
 * @param {number} count - Number of entries to retrieve
 * @returns {string} Formatted log string
 */
export function getRecentLogsFormatted(count = 30) {
  return getRecentLogs(count)
    .map(entry => `[${entry.timestamp}] ${entry.level.toUpperCase()}: ${entry.message}`)
    .join('\n');
}

/**
 * Clear the log buffer (useful for testing)
 */
export function clearLogBuffer() {
  logBuffer.length = 0;
}

/**
 * Get the current buffer size
 */
export function getLogBufferSize() {
  return logBuffer.length;
}

/**
 * Restore original console methods (useful for testing/cleanup)
 */
export function restoreConsole() {
  console.log = originalConsole.log;
  console.error = originalConsole.error;
  console.warn = originalConsole.warn;
  console.info = originalConsole.info;
  console.debug = originalConsole.debug;
}
