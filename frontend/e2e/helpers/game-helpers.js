// Game action helper functions for E2E tests

/**
 * Deal a new hand
 *
 * IMPORTANT: After dealing, the dealer (North/East/South/West) bids first.
 * If South is NOT the dealer, AI players will bid first and we need to
 * wait for the auction to come around to South's turn.
 */
export async function dealNewHand(page) {
  await page.click('[data-testid="deal-button"]');

  // Wait for bidding box to be visible
  await page.waitForSelector('[data-testid="bidding-box"]', { state: 'visible' });

  // Wait for the hand to be dealt - check that cards are visible
  await page.waitForSelector('.hand-display', { state: 'visible', timeout: 5000 });

  // Give the app a moment to set up dealer, currentPlayer, etc.
  await page.waitForTimeout(1000);

  // Check who the dealer is by looking for the dealer indicator (🔵)
  // The dealer indicator appears in the bidding table header
  const southIsDealer = await page.locator('[data-testid="bidding-header-south"]')
    .filter({ hasText: '🔵' })
    .count() > 0;

  if (!southIsDealer) {
    // AI players bid first - wait for auction to come around to South
    // Use waitForAIBid() which handles both "auction continues" and "auction complete"
    console.log('⏳ Waiting for AI players to bid (South is not dealer)...');

    // Wait for first AI bid to complete
    await waitForAIBid(page);

    // Check if it's South's turn now or if we need to wait more
    // Keep waiting until either:
    // 1. It's South's turn (Pass button enabled)
    // 2. Auction is complete (play button appears)
    let maxAttempts = 4; // Maximum 4 players can bid before South's turn
    let attempts = 0;

    while (attempts < maxAttempts) {
      const passButtonEnabled = await page.locator('[data-testid="bid-call-Pass"]:not([disabled])')
        .count() > 0;

      const playButtonVisible = await page.locator('[data-testid="play-button"], text=Play This Hand')
        .count() > 0;

      if (passButtonEnabled || playButtonVisible) {
        // Either it's South's turn or auction is complete
        break;
      }

      // Still waiting for South's turn - wait for next AI bid
      console.log(`⏳ Still waiting for South's turn (attempt ${attempts + 1}/${maxAttempts})...`);
      await waitForAIBid(page);
      attempts++;
    }
  } else {
    // South is dealer - just wait for bidding box to enable
    console.log('✅ South is dealer - waiting for bidding box to enable...');
    await page.waitForSelector('[data-testid="bid-call-Pass"]:not([disabled])', {
      state: 'visible',
      timeout: 15000
    });
  }
}

/**
 * Make a bid (level + suit)
 * @param {number} level - Bid level (1-7)
 * @param {string} suit - Suit symbol (♣, ♦, ♥, ♠, NT)
 */
export async function makeBid(page, level, suit) {
  // Click level
  await page.click(`[data-testid="bid-level-${level}"]`);

  // Click suit
  await page.click(`[data-testid="bid-suit-${suit}"]`);

  // Wait a moment for bid to be processed
  await page.waitForTimeout(500);
}

/**
 * Make a call (Pass, X, XX)
 * @param {string} call - Call to make (Pass, X, XX)
 */
export async function makeCall(page, call) {
  await page.click(`[data-testid="bid-call-${call}"]`);

  // Wait a moment for call to be processed
  await page.waitForTimeout(500);
}

/**
 * Pass until bidding is complete (3 consecutive passes)
 */
export async function passUntilComplete(page) {
  let passCount = 0;

  while (passCount < 3) {
    // Check if bidding box is still enabled
    const isDisabled = await page.locator('[data-testid="bid-call-Pass"]').isDisabled();

    if (isDisabled) {
      // Bidding is complete
      break;
    }

    // Make a pass
    await makeCall(page, 'Pass');

    // Wait for AI to bid
    await page.waitForTimeout(2000);

    passCount++;
  }
}

/**
 * Get current auction from bidding table
 */
export async function getAuction(page) {
  const auctionText = await page.locator('[data-testid="bidding-table-body"]').textContent();
  return auctionText.trim().split(/\s+/).filter(bid => bid.length > 0);
}

/**
 * Wait for AI to complete its bid
 */
export async function waitForAIBid(page) {
  // Wait for either:
  // 1. Bidding box to be enabled again (AI finished, auction continues)
  // 2. Play button to appear (auction complete)

  try {
    await Promise.race([
      // Option 1: Bidding continues
      page.waitForSelector('[data-testid="bid-call-Pass"]:not([disabled])', {
        state: 'visible',
        timeout: 10000
      }),
      // Option 2: Auction complete - play button appears
      page.waitForSelector('[data-testid="play-button"], text=Play This Hand', {
        state: 'visible',
        timeout: 10000
      })
    ]);
  } catch (error) {
    // If neither condition is met, the test should fail with a clear message
    throw new Error('AI bid timeout: Neither bidding box re-enabled nor play button appeared');
  }
}

/**
 * Play a complete bidding sequence
 * User bids, then AI bids until auction complete
 */
export async function playBiddingSequence(page, userBids) {
  for (const bid of userBids) {
    if (bid.type === 'bid') {
      await makeBid(page, bid.level, bid.suit);
    } else {
      await makeCall(page, bid.call);
    }

    // Wait for AI to respond
    await waitForAIBid(page);
  }
}

/**
 * Open the dashboard
 */
export async function openDashboard(page) {
  await page.click('[data-testid="dashboard-button"]');

  // Wait for dashboard content to load
  await page.waitForSelector('text=Learning Dashboard', { state: 'visible' });
}

/**
 * Close the dashboard
 */
export async function closeDashboard(page) {
  await page.click('.close-dashboard');

  // Wait for dashboard to close
  await page.waitForSelector('text=Learning Dashboard', { state: 'hidden' });
}

/**
 * Check if bidding is complete (3 consecutive passes)
 */
export async function isBiddingComplete(page) {
  const auction = await getAuction(page);

  // Check last 3 bids are all "Pass"
  if (auction.length < 4) return false;

  const lastThree = auction.slice(-3);
  return lastThree.every(bid => bid === 'Pass');
}

/**
 * Play a card during card play phase
 * @param {string} rank - Card rank (A, K, Q, J, 10, 9, etc.)
 * @param {string} suit - Card suit (♣, ♦, ♥, ♠)
 */
export async function playCard(page, rank, suit) {
  // Cards should have data-testid like "card-AS" for Ace of Spades
  const suitLetter = { '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' }[suit];
  await page.click(`[data-testid="card-${rank}${suitLetter}"]`);

  // Wait for card to be played
  await page.waitForTimeout(500);
}

/**
 * Wait for game phase to change
 */
export async function waitForGamePhase(page, phase) {
  // Wait for specific phase indicators
  if (phase === 'playing') {
    await page.waitForSelector('[data-testid="play-this-hand-button"]', {
      state: 'hidden',
      timeout: 5000
    });
  } else if (phase === 'bidding') {
    await page.waitForSelector('[data-testid="bidding-box"]', { state: 'visible' });
  }
}
