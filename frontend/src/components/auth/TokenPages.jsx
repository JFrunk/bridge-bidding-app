/**
 * Token Landing Pages — Handle URL tokens for email verify and magic link.
 *
 * These render when the app detects /auth/verify?token=... or /auth/magic?token=...
 * in the URL. They auto-process the token and show the result.
 */

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import * as authApi from '../../services/authApi';
import './LoginPage.css';

/**
 * VerifyEmailPage — Processes email verification token from URL.
 */
export function VerifyEmailPage({ token, onDone }) {
  const [status, setStatus] = useState('loading'); // 'loading' | 'success' | 'error'
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setError('No verification token provided');
      return;
    }

    (async () => {
      const result = await authApi.verifyEmail(token);
      if (result.success) {
        setStatus('success');
      } else {
        setStatus('error');
        setError(result.error || 'Verification failed');
      }
    })();
  }, [token]);

  return (
    <div className="token-page">
      <div className="token-card">
        {status === 'loading' && (
          <>
            <div className="token-status">&#8987;</div>
            <h2>Verifying Email...</h2>
            <p>Please wait while we verify your email address.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="token-status">&#10003;</div>
            <h2>Email Verified</h2>
            <p>Your email has been verified successfully.</p>
            <button className="btn-primary" onClick={onDone}>
              Continue
            </button>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="token-status">&#10007;</div>
            <h2>Verification Failed</h2>
            <p>{error}</p>
            <button className="btn-primary" onClick={onDone}>
              Back to App
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * MagicLinkPage — Processes magic link token from URL.
 */
export function MagicLinkPage({ token, onDone }) {
  const { verifyMagicLink } = useAuth();
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setError('No login token provided');
      return;
    }

    (async () => {
      const result = await verifyMagicLink(token);
      if (result.success) {
        setStatus('success');
        // Auto-redirect after brief success message
        setTimeout(() => onDone(), 1500);
      } else {
        setStatus('error');
        setError(result.error || 'Login link is invalid or expired');
      }
    })();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="token-page">
      <div className="token-card">
        {status === 'loading' && (
          <>
            <div className="token-status">&#8987;</div>
            <h2>Signing In...</h2>
            <p>Please wait while we verify your login link.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="token-status">&#10003;</div>
            <h2>Signed In</h2>
            <p>Redirecting you to the app...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="token-status">&#10007;</div>
            <h2>Link Invalid</h2>
            <p>{error}</p>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
              Request a new login link from the sign-in page.
            </p>
            <button className="btn-primary" onClick={onDone}>
              Back to Sign In
            </button>
          </>
        )}
      </div>
    </div>
  );
}
