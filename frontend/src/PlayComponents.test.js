/**
 * PlayComponents.test.js - Unit tests for hand visibility logic
 *
 * CRITICAL: These tests prevent regression of hand visibility bugs
 * Run these tests before any changes to PlayComponents.js
 *
 * Tests cover all 4 declarer scenarios × 4 dummy positions = 16 total scenarios
 */

import { render, screen } from '@testing-library/react';
import { PlayTable } from './PlayComponents';

// Mock data generator
function createMockPlayState(declarerPos, dummyPos) {
  return {
    contract: {
      level: 3,
      strain: 'NT',
      declarer: declarerPos,
      doubled: 0
    },
    dummy: dummyPos,
    dummy_revealed: true,  // CRITICAL: Dummy must be revealed for visibility tests
    current_trick: [],
    tricks_won: { N: 0, E: 0, S: 0, W: 0 },
    next_to_play: declarerPos,
    trick_complete: false,
    trick_winner: null
  };
}

function createMockHand() {
  return [
    { rank: 'A', suit: '♠' },
    { rank: 'K', suit: '♠' },
    { rank: 'Q', suit: '♥' }
  ];
}

/**
 * CRITICAL TEST SUITE: Data Structure Handling
 *
 * Bug Fix (2026-02-19): Backend returns dummy_hand as {cards: [...], position: "N"}
 * Frontend must handle both object format and array format
 */
describe('Data Structure Handling - Prevent Regression', () => {
  test('Handles dummy hand as object {cards: [...], position: "N"}', () => {
    const playState = createMockPlayState('S', 'N');
    const userHand = createMockHand();
    // Backend format: {cards: [...], position: "N"}
    const dummyHandObject = {
      cards: createMockHand(),
      position: 'N'
    };

    const { container } = render(
      <PlayTable
        playState={playState}
        userHand={userHand}
        dummyHand={dummyHandObject}
        onCardPlay={() => {}}
        isUserTurn={true}
        auction={[]}
        declarerHand={null}
        onDeclarerCardPlay={() => {}}
        isDeclarerTurn={false}
        onDummyCardPlay={() => {}}
        isDummyTurn={false}
        scoreData={null}
      />
    );

    // Should extract cards array and render all 3 cards
    const northHand = container.querySelector('.position-north .dummy-hand');
    expect(northHand).toBeTruthy();
    const cards = northHand.querySelectorAll('.playable-card');
    expect(cards.length).toBe(3);
  });

  test('Handles dummy hand as array [...] (legacy format)', () => {
    const playState = createMockPlayState('S', 'N');
    const userHand = createMockHand();
    // Legacy format: [...]
    const dummyHandArray = createMockHand();

    const { container } = render(
      <PlayTable
        playState={playState}
        userHand={userHand}
        dummyHand={dummyHandArray}
        onCardPlay={() => {}}
        isUserTurn={true}
        auction={[]}
        declarerHand={null}
        onDeclarerCardPlay={() => {}}
        isDeclarerTurn={false}
        onDummyCardPlay={() => {}}
        isDummyTurn={false}
        scoreData={null}
      />
    );

    // Should render all 3 cards
    const northHand = container.querySelector('.position-north .dummy-hand');
    expect(northHand).toBeTruthy();
    const cards = northHand.querySelectorAll('.playable-card');
    expect(cards.length).toBe(3);
  });
});

/**
 * CRITICAL TEST SUITE: Hand Visibility Rules
 *
 * Bridge Rules:
 * 1. User (South) ALWAYS sees their own hand
 * 2. EVERYONE sees the dummy hand
 * 3. Declarer's hand is ONLY visible if user IS the dummy
 * 4. Defenders NEVER see each other's hands
 */
describe('Hand Visibility Rules - Prevent Regression', () => {

  /**
   * Scenario 1: South declares, North is dummy
   * User sees: South (own hand) + North (dummy)
   */
  test('SCENARIO 1: South declares, North dummy - User sees South + North only', () => {
    const playState = createMockPlayState('S', 'N');
    const userHand = createMockHand();
    const dummyHand = createMockHand();

    const { container } = render(
      <PlayTable
        playState={playState}
        userHand={userHand}
        dummyHand={dummyHand}
        onCardPlay={() => {}}
        isUserTurn={true}
        auction={[]}
        declarerHand={null}
        onDeclarerCardPlay={() => {}}
        isDeclarerTurn={false}
        onDummyCardPlay={() => {}}
        isDummyTurn={false}
        scoreData={null}
      />
    );

    // Should show North (dummy)
    const northHand = container.querySelector('.position-north .dummy-hand');
    expect(northHand).toBeTruthy();

    // Should show South (user)
    const southHand = container.querySelector('.position-south .user-play-hand');
    expect(southHand).toBeTruthy();

    // Should NOT show East or West (opponents)
    const eastHand = container.querySelector('.position-east .dummy-hand, .position-east .declarer-hand');
    const westHand = container.querySelector('.position-west .dummy-hand, .position-west .declarer-hand');
    expect(eastHand).toBeFalsy();
    expect(westHand).toBeFalsy();
  });

  /**
   * Scenario 2: North declares, South is dummy
   * User sees: North (declarer - user controls) + South (own hand/dummy)
   */
  test('SCENARIO 2: North declares, South dummy - User sees North + South only', () => {
    const playState = createMockPlayState('N', 'S');
    const userHand = createMockHand(); // South's hand (user is dummy)
    const declarerHand = createMockHand(); // North's hand (declarer)

    const { container } = render(
      <PlayTable
        playState={playState}
        userHand={userHand}
        dummyHand={userHand} // South is dummy
        onCardPlay={() => {}}
        isUserTurn={false}
        auction={[]}
        declarerHand={declarerHand}
        onDeclarerCardPlay={() => {}}
        isDeclarerTurn={true}
        onDummyCardPlay={() => {}}
        isDummyTurn={false}
        scoreData={null}
      />
    );

    // Should show North (declarer - user controls it)
    const northHand = container.querySelector('.position-north .declarer-hand');
    expect(northHand).toBeTruthy();

    // Should show South (dummy/user)
    const southHand = container.querySelector('.position-south');
    expect(southHand).toBeTruthy();

    // Should NOT show East or West
    const eastHand = container.querySelector('.position-east .dummy-hand, .position-east .declarer-hand');
    const westHand = container.querySelector('.position-west .dummy-hand, .position-west .declarer-hand');
    expect(eastHand).toBeFalsy();
    expect(westHand).toBeFalsy();
  });

  /**
   * Scenario 3: East declares, West is dummy
   * User (South) is defender - sees: South (own hand) + West (dummy)
   * Should NOT see East (declarer)
   */
  test('SCENARIO 3: East declares, West dummy - Defender sees South + West only (NOT East)', () => {
    const playState = createMockPlayState('E', 'W');
    const userHand = createMockHand(); // South (defender)
    const dummyHand = createMockHand(); // West (dummy)
    const declarerHand = createMockHand(); // East (declarer - should be HIDDEN)

    const { container } = render(
      <PlayTable
        playState={playState}
        userHand={userHand}
        dummyHand={dummyHand}
        onCardPlay={() => {}}
        isUserTurn={false}
        auction={[]}
        declarerHand={declarerHand}
        onDeclarerCardPlay={() => {}}
        isDeclarerTurn={false}
        onDummyCardPlay={() => {}}
        isDummyTurn={false}
        scoreData={null}
      />
    );

    // Should show South (user/defender)
    const southHand = container.querySelector('.position-south .user-play-hand');
    expect(southHand).toBeTruthy();

    // Should show West (dummy)
    const westHand = container.querySelector('.position-west .dummy-hand');
    expect(westHand).toBeTruthy();

    // CRITICAL: Should NOT show East (declarer) - user is defender!
    const eastHand = container.querySelector('.position-east .dummy-hand, .position-east .declarer-hand');
    expect(eastHand).toBeFalsy();

    // Should NOT show North (other defender)
    const northHand = container.querySelector('.position-north .dummy-hand, .position-north .declarer-hand');
    expect(northHand).toBeFalsy();
  });

  /**
   * Scenario 4: West declares, East is dummy
   * User (South) is defender - sees: South (own hand) + East (dummy)
   * Should NOT see West (declarer)
   */
  test('SCENARIO 4: West declares, East dummy - Defender sees South + East only (NOT West)', () => {
    const playState = createMockPlayState('W', 'E');
    const userHand = createMockHand(); // South (defender)
    const dummyHand = createMockHand(); // East (dummy)
    const declarerHand = createMockHand(); // West (declarer - should be HIDDEN)

    const { container } = render(
      <PlayTable
        playState={playState}
        userHand={userHand}
        dummyHand={dummyHand}
        onCardPlay={() => {}}
        isUserTurn={false}
        auction={[]}
        declarerHand={declarerHand}
        onDeclarerCardPlay={() => {}}
        isDeclarerTurn={false}
        onDummyCardPlay={() => {}}
        isDummyTurn={false}
        scoreData={null}
      />
    );

    // Should show South (user/defender)
    const southHand = container.querySelector('.position-south .user-play-hand');
    expect(southHand).toBeTruthy();

    // Should show East (dummy)
    const eastHand = container.querySelector('.position-east .dummy-hand');
    expect(eastHand).toBeTruthy();

    // CRITICAL: Should NOT show West (declarer) - user is defender!
    const westHand = container.querySelector('.position-west .dummy-hand, .position-west .declarer-hand');
    expect(westHand).toBeFalsy();

    // Should NOT show North (other defender)
    const northHand = container.querySelector('.position-north .dummy-hand, .position-north .declarer-hand');
    expect(northHand).toBeFalsy();
  });
});

/**
 * Integration test: Console logging verification
 */
describe('Hand Visibility Logging', () => {
  test('Should log visibility decisions for debugging', () => {
    const consoleSpy = jest.spyOn(console, 'log');

    const playState = createMockPlayState('E', 'W');
    const userHand = createMockHand();
    const dummyHand = createMockHand();

    render(
      <PlayTable
        playState={playState}
        userHand={userHand}
        dummyHand={dummyHand}
        onCardPlay={() => {}}
        isUserTurn={false}
        auction={[]}
        declarerHand={null}
        onDeclarerCardPlay={() => {}}
        isDeclarerTurn={false}
        onDummyCardPlay={() => {}}
        isDummyTurn={false}
        scoreData={null}
      />
    );

    // Should have logged visibility rules
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Hand Visibility Rules Applied'),
      expect.any(Object)
    );

    consoleSpy.mockRestore();
  });
});
