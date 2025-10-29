import React from 'react';
import * as deck from '@letele/playing-cards';

/**
 * LibraryCard - Wrapper for @letele/playing-cards library
 *
 * Maps our card format {rank, suit} to the library's naming convention
 * and applies custom styling
 */
export function LibraryCard({ rank, suit, onClick, disabled = false, className, style }) {
  // Map suits to library format
  const suitMap = {
    '♠': 'S',  // Spades
    '♥': 'H',  // Hearts
    '♦': 'D',  // Diamonds
    '♣': 'C'   // Clubs
  };

  // Map ranks to library format
  // Library uses: Ca, C2-C9, C10, Cj, Cq, Ck (lowercase for face cards, "10" for ten)
  const rankMap = {
    'A': 'a',   // Ca (lowercase)
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    'T': '10',  // C10 (the string "10")
    'J': 'j',   // Cj (lowercase)
    'Q': 'q',   // Cq (lowercase)
    'K': 'k'    // Ck (lowercase)
  };

  // Get the library component name (e.g., 'Sa' for Ace of Spades)
  const librarySuit = suitMap[suit];
  const libraryRank = rankMap[rank];
  const cardName = `${librarySuit}${libraryRank}`;

  // Get the card component from the deck
  const CardComponent = deck[cardName];

  if (!CardComponent) {
    console.error(`❌ Card not found: ${cardName} (rank: ${rank}, suit: ${suit})`);
    console.error('Available cards in deck:', Object.keys(deck).slice(0, 10).join(', '), '...');
    return null;
  }

  console.log(`✅ Rendering card: ${cardName}`);

  // Determine if card is clickable
  const isClickable = onClick && !disabled;

  // Combine inline styles
  const combinedStyle = {
    height: '100%',
    width: '100%',
    cursor: isClickable ? 'pointer' : 'default',
    transition: 'transform 0.2s',
    ...style
  };

  return (
    <div
      className={`library-card ${className || ''}`}
      style={{
        width: '70px',
        height: '100px',
        position: 'relative',
        ...style
      }}
      onClick={!disabled ? onClick : undefined}
      onMouseEnter={(e) => {
        if (isClickable) {
          e.currentTarget.querySelector('svg').style.transform = 'translateY(-4px)';
        }
      }}
      onMouseLeave={(e) => {
        if (isClickable) {
          e.currentTarget.querySelector('svg').style.transform = 'translateY(0)';
        }
      }}
    >
      <CardComponent style={combinedStyle} />
    </div>
  );
}

LibraryCard.displayName = 'LibraryCard';
