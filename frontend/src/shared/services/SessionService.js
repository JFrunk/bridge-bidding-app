/**
 * SessionService
 *
 * Frontend service for managing sessions with the backend.
 * Handles session creation, storage, and retrieval.
 */

const SESSION_STORAGE_KEY = 'bridge_session_id';

class SessionService {
  constructor() {
    this.sessionId = null;
    this.sessionType = null;
    this.loadFromStorage();
  }

  /**
   * Load session ID from localStorage
   */
  loadFromStorage() {
    try {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        this.sessionId = data.sessionId;
        this.sessionType = data.sessionType;
      }
    } catch (error) {
      console.error('Failed to load session from storage:', error);
    }
  }

  /**
   * Save session ID to localStorage
   */
  saveToStorage() {
    try {
      if (this.sessionId) {
        localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
          sessionId: this.sessionId,
          sessionType: this.sessionType,
          timestamp: Date.now()
        }));
      } else {
        localStorage.removeItem(SESSION_STORAGE_KEY);
      }
    } catch (error) {
      console.error('Failed to save session to storage:', error);
    }
  }

  /**
   * Create a new session
   *
   * @param {string} type - Session type ('bidding', 'play', 'integrated')
   * @param {string|null} userId - Optional user ID
   * @returns {Promise<string>} Session ID
   */
  async createSession(type, userId = null) {
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

    try {
      const response = await fetch(`${API_URL}/api/session/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_type: type,
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`);
      }

      const data = await response.json();
      this.sessionId = data.session_id;
      this.sessionType = type;
      this.saveToStorage();

      return this.sessionId;
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  }

  /**
   * Get current session ID
   *
   * @returns {string|null} Current session ID
   */
  getSessionId() {
    return this.sessionId;
  }

  /**
   * Get current session type
   *
   * @returns {string|null} Current session type
   */
  getSessionType() {
    return this.sessionType;
  }

  /**
   * Clear current session
   */
  clearSession() {
    this.sessionId = null;
    this.sessionType = null;
    this.saveToStorage();
  }

  /**
   * Check if session exists
   *
   * @returns {boolean} True if session exists
   */
  hasSession() {
    return this.sessionId !== null;
  }

  /**
   * Ensure session exists, create if needed
   *
   * @param {string} type - Session type if creation needed
   * @returns {Promise<string>} Session ID
   */
  async ensureSession(type) {
    if (!this.hasSession()) {
      await this.createSession(type);
    }
    return this.sessionId;
  }

  /**
   * Add session ID to API call options
   *
   * @param {Object} options - Fetch options object
   * @returns {Object} Modified options with session ID
   */
  addSessionToRequest(options = {}) {
    if (!this.sessionId) {
      return options;
    }

    const headers = options.headers || {};
    headers['X-Session-ID'] = this.sessionId;

    return {
      ...options,
      headers
    };
  }
}

// Singleton instance
const sessionService = new SessionService();

export default sessionService;
