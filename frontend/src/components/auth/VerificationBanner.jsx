/**
 * VerificationBanner — Persistent banner for unverified email users.
 *
 * PRD §3.4: "Persistent but dismissable banner that reappears on each session."
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './LoginPage.css';

export function VerificationBanner() {
  const { user, resendVerification } = useAuth();
  const [dismissed, setDismissed] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  // Only show for V2 users who haven't verified email
  if (!user || user.isGuest || user.emailVerified !== false || !user.authVersion) return null;
  if (dismissed) return null;

  const handleResend = async () => {
    setSending(true);
    await resendVerification();
    setSent(true);
    setSending(false);
  };

  return (
    <div className="verification-banner">
      <span>
        {sent
          ? 'Verification email sent — check your inbox.'
          : 'Verify your email to secure your account.'}
      </span>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        {!sent && (
          <button onClick={handleResend} disabled={sending}>
            {sending ? 'Sending...' : 'Resend'}
          </button>
        )}
        <button className="banner-dismiss" onClick={() => setDismissed(true)} title="Dismiss">
          &times;
        </button>
      </div>
    </div>
  );
}
