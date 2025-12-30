/**
 * API Service Layer with Session Management
 *
 * This module provides a centralized API service that:
 * - Manages session IDs for backend session state isolation
 * - Provides helper functions for all API endpoints
 * - Handles common error scenarios
 * - Ensures all requests include proper session headers
 *
 * Usage:
 *   import api from './services/api';
 *   const data = await api.dealHands();
 */

// API URL configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

/**
 * Session ID Management
 *
 * Generates a unique session ID on first access and stores it in localStorage.
 * This ensures each user/tab gets isolated game state on the backend.
 */
class SessionManager {
  constructor() {
    this.sessionId = null;
  }

  /**
   * Get or create session ID
   * @returns {string} Unique session identifier
   */
  getSessionId() {
    if (this.sessionId) {
      return this.sessionId;
    }

    // Try to retrieve from localStorage
    let sessionId = localStorage.getItem('bridge_session_id');

    if (!sessionId) {
      // Generate new session ID
      sessionId = this.generateSessionId();
      localStorage.setItem('bridge_session_id', sessionId);
      console.log('🆔 Generated new session ID:', sessionId);
    } else {
      console.log('🆔 Using existing session ID:', sessionId);
    }

    this.sessionId = sessionId;
    return sessionId;
  }

  /**
   * Generate a unique session ID
   * @returns {string} New session ID
   */
  generateSessionId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 11);
    return `session_${timestamp}_${random}`;
  }

  /**
   * Clear current session (force new session on next request)
   */
  clearSession() {
    localStorage.removeItem('bridge_session_id');
    this.sessionId = null;
    console.log('🆔 Session cleared');
  }

  /**
   * Get session info for debugging
   */
  getSessionInfo() {
    return {
      sessionId: this.getSessionId(),
      created: localStorage.getItem('bridge_session_created') || 'Unknown'
    };
  }
}

// Singleton instance
const sessionManager = new SessionManager();

/**
 * API Request Helper
 *
 * Wrapper around fetch that adds session headers and error handling
 */
class ApiClient {
  constructor() {
    this.baseUrl = API_URL;
    this.sessionManager = sessionManager;
  }

  /**
   * Make an API request with session headers
   * @param {string} endpoint - API endpoint (e.g., '/api/deal-hands')
   * @param {Object} options - Fetch options
   * @returns {Promise<Object>} Response data
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const sessionId = this.sessionManager.getSessionId();

    // Build headers
    const headers = {
      'Content-Type': 'application/json',
      'X-Session-ID': sessionId,
      ...options.headers
    };

    // Build request options
    const requestOptions = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, requestOptions);

      // Handle non-OK responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * GET request
   */
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // ============================================================================
  // SESSION ENDPOINTS
  // ============================================================================

  /**
   * Start a new game session
   * @param {Object} params - Session parameters
   * @returns {Promise<Object>} Session data
   */
  async startSession(params = {}) {
    const data = {
      user_id: params.userId || 1,
      session_type: params.sessionType || 'chicago',
      player_position: params.playerPosition || 'S',
      ai_difficulty: params.aiDifficulty || 'expert'  // Default to expert (DDS when available)
    };
    return this.post('/api/session/start', data);
  }

  /**
   * Get current session status
   */
  async getSessionStatus() {
    return this.get('/api/session/status');
  }

  /**
   * Complete current hand
   */
  async completeSessionHand(scoreData) {
    return this.post('/api/session/complete-hand', { score_data: scoreData });
  }

  /**
   * Get session history
   */
  async getSessionHistory() {
    return this.get('/api/session/history');
  }

  /**
   * Abandon current session
   */
  async abandonSession() {
    return this.post('/api/session/abandon', {});
  }

  /**
   * Get session stats
   */
  async getSessionStats(userId = 1) {
    return this.get(`/api/session/stats?user_id=${userId}`);
  }

  // ============================================================================
  // AI ENDPOINTS
  // ============================================================================

  /**
   * Get AI status
   */
  async getAiStatus() {
    return this.get('/api/ai/status');
  }

  /**
   * Get available AI difficulties
   */
  async getAiDifficulties() {
    return this.get('/api/ai-difficulties');
  }

  /**
   * Set AI difficulty
   */
  async setAiDifficulty(difficulty) {
    return this.post('/api/set-ai-difficulty', { difficulty });
  }

  /**
   * Get AI statistics
   */
  async getAiStatistics() {
    return this.get('/api/ai-statistics');
  }

  // ============================================================================
  // BIDDING ENDPOINTS
  // ============================================================================

  /**
   * Get available scenarios
   */
  async getScenarios() {
    return this.get('/api/scenarios');
  }

  /**
   * Load a specific scenario
   */
  async loadScenario(scenarioName) {
    return this.post('/api/load-scenario', { name: scenarioName });
  }

  /**
   * Deal new hands
   */
  async dealHands() {
    return this.get('/api/deal-hands');
  }

  /**
   * Get next AI bid
   */
  async getNextBid(auctionHistory, currentPlayer, explanationLevel = 'detailed') {
    return this.post('/api/get-next-bid', {
      auction_history: auctionHistory,
      current_player: currentPlayer,
      explanation_level: explanationLevel
    });
  }

  /**
   * Get next bid with structured explanation
   */
  async getNextBidStructured(auctionHistory, currentPlayer) {
    return this.post('/api/get-next-bid-structured', {
      auction_history: auctionHistory,
      current_player: currentPlayer
    });
  }

  /**
   * Get feedback on user's bid
   */
  async getFeedback(auctionHistory, explanationLevel = 'detailed') {
    return this.post('/api/get-feedback', {
      auction_history: auctionHistory,
      explanation_level: explanationLevel
    });
  }

  /**
   * Get all hands
   */
  async getAllHands() {
    return this.get('/api/get-all-hands');
  }

  /**
   * Request review
   */
  async requestReview(reviewData) {
    return this.post('/api/request-review', reviewData);
  }

  /**
   * Get convention info
   */
  async getConventionInfo(name) {
    const query = name ? `?name=${encodeURIComponent(name)}` : '';
    return this.get(`/api/convention-info${query}`);
  }

  // ============================================================================
  // PLAY ENDPOINTS
  // ============================================================================

  /**
   * Start card play phase
   */
  async startPlay(auctionHistory, vulnerability, hands = null) {
    return this.post('/api/start-play', {
      auction_history: auctionHistory,
      vulnerability: vulnerability,
      hands: hands
    });
  }

  /**
   * Play a card
   */
  async playCard(card, position = 'South') {
    return this.post('/api/play-card', {
      card: card,
      position: position
    });
  }

  /**
   * Get AI card play
   */
  async getAiPlay() {
    return this.post('/api/get-ai-play', {});
  }

  /**
   * Get current play state
   */
  async getPlayState() {
    return this.get('/api/get-play-state');
  }

  /**
   * Clear current trick
   */
  async clearTrick() {
    return this.post('/api/clear-trick', {});
  }

  /**
   * Complete play and get final score
   */
  async completePlay(vulnerability = null) {
    if (vulnerability) {
      return this.post('/api/complete-play', { vulnerability });
    }
    return this.get('/api/complete-play');
  }
}

// Create singleton instance
const api = new ApiClient();

// Export both the API client and session manager
export default api;
export { sessionManager };
