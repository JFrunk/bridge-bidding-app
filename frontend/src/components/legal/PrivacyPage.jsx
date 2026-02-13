/**
 * PrivacyPage - Privacy Policy Modal
 */

import React from 'react';
import './LegalPages.css';

export function PrivacyPage({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="legal-modal-overlay" onClick={onClose}>
      <div className="legal-modal" onClick={e => e.stopPropagation()}>
        <button className="legal-close-button" onClick={onClose} aria-label="Close">
          &times;
        </button>

        <h1>Privacy Policy</h1>
        <p className="legal-updated">Last updated: February 2026</p>

        <section>
          <h2>No Password Required</h2>
          <p>
            My Bridge Buddy uses passwordless authentication. We only store your email
            address for account identification. No passwords are ever stored or transmitted.
          </p>
        </section>

        <section>
          <h2>Data We Collect</h2>
          <ul>
            <li><strong>Email address:</strong> Used for login and account identification</li>
            <li><strong>Game history:</strong> Hands played, bids made, and performance statistics</li>
            <li><strong>Learning progress:</strong> Convention mastery and skill development tracking</li>
          </ul>
        </section>

        <section>
          <h2>Strictly Pedagogical</h2>
          <p>
            All data collected is used exclusively for educational purposes:
          </p>
          <ul>
            <li>Providing personalized learning recommendations</li>
            <li>Tracking your improvement over time</li>
            <li>Analyzing bidding patterns to offer targeted feedback</li>
          </ul>
        </section>

        <section>
          <h2>Data Security</h2>
          <p>
            Your data is stored securely and is never sold or shared with third parties.
            You can request deletion of your account and all associated data at any time.
          </p>
        </section>

        <section>
          <h2>Contact</h2>
          <p>
            For questions about this privacy policy or your data, contact us at{' '}
            <a href="mailto:privacy@mybridgebuddy.com">privacy@mybridgebuddy.com</a>
          </p>
        </section>
      </div>
    </div>
  );
}

export default PrivacyPage;
