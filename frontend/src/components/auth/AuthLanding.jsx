/**
 * AuthLanding — Unified auth page (Canva-style).
 *
 * Single flow: "Continue with Google" or "Continue with email".
 * Email flow auto-detects login vs register based on whether account exists.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { requestPasswordReset } from '../../services/authApi';
import './AuthLanding.css';
import { ReactComponent as BrandIcon } from '../../assets/branding/icon.svg';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

// Inline password strength (same logic as RegisterPage)
function getPasswordStrength(password) {
  if (!password) return { score: 0, label: '', level: '' };
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 2) return { score, label: 'Weak', level: 'weak' };
  if (score <= 3) return { score, label: 'Fair', level: 'fair' };
  return { score, label: 'Strong', level: 'strong' };
}

export function AuthLanding({ onClose, hideGuest }) {
  const { loginV2, registerV2, loginWithGoogle, continueAsGuest } = useAuth();

  const [mode, setMode] = useState('buttons'); // 'buttons' | 'email'
  const [emailMode, setEmailMode] = useState(null); // null | 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [gsiReady, setGsiReady] = useState(!!window.google?.accounts?.id);
  const [resetSent, setResetSent] = useState(false);

  // Poll for GSI readiness (loads async from index.html script tag)
  useEffect(() => {
    if (gsiReady || !GOOGLE_CLIENT_ID) return;
    const interval = setInterval(() => {
      if (window.google?.accounts?.id) {
        setGsiReady(true);
        clearInterval(interval);
      }
    }, 200);
    return () => clearInterval(interval);
  }, [gsiReady]);

  const strength = useMemo(() => getPasswordStrength(password), [password]);

  const googleBtnRef = React.useRef(null);

  // Initialize GSI and render a hidden Google button (clicked programmatically)
  useEffect(() => {
    if (!gsiReady || !GOOGLE_CLIENT_ID) return;
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      ux_mode: 'popup',
      callback: async (response) => {
        setError('');
        setLoading(true);
        const result = await loginWithGoogle(response.credential);
        if (result.success) {
          onClose();
        } else {
          setError(result.error || 'Google sign-in failed');
        }
        setLoading(false);
      },
    });
    // Render hidden Google button so we can trigger its popup via click
    if (googleBtnRef.current) {
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        type: 'icon',
        size: 'large',
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gsiReady]);

  const handleGoogleLogin = () => {
    // Programmatically click the hidden Google button to trigger popup
    const btn = googleBtnRef.current?.querySelector('[role="button"]');
    if (btn) {
      btn.click();
    }
  };

  const handleEmailContinue = async (e) => {
    e.preventDefault();
    setError('');

    // First submission: try to register
    if (!emailMode) {
      if (password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }

      setLoading(true);
      const result = await registerV2({ email, password, displayName: displayName || undefined });

      if (result.success) {
        onClose();
        return;
      }

      // Account exists — switch to login mode
      if (result.status === 409) {
        setEmailMode('login');
        setPassword('');
        setConfirmPassword('');
        setError('');
      } else {
        setError(result.error || 'Something went wrong');
      }
      setLoading(false);
      return;
    }

    // Login mode
    if (emailMode === 'login') {
      setLoading(true);
      const result = await loginV2({ email, password });
      if (result.success) {
        onClose();
      } else {
        if (result.status === 429) {
          setError('Account temporarily locked. Try again in 15 minutes.');
        } else {
          setError(result.error || 'Invalid email or password');
        }
      }
      setLoading(false);
    }
  };

  const handleGuest = () => {
    continueAsGuest();
    onClose();
  };

  const handleForgotPassword = async () => {
    if (!email) {
      setError('Please enter your email address first');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await requestPasswordReset(email);
      setResetSent(true);
    } catch {
      setError('Failed to send reset email. Please try again.');
    }
    setLoading(false);
  };

  const isEmailValid = email.includes('@') && email.includes('.');
  const canSubmitNew = isEmailValid && password.length >= 8 && password === confirmPassword;
  const canSubmitLogin = isEmailValid && password.length > 0;

  // Button mode — show Continue with Google / Continue with email
  if (mode === 'buttons') {
    return (
      <div className="auth-landing-overlay">
        <div className="auth-landing-modal">
          <BrandIcon className="auth-brand-icon" aria-label="My Bridge Buddy" />
          <h1>Log in or sign up in seconds</h1>
          <p className="auth-landing-subtitle">
            Use your email or another service to continue with MyBridgeBuddy (it's free)!
          </p>

          {/* Hidden Google button — clicked programmatically to open popup */}
          <div ref={googleBtnRef} style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }} />

          <div className="auth-landing-buttons">
            {GOOGLE_CLIENT_ID && (
              <button className="auth-provider-btn" onClick={handleGoogleLogin} disabled={loading || !gsiReady}>
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </button>
            )}

            <button className="auth-provider-btn" onClick={() => setMode('email')}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="M22 4L12 13 2 4"/>
              </svg>
              Continue with email
            </button>

            {!hideGuest && (
              <button className="auth-provider-btn" onClick={handleGuest}>
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="8" r="4"/>
                  <path d="M20 21a8 8 0 0 0-16 0"/>
                </svg>
                Continue as guest
              </button>
            )}
          </div>

          {error && <div className="auth-landing-error">{error}</div>}
        </div>
      </div>
    );
  }

  // Email mode — smart form
  return (
    <div className="auth-landing-overlay">
      <div className="auth-landing-modal">
        <button className="auth-back-btn" onClick={() => { setMode('buttons'); setEmailMode(null); setError(''); setPassword(''); }}>
          &larr; Back
        </button>

        <h1>{emailMode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
        {emailMode === 'login' && (
          <p className="auth-landing-subtitle">Account found for <strong>{email}</strong></p>
        )}

        {error && <div className="auth-landing-error">{error}</div>}

        <form onSubmit={handleEmailContinue}>
          {/* Email — always shown, but disabled in login mode (already set) */}
          {emailMode !== 'login' && (
            <div className="form-group">
              <label htmlFor="auth-email">Email</label>
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
                autoFocus
              />
            </div>
          )}

          {/* Display name — only for new accounts */}
          {!emailMode && (
            <div className="form-group">
              <label htmlFor="auth-name">Display Name (optional)</label>
              <input
                id="auth-name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="How should we call you?"
                autoComplete="name"
                maxLength={30}
              />
            </div>
          )}

          {/* Password */}
          <div className="form-group">
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={emailMode === 'login' ? 'Enter your password' : 'At least 8 characters'}
              autoComplete={emailMode === 'login' ? 'current-password' : 'new-password'}
              required
              autoFocus={emailMode === 'login'}
            />
            {/* Password requirements — only for new accounts */}
            {!emailMode && !password && (
              <span className="input-hint">Min 8 characters. Mix uppercase, lowercase, numbers, and symbols for a stronger password.</span>
            )}
            {/* Strength indicator — only for new accounts */}
            {!emailMode && password && (
              <>
                <div className="password-strength">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className={`password-strength-bar ${strength.score >= i * 2 - 1 ? strength.level : ''}`}
                    />
                  ))}
                </div>
                <div className={`password-strength-label ${strength.level}`}>
                  {strength.label}
                </div>
              </>
            )}
          </div>

          {/* Confirm password — only for new accounts */}
          {!emailMode && (
            <div className="form-group">
              <label htmlFor="auth-confirm">Confirm Password</label>
              <input
                id="auth-confirm"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                autoComplete="new-password"
                required
              />
              {confirmPassword && password !== confirmPassword && (
                <span className="input-hint" style={{ color: 'var(--color-danger)' }}>
                  Passwords do not match
                </span>
              )}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || (emailMode === 'login' ? !canSubmitLogin : !canSubmitNew)}
          >
            {loading ? 'Please wait...' : emailMode === 'login' ? 'Sign In' : 'Create Account'}
          </button>

          {/* Forgot password — only in login mode */}
          {emailMode === 'login' && (
            <div className="forgot-link">
              {resetSent ? (
                <span className="reset-sent-msg">Reset link sent to {email}. Check your inbox.</span>
              ) : (
                <button type="button" className="text-link" onClick={handleForgotPassword} disabled={loading}>
                  Forgot password?
                </button>
              )}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
