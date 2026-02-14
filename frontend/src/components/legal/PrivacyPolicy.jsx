import React from 'react';
import './PrivacyPolicy.css';

export function PrivacyPolicy({ onClose }) {
  return (
    <div className="privacy-policy-overlay" onClick={(e) => {
      if (e.target.className === 'privacy-policy-overlay') onClose?.();
    }}>
      <div className="privacy-policy-modal">
        <button className="close-button" onClick={onClose} aria-label="Close">
          ×
        </button>

        <h1>Privacy Policy: My Bridge Buddy</h1>
        <p className="last-updated">Last Updated: February 12, 2026</p>

        <section>
          <h2>1. Purpose of Data Collection</h2>
          <p>
            My Bridge Buddy is an educational platform designed for the practice of Contract Bridge.
            We collect minimal personal information solely to facilitate account authentication and
            to save your progress within our learning modules.
          </p>
        </section>

        <section>
          <h2>2. Information We Collect</h2>

          <h3>Authentication & Profile Data</h3>
          <p>
            We collect your email address solely for account identification and secure login purposes.
            <strong> At this time, we do not collect or store user passwords.</strong>
          </p>

          <h3>Gameplay & Progress Metrics</h3>
          <p>
            We store your bidding history, hand results, and coaching performance data to provide
            personalized feedback and track your improvement over time.
          </p>

          <h3>Technical Identifiers</h3>
          <p>
            We may collect basic technical data (such as IP addresses) strictly for security monitoring
            and to maintain the integrity of our private Team Practice rooms.
          </p>
        </section>

        <section>
          <h2>3. No Financial Transactions</h2>
          <p>
            My Bridge Buddy is strictly a pedagogical tool. We do not process payments, collect
            credit card information, or facilitate any cash transactions on this platform.
          </p>
        </section>

        <section>
          <h2>4. Data Sharing and Third Parties</h2>

          <h3>No Third-Party Monetization</h3>
          <p>
            We do not sell, rent, trade, or share any of your personal data or gameplay history
            with third parties for marketing or advertising purposes.
          </p>

          <h3>Partnership Play</h3>
          <p>
            In "Team Practice" mode, your username and active bidding status are visible only to
            the specific partner you have invited to your session via a private room code.
          </p>
        </section>

        <section>
          <h2>5. Security Protocols</h2>
          <p>
            We utilize industry-standard SSL/TLS encryption to protect all data in transit.
            Our environment is designed to provide a secure and private space for bridge students
            and teams to practice their skills.
          </p>
        </section>

        <section>
          <h2>6. Contact</h2>
          <p>
            For questions about this privacy policy or your data, contact us at{' '}
            <a href="mailto:support@mybridgebuddy.com">support@mybridgebuddy.com</a>
          </p>
        </section>
      </div>
    </div>
  );
}
