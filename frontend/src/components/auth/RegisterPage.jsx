/**
 * RegisterPage — Account creation with password strength indicator.
 */

import React, { useState, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './SimpleLogin.css';
import './LoginPage.css';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

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

export function RegisterPage({ onClose, onSwitchToLogin }) {
  const { registerV2, loginWithGoogle, continueAsGuest } = useAuth();

  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const strength = useMemo(() => getPasswordStrength(password), [password]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    const result = await registerV2({
      email,
      password,
      displayName: displayName || undefined,
    });

    if (result.success) {
      onClose();
    } else {
      setError(result.error || 'Registration failed');
    }
    setLoading(false);
  };

  const handleGuest = () => {
    continueAsGuest();
    onClose();
  };

  const isEmailValid = email.includes('@') && email.includes('.');
  const canSubmit = isEmailValid && password.length >= 8 && password === confirmPassword;

  return (
    <div className="simple-login-overlay">
      <div className="simple-login-modal login-page-modal">
        <h2>Create Account</h2>
        <p className="login-subtitle">Start tracking your bridge progress</p>

        {error && <div className="error-message">{error}</div>}

        {/* Google Sign-Up */}
        {GOOGLE_CLIENT_ID && (
          <>
            <button
              className="btn-google"
              onClick={() => {
                if (!window.google) return;
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
              }}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" width="18" height="18">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Sign up with Google
            </button>
            <div className="divider"><span>or</span></div>
          </>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="reg-email">Email</label>
            <input
              id="reg-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-name">Display Name (optional)</label>
            <input
              id="reg-name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="How should we call you?"
              autoComplete="name"
              maxLength={30}
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              required
              minLength={8}
            />
            {password && (
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

          <div className="form-group">
            <label htmlFor="reg-confirm">Confirm Password</label>
            <input
              id="reg-confirm"
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

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !canSubmit}
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="divider"><span>or</span></div>

        <div className="auth-links">
          {onSwitchToLogin && (
            <button className="text-link" onClick={onSwitchToLogin}>
              Already have an account? Sign in
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
