import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './RegistrationPrompt.css';

export function RegistrationPrompt({
  message = "You're doing great! Create an account to save your progress.",
  onClose
}) {
  const [loginMethod, setLoginMethod] = useState('email');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { simpleLogin, dismissRegistrationPrompt, handsCompleted } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const identifier = loginMethod === 'email' ? email : phone;

    if (!identifier) {
      setError(`${loginMethod === 'email' ? 'Email' : 'Phone number'} is required`);
      setLoading(false);
      return;
    }

    const result = await simpleLogin(identifier, loginMethod);

    if (result.success) {
      onClose?.();
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  const handleDismiss = (permanent = false) => {
    dismissRegistrationPrompt(permanent);
    onClose?.();
  };

  const formatPhoneNumber = (value) => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length <= 3) return cleaned;
    if (cleaned.length <= 6) return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
  };

  return (
    <div className="registration-prompt-overlay" onClick={(e) => {
      if (e.target.className === 'registration-prompt-overlay') handleDismiss(false);
    }}>
      <div className="registration-prompt-modal">
        <button
          className="close-button"
          onClick={() => handleDismiss(false)}
          aria-label="Close"
        >
          ×
        </button>

        <div className="prompt-header">
          <span className="prompt-icon">🎉</span>
          <h2>Save Your Progress!</h2>
        </div>

        <p className="prompt-message">
          {message}
        </p>

        <div className="progress-stats">
          <div className="stat">
            <span className="stat-value">{handsCompleted}</span>
            <span className="stat-label">Hands Played</span>
          </div>
        </div>

        <div className="benefits-list">
          <div className="benefit">
            <span className="benefit-icon">📊</span>
            <span>Track your improvement over time</span>
          </div>
          <div className="benefit">
            <span className="benefit-icon">📈</span>
            <span>View detailed performance analytics</span>
          </div>
          <div className="benefit">
            <span className="benefit-icon">🏆</span>
            <span>Earn achievements and milestones</span>
          </div>
        </div>

        <div className="login-method-toggle">
          <button
            type="button"
            className={`toggle-btn ${loginMethod === 'email' ? 'active' : ''}`}
            onClick={() => setLoginMethod('email')}
          >
            📧 Email
          </button>
          <button
            type="button"
            className={`toggle-btn ${loginMethod === 'phone' ? 'active' : ''}`}
            onClick={() => setLoginMethod('phone')}
          >
            📱 Phone
          </button>
        </div>

        <form onSubmit={handleSubmit} className="registration-form">
          {loginMethod === 'email' ? (
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              autoFocus
              autoComplete="email"
            />
          ) : (
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(formatPhoneNumber(e.target.value))}
              placeholder="(234) 567-8900"
              autoFocus
              autoComplete="tel"
            />
          )}

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating Account...' : 'Save My Progress'}
          </button>
        </form>

        <div className="prompt-footer">
          <button
            type="button"
            className="btn-text"
            onClick={() => handleDismiss(false)}
          >
            Maybe Later
          </button>
          <span className="separator">•</span>
          <button
            type="button"
            className="btn-text muted"
            onClick={() => handleDismiss(true)}
          >
            Don't Ask Again
          </button>
        </div>

        <p className="privacy-note">
          No password required. We'll remember you on this device.
        </p>
      </div>
    </div>
  );
}
