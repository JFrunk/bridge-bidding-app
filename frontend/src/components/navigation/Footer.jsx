/**
 * Footer - App footer with trust links
 */

import React from 'react';
import './Footer.css';

export function Footer({ onPrivacyClick, onAboutClick }) {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-links">
          <button onClick={onPrivacyClick} className="footer-link">
            Privacy Policy
          </button>
          <span className="footer-divider">|</span>
          <button onClick={onAboutClick} className="footer-link">
            About
          </button>
        </div>
        <div className="footer-copyright">
          &copy; {currentYear} My Bridge Buddy
        </div>
      </div>
    </footer>
  );
}

export default Footer;
