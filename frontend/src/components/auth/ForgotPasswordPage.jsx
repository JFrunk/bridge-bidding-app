/**
 * ForgotPasswordPage — Request password reset email.
 */

import React, { useState } from 'react';
import * as authApi from '../../services/authApi';
import './SimpleLogin.css';
import './LoginPage.css';

export function ForgotPasswordPage({ onClose, onBackToLogin, prefillEmail }) {
  const [email, setEmail] = useState(prefillEmail || '');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await authApi.requestPasswordReset(email);

    if (result.success) {
      setSent(true);
    } else {
      setError(result.error || 'Failed to send reset email');
    }
    setLoading(false);
  };

  return (
    <div className="simple-login-overlay">
      <div className="simple-login-modal login-page-modal">
        <h2>Reset Password</h2>

        {sent ? (
          <>
            <div className="success-message">
              If an account exists with that email, a reset link has been sent.
            </div>
            <p className="login-subtitle">Check your inbox and follow the link to set a new password.</p>
            <button className="btn-primary" onClick={onBackToLogin || onClose}>
              Back to Sign In
            </button>
          </>
        ) : (
          <>
            <p className="login-subtitle">
              Enter your email and we'll send you a link to reset your password.
            </p>

            {error && <div className="error-message">{error}</div>}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="reset-email">Email</label>
                <input
                  id="reset-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                  autoFocus
                />
              </div>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading || !email.includes('@')}
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>

            <div className="divider"><span>or</span></div>

            <div className="auth-links">
              <button className="text-link" onClick={onBackToLogin || onClose}>
                Back to Sign In
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
