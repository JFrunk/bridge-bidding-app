/**
 * LoginPage — Auth V2 login modal.
 *
 * Replaces SimpleLogin with:
 *  - Password login tab
 *  - Magic link tab
 *  - Google Sign-In button
 *  - "Create Account" link → RegisterPage
 *  - "Continue as Guest" fallback
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './SimpleLogin.css';
import './LoginPage.css';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

export function LoginPage({ onClose, onSwitchToRegister, onForgotPassword }) {
  const { loginV2, requestMagicLink, loginWithGoogle, continueAsGuest } = useAuth();

  const [tab, setTab] = useState('password'); // 'password' | 'magic'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setError('');
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
  };

  const handleMagicLink = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await requestMagicLink(email);

    if (result.success) {
      setSuccess('Check your email for a login link.');
    } else {
      setError(result.error || 'Failed to send login link');
    }
    setLoading(false);
  };

  const handleGoogleLogin = () => {
    if (!GOOGLE_CLIENT_ID || !window.google) return;

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
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

    window.google.accounts.id.prompt();
  };

  const handleGuest = () => {
    continueAsGuest();
    onClose();
  };

  const isEmailValid = email.includes('@') && email.includes('.');

  return (
    <div className="simple-login-overlay">
      <div className="simple-login-modal login-page-modal">
        <h2>MyBridgeBuddy</h2>
        <p className="login-subtitle">Sign in to continue</p>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        {/* Google Sign-In */}
        {GOOGLE_CLIENT_ID && (
          <>
            <button
              className="btn-google"
              onClick={handleGoogleLogin}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" width="18" height="18">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Sign in with Google
            </button>
            <div className="divider"><span>or</span></div>
          </>
        )}

        {/* Tabs */}
        <div className="login-method-toggle">
          <button
            className={`toggle-btn ${tab === 'password' ? 'active' : ''}`}
            onClick={() => { setTab('password'); setError(''); setSuccess(''); }}
          >
            Password
          </button>
          <button
            className={`toggle-btn ${tab === 'magic' ? 'active' : ''}`}
            onClick={() => { setTab('magic'); setError(''); setSuccess(''); }}
          >
            Magic Link
          </button>
        </div>

        {/* Password Tab */}
        {tab === 'password' && (
          <form onSubmit={handlePasswordLogin}>
            <div className="form-group">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </div>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !isEmailValid || !password}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
            {onForgotPassword && (
              <div className="forgot-link">
                <button
                  type="button"
                  className="text-link"
                  onClick={() => onForgotPassword(email)}
                >
                  Forgot password?
                </button>
              </div>
            )}
          </form>
        )}

        {/* Magic Link Tab */}
        {tab === 'magic' && !success && (
          <form onSubmit={handleMagicLink}>
            <div className="form-group">
              <label htmlFor="magic-email">Email</label>
              <input
                id="magic-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
              <span className="input-hint">
                We'll send you a one-click login link. No password needed.
              </span>
            </div>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !isEmailValid}
            >
              {loading ? 'Sending...' : 'Send Login Link'}
            </button>
          </form>
        )}

        <div className="divider"><span>or</span></div>

        {/* Bottom Links */}
        <div className="auth-links">
          {onSwitchToRegister && (
            <button className="text-link" onClick={onSwitchToRegister}>
              Create an account
            </button>
          )}
          <button className="text-link text-link-muted" onClick={handleGuest}>
            Continue as guest
          </button>
        </div>
      </div>
    </div>
  );
}
