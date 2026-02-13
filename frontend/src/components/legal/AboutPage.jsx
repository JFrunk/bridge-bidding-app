/**
 * AboutPage - About Modal
 */

import React from 'react';
import './LegalPages.css';

export function AboutPage({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="legal-modal-overlay" onClick={onClose}>
      <div className="legal-modal" onClick={e => e.stopPropagation()}>
        <button className="legal-close-button" onClick={onClose} aria-label="Close">
          &times;
        </button>

        <h1>About My Bridge Buddy</h1>

        <section>
          <h2>Our Mission</h2>
          <p>
            My Bridge Buddy is designed to help bridge players of all levels improve
            their bidding and play through interactive practice and personalized feedback.
          </p>
        </section>

        <section>
          <h2>Features</h2>
          <ul>
            <li><strong>AI-Powered Practice:</strong> Play against intelligent AI opponents</li>
            <li><strong>Convention Training:</strong> Learn and practice standard conventions</li>
            <li><strong>Double Dummy Analysis:</strong> Get optimal play feedback</li>
            <li><strong>Progress Tracking:</strong> Monitor your improvement over time</li>
            <li><strong>Team Mode:</strong> Play with a partner against AI opponents</li>
          </ul>
        </section>

        <section>
          <h2>Technology</h2>
          <p>
            Built with modern web technologies and powered by sophisticated bridge
            analysis engines including Double Dummy Solver integration.
          </p>
        </section>

        <section>
          <h2>Version</h2>
          <p>
            My Bridge Buddy v1.0
          </p>
        </section>
      </div>
    </div>
  );
}

export default AboutPage;
