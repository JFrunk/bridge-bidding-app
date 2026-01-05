/**
 * ChartHelp - Collapsible help section for charts and analysis views
 *
 * Consumer-friendly explanations using encouraging "coach" tone.
 * Designed for progressive disclosure - collapsed by default.
 */

import React, { useState } from 'react';
import './ChartHelp.css';

/**
 * ChartHelp Component
 *
 * @param {Object} props
 * @param {string} props.chartType - Which chart this help is for
 * @param {string} props.variant - 'inline' (below chart) or 'icon' (? trigger)
 * @param {boolean} props.defaultOpen - Start expanded (default false)
 */
const ChartHelp = ({ chartType, variant = 'inline', defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const helpContent = CHART_HELP_CONTENT[chartType];

  if (!helpContent) {
    console.warn(`ChartHelp: Unknown chartType "${chartType}"`);
    return null;
  }

  const toggleOpen = () => setIsOpen(!isOpen);

  if (variant === 'icon') {
    return (
      <div className="chart-help-icon-container">
        <button
          className="chart-help-icon"
          onClick={toggleOpen}
          aria-label="How does this work?"
          aria-expanded={isOpen}
        >
          ?
        </button>
        {isOpen && (
          <div className="chart-help-popup">
            <div className="chart-help-popup-header">
              <span className="chart-help-popup-title">{helpContent.title}</span>
              <button
                className="chart-help-popup-close"
                onClick={toggleOpen}
                aria-label="Close help"
              >
                ×
              </button>
            </div>
            <HelpBody content={helpContent} />
          </div>
        )}
      </div>
    );
  }

  // Default: inline collapsible
  return (
    <div className={`chart-help-inline ${isOpen ? 'open' : ''}`}>
      <button
        className="chart-help-trigger"
        onClick={toggleOpen}
        aria-expanded={isOpen}
      >
        <span className="chart-help-trigger-icon">{isOpen ? '▼' : '▶'}</span>
        <span className="chart-help-trigger-text">
          {isOpen ? 'Hide guide' : 'How does this work?'}
        </span>
      </button>
      {isOpen && (
        <div className="chart-help-content">
          <div className="chart-help-title">{helpContent.title}</div>
          <HelpBody content={helpContent} />
        </div>
      )}
    </div>
  );
};

/**
 * HelpBody - Renders the structured help content
 */
const HelpBody = ({ content }) => {
  return (
    <div className="chart-help-body">
      {content.intro && (
        <p className="chart-help-intro">{content.intro}</p>
      )}

      {content.sections && content.sections.map((section, idx) => (
        <div key={idx} className="chart-help-section">
          {section.heading && (
            <div className="chart-help-section-heading">{section.heading}</div>
          )}
          {section.items && (
            <ul className="chart-help-list">
              {section.items.map((item, itemIdx) => (
                <li key={itemIdx} className="chart-help-list-item">
                  {item.icon && <span className="chart-help-item-icon">{item.icon}</span>}
                  {item.label && <strong className="chart-help-item-label">{item.label}</strong>}
                  {item.text && <span className="chart-help-item-text">{item.text}</span>}
                </li>
              ))}
            </ul>
          )}
          {section.text && (
            <p className="chart-help-section-text">{section.text}</p>
          )}
        </div>
      ))}

      {content.proTip && (
        <div className="chart-help-pro-tip">
          <span className="pro-tip-label">Pro Tip:</span>
          <span className="pro-tip-text">{content.proTip}</span>
        </div>
      )}
    </div>
  );
};

/**
 * Help content for each chart type
 * Using consumer-friendly, encouraging "coach" tone
 */
const CHART_HELP_CONTENT = {
  'trick-timeline': {
    title: 'See How the Hand Unfolded',
    intro: 'This chart shows a "live tracker" of your trick potential. It compares your play to a perfect computer model to help you find the turning points in every hand.',
    sections: [
      {
        heading: 'Reading the line:',
        items: [
          { icon: '—', label: 'Flat line', text: "You're playing perfectly! Holding onto every trick possible." },
          { icon: '↘', label: 'Downward step', text: 'A moment where a trick got away. These are your best "Aha!" moments for learning.' },
          { icon: '↗', label: 'Upward step', text: 'Great job! The defense made a mistake, and you pounced on it to gain an extra trick.' }
        ]
      },
      {
        heading: 'The markers:',
        items: [
          { icon: '🔴', label: 'Red dots', text: 'Where you might have missed a trick' },
          { icon: '🟢', label: 'Green dots', text: 'Where you gained one back from the opponents' }
        ]
      }
    ],
    proTip: 'Click any point on the line to jump straight to that card. Focus on the red dots—they are the keys to leveling up your game!'
  },

  'bidding-review': {
    title: 'Your Bidding Coach',
    intro: "Step through the auction to see how you and your partner reached your contract. It's like having a pro sitting next to you, offering a second opinion on your choices.",
    sections: [
      {
        heading: 'How to move:',
        text: 'Use your arrow keys or the buttons to walk through the auction bid-by-bid.'
      },
      {
        heading: 'The feedback (we focus on your decisions as South):',
        items: [
          { icon: '✓', label: 'Great', text: 'You found the best bid!' },
          { icon: '○', label: 'Good', text: 'A solid choice that works well.' },
          { icon: '!', label: 'Try Again', text: 'There was a more descriptive or safer option available.' }
        ]
      },
      {
        heading: 'Learn the "Why":',
        text: "Check the explanation panel to see the logic behind the suggested bids. It's the fastest way to get in sync with your partner."
      }
    ]
  },

  'play-review': {
    title: 'Follow the Action',
    intro: 'Watch the cards hit the table one by one. This view helps you visualize the "flow" of the game and spot winning tactics.',
    sections: [
      {
        heading: 'Navigation:',
        text: "Use the arrow keys to see the cards played in order. Position 0 shows everyone's \"starting hand\" before the first lead."
      },
      {
        heading: 'The center circle:',
        text: 'Shows the current trick. The card with the dot (●) was the lead.'
      },
      {
        heading: 'Declarer feedback:',
        text: 'If you were playing the hand, look for the faded "Ghost Card" in your hand layout—that\'s the play the computer suggests for the best result!'
      },
      {
        heading: 'Sync with the chart:',
        text: 'Use this alongside the Trick Timeline. When you see a drop in the line, check this view to see exactly which card was played.'
      }
    ]
  },

  'possible-tricks': {
    title: 'What Was Possible?',
    intro: 'This table shows the maximum number of tricks available for each side in every suit. It\'s the "solved" version of the hand, assuming everyone plays perfectly.',
    sections: [
      {
        heading: 'NS and EW:',
        text: 'Look at the NS row to see how many tricks you and your partner could make. Look at EW to see what the opponents could do.'
      },
      {
        heading: 'The magic number:',
        text: 'Each column adds up to 13. If you can make 10 tricks in Spades, the opponents can only make 3!'
      },
      {
        heading: 'The colorful rings highlight big opportunities:',
        items: [
          { icon: '🟢', label: 'Green ring', text: 'A "Game" was possible (the big point bonus!)' },
          { icon: '🟠', label: 'Orange ring', text: 'A "Small Slam" was there (almost all the tricks!)' },
          { icon: '🔴', label: 'Red ring', text: 'A "Grand Slam" was available (all 13 tricks!)' }
        ]
      }
    ],
    proTip: 'If you bid a Game but the table shows only 8 tricks were possible, you were just a bit unlucky with the cards!'
  },

  'success-map': {
    title: 'Your Big Picture',
    intro: "This map looks at your recent hands to show you where you're shining and where you might want to focus your next practice session.",
    sections: [
      {
        heading: 'The four zones:',
        items: [
          { icon: '↗', label: 'Top-Right (Green)', text: 'The "Sweet Spot." Great bidding and great play!' },
          { icon: '↖', label: 'Top-Left (Yellow)', text: "You're a Bidding Star! Now, let's look at the card play to find those extra tricks." },
          { icon: '↘', label: 'Bottom-Right (Yellow)', text: "You're a Play Pro! A little more bidding practice will have you in the Green Zone in no time." },
          { icon: '↙', label: 'Bottom-Left (Red)', text: "These were just tough boards. They happen to everyone—don't sweat them!" }
        ]
      },
      {
        heading: 'The shapes:',
        items: [
          { icon: '●', label: 'Solid', text: 'Hands you declared' },
          { icon: '○', label: 'Outline', text: 'Hands where you were defending or helping your partner' }
        ]
      }
    ],
    proTip: "Don't worry about any single dot. Look for where your dots clump together. That's your \"Bridge Personality!\""
  }
};

export default ChartHelp;
export { CHART_HELP_CONTENT };
