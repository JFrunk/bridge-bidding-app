import ReactGA from 'react-ga4';

/**
 * Google Analytics Service
 *
 * Provides a centralized interface for all analytics tracking.
 * Uses GA4 (Google Analytics 4) via react-ga4.
 */

// Initialize GA4
export const initializeAnalytics = () => {
  const measurementId = process.env.REACT_APP_GA_MEASUREMENT_ID;

  if (measurementId) {
    ReactGA.initialize(measurementId, {
      gaOptions: {
        anonymizeIp: true, // Privacy: anonymize IP addresses
      },
    });
    console.log('[Analytics] Google Analytics initialized:', measurementId);
  } else {
    console.warn('[Analytics] GA_MEASUREMENT_ID not found. Analytics disabled.');
  }
};

// Check if analytics is enabled
export const isAnalyticsEnabled = () => {
  return !!process.env.REACT_APP_GA_MEASUREMENT_ID;
};

// Set user ID for logged-in users (links sessions across devices)
export const setUserId = (userId) => {
  if (!isAnalyticsEnabled()) return;

  ReactGA.gtag('config', process.env.REACT_APP_GA_MEASUREMENT_ID, {
    user_id: userId,
  });
  console.log('[Analytics] User ID set:', userId);
};

// Clear user ID on logout
export const clearUserId = () => {
  if (!isAnalyticsEnabled()) return;

  ReactGA.gtag('config', process.env.REACT_APP_GA_MEASUREMENT_ID, {
    user_id: null,
  });
  console.log('[Analytics] User ID cleared');
};

// Track page views (called automatically by routing)
export const trackPageView = (path, title) => {
  if (!isAnalyticsEnabled()) return;

  ReactGA.send({
    hitType: 'pageview',
    page: path,
    title: title || document.title,
  });
  console.log('[Analytics] Page view:', path);
};

// Generic event tracking
export const trackEvent = (category, action, label, value) => {
  if (!isAnalyticsEnabled()) return;

  ReactGA.event({
    category,
    action,
    label,
    value,
  });
  console.log('[Analytics] Event:', { category, action, label, value });
};

// === AUTHENTICATION EVENTS ===

export const trackLogin = (method) => {
  trackEvent('Authentication', 'Login', method);
};

export const trackLogout = () => {
  trackEvent('Authentication', 'Logout');
};

export const trackGuestMode = () => {
  trackEvent('Authentication', 'Guest Mode');
};

// === GAMEPLAY EVENTS ===

export const trackDealHand = (mode) => {
  trackEvent('Gameplay', 'Deal Hand', mode); // mode: 'random', 'scenario', 'daily_hand'
};

export const trackBidMade = (bid, isUser, score) => {
  const actor = isUser ? 'User' : 'AI';
  trackEvent('Gameplay', `Bid Made - ${actor}`, bid, score);
};

export const trackCardPlayed = (isUser) => {
  const actor = isUser ? 'User' : 'AI';
  trackEvent('Gameplay', `Card Played - ${actor}`);
};

export const trackHandComplete = (contractMade, declarerMade, tricksWon) => {
  trackEvent('Gameplay', 'Hand Complete', contractMade ? 'Made' : 'Failed', tricksWon);
};

export const trackBiddingComplete = (finalContract, declarer) => {
  trackEvent('Gameplay', 'Bidding Complete', finalContract);
};

// === LEARNING EVENTS ===

export const trackDashboardOpen = () => {
  trackEvent('Learning', 'Dashboard Opened');
};

export const trackFeedbackViewed = (bidRating) => {
  trackEvent('Learning', 'Feedback Viewed', bidRating); // 'optimal', 'acceptable', etc.
};

export const trackScenarioSelected = (scenarioName) => {
  trackEvent('Learning', 'Scenario Selected', scenarioName);
};

export const trackDailyHandStart = () => {
  trackEvent('Learning', 'Daily Hand Started');
};

export const trackDailyHandComplete = (success) => {
  trackEvent('Learning', 'Daily Hand Complete', success ? 'Success' : 'Failed');
};

// === MODE CHANGES ===

export const trackModeChange = (newMode) => {
  trackEvent('Navigation', 'Mode Changed', newMode); // 'freeplay', 'scenarios', 'daily_hand'
};

// === ERROR TRACKING ===

export const trackError = (errorType, errorMessage) => {
  trackEvent('Error', errorType, errorMessage);
};

// === USER FEEDBACK ===

export const trackFeedbackSubmitted = (feedbackType) => {
  trackEvent('User Feedback', 'Feedback Submitted', feedbackType);
};

export default {
  initializeAnalytics,
  isAnalyticsEnabled,
  setUserId,
  clearUserId,
  trackPageView,
  trackEvent,
  trackLogin,
  trackLogout,
  trackGuestMode,
  trackDealHand,
  trackBidMade,
  trackCardPlayed,
  trackHandComplete,
  trackBiddingComplete,
  trackDashboardOpen,
  trackFeedbackViewed,
  trackScenarioSelected,
  trackDailyHandStart,
  trackDailyHandComplete,
  trackModeChange,
  trackError,
  trackFeedbackSubmitted,
};
