/**
 * ResetPasswordPage — Set new password from reset token (URL param).
 */

import React, { useState, useMemo } from 'react';
import * as authApi from '../../services/authApi';
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

export function ResetPasswordPage({ token, onDone }) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const strength = useMemo(() => getPasswordStrength(password), [password]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    const result = await authApi.resetPassword({ token, password });

    if (result.success) {
      setSuccess(true);
    } else {
      setError(result.error || 'Password reset failed');
    }
    setLoading(false);
  };

  if (success) {
    return (
      <div className="token-page">
        <div className="token-card">
          <div className="token-status">&#10003;</div>
          <h2>Password Reset</h2>
          <p>Your password has been updated. Please sign in with your new password.</p>
          <button className="btn-primary" onClick={onDone}>
            Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="token-page">
      <div className="token-card" style={{ textAlign: 'left' }}>
        <h2 style={{ textAlign: 'center' }}>Set New Password</h2>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="new-password">New Password</label>
            <input
              id="new-password"
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
            <label htmlFor="confirm-new-password">Confirm Password</label>
            <input
              id="confirm-new-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
              autoComplete="new-password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || password.length < 8 || password !== confirmPassword}
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
      </div>
    </div>
  );
}
