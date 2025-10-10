import React, { useState } from 'react';
import './Login.css';

function Login({ onLogin }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // Simple password check - in production, this should be an environment variable
  const VALID_PASSWORD = process.env.REACT_APP_ACCESS_PASSWORD || 'bridge2024';

  const handleSubmit = (e) => {
    e.preventDefault();

    if (password === VALID_PASSWORD) {
      localStorage.setItem('bridgeAuth', 'true');
      onLogin();
    } else {
      setError('Incorrect password. Please try again.');
      setPassword('');
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>🃏 Bridge Bidding Trainer</h1>
        <p className="login-subtitle">Enter password to continue</p>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              autoFocus
              className="password-input"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="login-button">
            Sign In
          </button>
        </form>

        <div className="login-footer">
          <p>Limited Access • SAYC Training System</p>
        </div>
      </div>
    </div>
  );
}

export default Login;
