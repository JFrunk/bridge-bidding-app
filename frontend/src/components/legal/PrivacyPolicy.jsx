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

        <h1>Privacy Policy: MyBridgeBuddy</h1>
        <p className="last-updated">Last Updated: March 20, 2026</p>

        <section>
          <h2>1. Purpose of Data Collection</h2>
          <p>
            MyBridgeBuddy is an educational platform designed for the practice of Contract Bridge.
            We collect minimal personal information solely to facilitate account authentication,
            secure access to your profile, and save your progress within our learning modules.
          </p>
        </section>

        <section>
          <h2>2. Information We Collect</h2>

          <h3>Authentication &amp; Profile Data</h3>
          <p>
            <strong>OAuth Users:</strong> If you sign in via Google, we collect your email address
            and basic profile identifier to establish your account.
          </p>
          <p>
            <strong>Direct Email Users:</strong> If you choose to create a local account, we collect
            your email address and a hashed version of your password.
          </p>
          <p>
            <strong>Note on Security:</strong> We utilize industry-standard cryptographic hashing.
            Your "plain text" password is never stored in our database or accessible to our staff.
          </p>

          <h3>Gameplay &amp; Progress Metrics</h3>
          <p>
            We store your bidding history, hand results, and coaching performance data to provide
            personalized feedback and track your improvement over time in Zone 3 (The Coach).
          </p>

          <h3>Technical Identifiers</h3>
          <p>
            We may collect basic technical data (such as IP addresses and browser headers) strictly
            for security monitoring, session management, and to maintain the integrity of our
            private Team Practice rooms.
          </p>
        </section>

        <section>
          <h2>3. No Financial Transactions</h2>
          <p>
            MyBridgeBuddy remains strictly a pedagogical tool. We do not process payments, collect
            credit card information, or facilitate any cash transactions on this platform.
          </p>
        </section>

        <section>
          <h2>4. Data Sharing and Third Parties</h2>
          <p>
            <strong>No Third-Party Monetization:</strong> We do not sell, rent, trade, or share any
            of your personal data or gameplay history with third parties for marketing or advertising
            purposes.
          </p>
          <p>
            <strong>Partnership Play:</strong> In "Team Practice" mode, your username and active
            bidding status are visible only to the specific partner you have invited to your session
            via a private room code.
          </p>
        </section>

        <section>
          <h2>5. Security Protocols</h2>
          <p>
            We utilize SSL/TLS encryption for all data in transit. For users logging in with a
            password, we employ salted hashing to protect credential integrity. Our environment is
            designed to provide a secure and private space for bridge students and teams to practice.
          </p>
        </section>

        <section>
          <h2>6. Google API Disclosure</h2>
          <p>
            MyBridgeBuddy's use and transfer to any other app of information received from Google
            APIs will adhere to the{' '}
            <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer">
              Google API Services User Data Policy
            </a>, including the Limited Use requirements.
          </p>
        </section>

        <section>
          <h2>7. Contact</h2>
          <p>
            For questions about this privacy policy or your data, contact us at{' '}
            <a href="mailto:mybridgebuddy@gmail.com">mybridgebuddy@gmail.com</a>
          </p>
        </section>
      </div>
    </div>
  );
}
