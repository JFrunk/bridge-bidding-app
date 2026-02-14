import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { PrivacyPolicy } from '../legal/PrivacyPolicy';
import { AboutUs } from '../legal/AboutUs';
import './SimpleLogin.css';

export function SimpleLogin({ onClose }) {
  const [userType, setUserType] = useState('new'); // 'new' or 'returning'
  const [loginMethod, setLoginMethod] = useState('email'); // 'email' or 'phone'
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);
  const [showAboutUs, setShowAboutUs] = useState(false);
  const { simpleLogin, continueAsGuest } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
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
        // New user created
        setSuccessMessage('Welcome! Your account has been created.');
        setTimeout(() => onClose?.(), 1500);
      } else {
        // Existing user found
        setSuccessMessage('Welcome back!');
        setTimeout(() => onClose?.(), 1000);
      }
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
    <div className="simple-login-overlay" data-testid="login-overlay" onClick={(e) => {
      if (e.target.className === 'simple-login-overlay') onClose?.();
    }}>
      <div className="simple-login-modal" data-testid="login-modal">
        <button className="close-button" data-testid="login-close-button" onClick={onClose} aria-label="Close">
          ×
        </button>

        <h2>Welcome to My Bridge Buddy</h2>

        {/* New/Returning User Tabs */}
        <div className="user-type-tabs" data-testid="user-type-tabs">
          <button
            type="button"
            className={`user-type-tab ${userType === 'new' ? 'active' : ''}`}
            onClick={() => { setUserType('new'); setError(''); setSuccessMessage(''); }}
            data-testid="tab-new-user"
          >
            New User
          </button>
          <button
            type="button"
            className={`user-type-tab ${userType === 'returning' ? 'active' : ''}`}
            onClick={() => { setUserType('returning'); setError(''); setSuccessMessage(''); }}
            data-testid="tab-returning-user"
          >
            Returning User
          </button>
        </div>

        {/* Email/Phone Toggle */}
        <div className="login-method-toggle" data-testid="login-method-toggle">
          <button
            type="button"
            className={`toggle-btn ${loginMethod === 'email' ? 'active' : ''}`}
            onClick={() => setLoginMethod('email')}
            data-testid="login-toggle-email"
          >
            Email
          </button>
          <button
            type="button"
            className={`toggle-btn ${loginMethod === 'phone' ? 'active' : ''}`}
            onClick={() => setLoginMethod('phone')}
            data-testid="login-toggle-phone"
          >
            Phone
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form" data-testid="login-form">
          <p className="login-subtitle">
            {userType === 'new'
              ? (loginMethod === 'email'
                  ? 'Enter your email to create an account'
                  : 'Enter your phone number to create an account')
              : (loginMethod === 'email'
                  ? 'Enter your email to sign in'
                  : 'Enter your phone number to sign in')
            }
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
                autoComplete="username"
                data-testid="login-email-input"
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
                data-testid="login-phone-input"
              />
              <small className="input-hint">US number (10 digits)</small>
            </div>
          )}

          {userType === 'new' && (
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
                data-testid="login-displayname-input"
              />
            </div>
          )}

          {error && <div className="error-message" data-testid="login-error">{error}</div>}
          {successMessage && <div className="success-message" data-testid="login-success">{successMessage}</div>}

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            data-testid="login-submit-button"
          >
            {loading ? 'Please wait...' : (userType === 'new' ? 'Create Account' : 'Sign In')}
          </button>

          {/* Forgot email hint for returning users */}
          {userType === 'returning' && loginMethod === 'email' && (
            <p className="forgot-hint">
              Forgot which email you used? Search your inbox for "Bridge Buddy" to find your welcome email.
            </p>
          )}

          <div className="divider">
            <span>or</span>
          </div>

          <button
            type="button"
            onClick={handleGuestMode}
            className="btn-secondary"
            data-testid="login-guest-button"
          >
            Continue as Guest
          </button>

          <p className="privacy-note">
            <span className="security-badge">🔒 Secure, Password-less Login</span>
            <br />
            {userType === 'new'
              ? `We use secure, password-less authentication to protect your privacy. We'll send you a welcome email and remember you on this device.`
              : `We use secure, password-less authentication to protect your privacy. We'll remember you on this device.`
            }
            <br />
            <button
              type="button"
              className="privacy-link"
              onClick={() => setShowPrivacyPolicy(true)}
            >
              Privacy Policy
            </button>
            <span className="link-separator"> | </span>
            <button
              type="button"
              className="privacy-link"
              onClick={() => setShowAboutUs(true)}
            >
              About Us
            </button>
          </p>
        </form>
      </div>

      {showPrivacyPolicy && (
        <PrivacyPolicy onClose={() => setShowPrivacyPolicy(false)} />
      )}
      {showAboutUs && (
        <AboutUs onClose={() => setShowAboutUs(false)} />
      )}
    </div>
  );
}
