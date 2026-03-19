/**
 * RegisterPage — Account creation with password strength indicator.
 */

import React, { useState, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './SimpleLogin.css';
import './LoginPage.css';

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
  const { registerV2, continueAsGuest } = useAuth();

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
