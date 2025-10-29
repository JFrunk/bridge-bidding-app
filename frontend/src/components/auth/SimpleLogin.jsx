import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './SimpleLogin.css';

export function SimpleLogin({ onClose }) {
  const [loginMethod, setLoginMethod] = useState('email'); // 'email' or 'phone'
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { simpleLogin, continueAsGuest } = useAuth();

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
      if (result.created) {
        console.log('Welcome! New account created.');
      } else {
        console.log('Welcome back!');
      }
      onClose?.();
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  const handleGuestMode = () => {
    continueAsGuest();
    onClose?.();
  };

  const formatPhoneNumber = (value) => {
    // Remove all non-digit characters
    const cleaned = value.replace(/\D/g, '');

    // Format as (XXX) XXX-XXXX for US numbers
    if (cleaned.length <= 3) {
      return cleaned;
    } else if (cleaned.length <= 6) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
    } else if (cleaned.length <= 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }

    // Limit to 10 digits
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
  };

  const handlePhoneChange = (e) => {
    const value = e.target.value;
    const formatted = formatPhoneNumber(value);
    setPhone(formatted);
  };

  return (
    <div className="simple-login-overlay" onClick={(e) => {
      if (e.target.className === 'simple-login-overlay') onClose?.();
    }}>
      <div className="simple-login-modal">
        <button className="close-button" onClick={onClose} aria-label="Close">
          ×
        </button>

        <h2>Welcome to Bridge Bidding Practice</h2>

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

        <form onSubmit={handleSubmit} className="login-form">
          <p className="login-subtitle">
            {loginMethod === 'email'
              ? 'Enter your email to continue'
              : 'Enter your phone number to continue'}
          </p>

          {loginMethod === 'email' ? (
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                autoFocus
                autoComplete="email"
              />
            </div>
          ) : (
            <div className="form-group">
              <label htmlFor="phone">Phone Number</label>
              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={handlePhoneChange}
                placeholder="(234) 567-8900"
                required
                autoFocus
                autoComplete="tel"
              />
              <small className="input-hint">US number (10 digits)</small>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="displayName">
              Display Name (optional)
            </label>
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="How should we call you?"
              autoComplete="name"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Please wait...' : 'Continue'}
          </button>

          <div className="divider">
            <span>or</span>
          </div>

          <button
            type="button"
            onClick={handleGuestMode}
            className="btn-secondary"
          >
            Continue as Guest
          </button>

          <p className="privacy-note">
            No password required. We'll remember you on this device.
            Your progress will be saved to your {loginMethod === 'email' ? 'email' : 'phone number'}.
          </p>
        </form>
      </div>
    </div>
  );
}
