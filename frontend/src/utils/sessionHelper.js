/**
 * Session Helper - Minimal integration for session management
 *
 * Use this if you want to add session support without refactoring all API calls.
 * Just import getSessionHeaders() and add to your existing fetch calls.
 *
 * Usage:
 *   import { getSessionHeaders } from './utils/sessionHelper';
 *
 *   fetch(`${API_URL}/api/deal-hands`, {
 *     headers: {
 *       'Content-Type': 'application/json',
 *       ...getSessionHeaders()  // Add this line
 *     }
 *   });
 */

/**
 * Get or create session ID
 * @returns {string} Unique session identifier
 */
export function getSessionId() {
  let sessionId = localStorage.getItem('bridge_session_id');

  if (!sessionId) {
    // Generate new session ID
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 11);
    sessionId = `session_${timestamp}_${random}`;

    // Store in localStorage
    localStorage.setItem('bridge_session_id', sessionId);
    localStorage.setItem('bridge_session_created', new Date().toISOString());

    console.log('🆔 Generated new session ID:', sessionId);
  }

  return sessionId;
}

/**
 * Get session headers to include in fetch requests
 * @returns {Object} Headers object with X-Session-ID and X-User-ID
 */
export function getSessionHeaders() {
  const headers = {
    'X-Session-ID': getSessionId()
  };

  // Include user ID if available (from AuthContext storage)
  // AuthContext stores user as JSON in 'bridge_user'
  const storedUser = localStorage.getItem('bridge_user');
  if (storedUser) {
    try {
      const userData = JSON.parse(storedUser);
      if (userData?.id) {
        headers['X-User-ID'] = String(userData.id);
      }
    } catch (e) {
      // Ignore parse errors
    }
  }

  // Fallback: check for guest ID
  if (!headers['X-User-ID']) {
    const guestId = localStorage.getItem('bridge_guest_id');
    if (guestId) {
      headers['X-User-ID'] = guestId;
    }
  }

  return headers;
}

/**
 * Clear current session (force new session on next request)
 */
export function clearSession() {
  localStorage.removeItem('bridge_session_id');
  localStorage.removeItem('bridge_session_created');
  console.log('🆔 Session cleared - new session will be created on next request');
}

/**
 * Get session info for debugging
 * @returns {Object} Session information
 */
export function getSessionInfo() {
  return {
    sessionId: getSessionId(),
    created: localStorage.getItem('bridge_session_created') || 'Unknown',
    age: getSessionAge()
  };
}

/**
 * Get session age in minutes
 * @returns {number} Minutes since session created
 */
function getSessionAge() {
  const created = localStorage.getItem('bridge_session_created');
  if (!created) return 0;

  const createdDate = new Date(created);
  const now = new Date();
  return Math.floor((now - createdDate) / (1000 * 60));
}

/**
 * Enhanced fetch with session headers
 * Drop-in replacement for fetch() that automatically adds session headers
 *
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>} Fetch promise
 */
export async function fetchWithSession(url, options = {}) {
  const enhancedOptions = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getSessionHeaders(),
      ...options.headers  // Allow overriding
    }
  };

  return fetch(url, enhancedOptions);
}

export default {
  getSessionId,
  getSessionHeaders,
  clearSession,
  getSessionInfo,
  fetchWithSession
};
