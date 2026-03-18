/**
 * Sentry error tracking configuration for React frontend.
 *
 * Free tier budget: 5K errors/month, 10K perf spans/month, 50 replays/month.
 * Filters browser noise (extensions, ResizeObserver, chunk loading) to conserve quota.
 */
import * as Sentry from '@sentry/react';

// Browser errors that are noise, not bugs
const IGNORED_ERRORS = [
  // Browser internals
  'ResizeObserver loop limit exceeded',
  'ResizeObserver loop completed with undelivered notifications',
  // Network issues (user offline, server restart)
  'Failed to fetch',
  'NetworkError',
  'Load failed',
  // Stale cache after deploy
  /Loading chunk \d+ failed/,
  /Loading CSS chunk \d+ failed/,
  // Safari-specific
  'cancelled',
];

// URLs to ignore errors from (browser extensions, third-party scripts)
const DENY_URLS = [
  /extensions\//i,
  /^chrome:\/\//i,
  /^chrome-extension:\/\//i,
  /^moz-extension:\/\//i,
];

export function initSentry() {
  const dsn = process.env.REACT_APP_SENTRY_DSN;
  if (!dsn) {
    console.log('Sentry DSN not configured — error tracking disabled');
    return;
  }

  Sentry.init({
    dsn,
    // Performance: 10% sampling to stay within 10K spans/month
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: 0.1,
    // Session replay: only record when an error occurs (conserves 50/month budget)
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 1.0,
    // Filter noise
    ignoreErrors: IGNORED_ERRORS,
    denyUrls: DENY_URLS,
    // Only accept errors from our domain
    allowUrls: [
      /mybridgebuddy\.com/,
      /localhost/,
    ],
    environment: process.env.NODE_ENV,
  });
}
