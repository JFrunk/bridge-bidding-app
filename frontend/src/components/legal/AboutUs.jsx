import React from 'react';
import './AboutUs.css';

export function AboutUs({ onClose }) {
  return (
    <div className="about-us-overlay" onClick={(e) => {
      if (e.target.className === 'about-us-overlay') onClose?.();
    }}>
      <div className="about-us-modal">
        <button className="close-button" onClick={onClose} aria-label="Close">
          ×
        </button>

        <h1>About Us: My Bridge Buddy</h1>

        <section>
          <h2>Our Mission</h2>
          <p>
            At My Bridge Buddy, we believe that the game of Contract Bridge should be accessible,
            engaging, and structured for modern learners. Our mission is to provide a secure,
            AI-powered sandbox where students can master the Standard American Yellow Card (SAYC)
            system and practice partnership synchronization without the pressure of a competitive lobby.
          </p>
        </section>

        <section>
          <h2>Why We Built This</h2>
          <p>
            Bridge is often called the "King of Card Games," but its steep learning curve can be
            a barrier. We developed this platform to bridge that gap by offering:
          </p>
          <ul className="feature-list">
            <li>
              <strong>Intelligent Coaching:</strong> Real-time bidding analysis and high-card point
              (HCP) verification to help you develop a "feel" for the deck.
            </li>
            <li>
              <strong>Team Practice Rooms:</strong> Private, code-protected environments where
              partners can bid and play against advanced AI to refine their systemic agreements.
            </li>
            <li>
              <strong>Data Integrity:</strong> A commitment to privacy, including a secure
              password-less architecture that puts user safety first.
            </li>
          </ul>
        </section>

        <section>
          <h2>How It Works</h2>
          <p>
            My Bridge Buddy utilizes a "Physics of the Deck" approach to coaching. Our algorithms
            ensure that every lesson is grounded in mathematical reality—verifying that high-card
            points and suit lengths always align with the 40-point deck and the bidding logic of
            your opponents.
          </p>
        </section>

        <section>
          <h2>Our Commitment to Security</h2>
          <p>
            We are a strictly pedagogical platform. We do not process financial transactions,
            collect passwords, or share user data with third-party advertisers. Our goal is to
            foster a safe community for learners to focus on what matters most: the cards.
          </p>
        </section>

        <section>
          <h2>Contact</h2>
          <p>
            Questions or feedback? Reach us at{' '}
            <a href="mailto:support@mybridgebuddy.com">support@mybridgebuddy.com</a>
          </p>
        </section>
      </div>
    </div>
  );
}
