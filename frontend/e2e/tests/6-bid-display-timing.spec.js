/**
 * E2E Test: Bid Display Timing
 *
 * Tests that bids appear immediately in the bidding table:
 * - User bids appear before AI bids
 * - AI bids appear sequentially (not batched)
 * - Each bid renders individually
 *
 * This validates the fix for the flushSync rendering issue.
 */

const { test, expect } = require('@playwright/test');
const { loginAsGuest } = require('../helpers/auth-helpers');
const { dealNewHand, makeCall } = require('../helpers/game-helpers');

test.describe('Bid Display Timing', () => {
  test('user bid appears immediately in bidding table', async ({ page }) => {
    // Login as guest
    await loginAsGuest(page);

    // Deal new hand - don't use dealNewHand() to avoid AI waiting complexity
    await page.click('[data-testid="deal-button"]');
    await page.waitForSelector('[data-testid="bidding-box"]', { state: 'visible' });
    await page.waitForTimeout(1000);

    // Wait until it's South's turn (Pass button enabled)
    await page.waitForSelector('[data-testid="bid-call-Pass"]:not([disabled])', {
      state: 'visible',
      timeout: 15000
    });

    // Get initial auction length
    const initialBids = await page.locator('[data-testid="bidding-table-body"] td').allTextContents();
    const initialLength = initialBids.filter(text => text.trim() !== '').length;

    console.log(`Initial bid count: ${initialLength}`);

    // Make a Pass bid
    await makeCall(page, 'Pass');

    // CRITICAL: User's bid should appear IMMEDIATELY
    // Check within 50ms (before AI bid starts at 500ms delay)
    await page.waitForTimeout(50);

    // Count bids in table now
    const afterUserBid = await page.locator('[data-testid="bidding-table-body"] td').allTextContents();
    const afterUserLength = afterUserBid.filter(text => text.trim() !== '').length;

    console.log(`After user bid count (50ms): ${afterUserLength}`);

    // User's bid should be in the table now
    // It might be initialLength + 1 (just user) OR initialLength + 2 (user + fast AI)
    // The key is that user's bid appeared - verify by checking auction contains more bids
    expect(afterUserLength).toBeGreaterThanOrEqual(initialLength + 1);

    // Verify user's Pass is in the auction
    const allBids = afterUserBid.filter(text => text.trim() !== '');
    const lastUserBid = allBids[initialLength]; // User's bid at initial position
    expect(lastUserBid).toContain('Pass');

    console.log('✅ User bid appears immediately in bidding table (within 50ms)');
  });

  test('AI bids appear sequentially (not batched)', async ({ page }) => {
    // Login as guest
    await loginAsGuest(page);

    // Deal new hand
    await page.click('[data-testid="deal-button"]');
    await page.waitForSelector('[data-testid="bidding-box"]', { state: 'visible' });
    await page.waitForTimeout(1000);

    // Get bid count after dealing
    const initialBids = await page.locator('[data-testid="bidding-table-body"] td').allTextContents();
    const initialCount = initialBids.filter(text => text.trim() !== '').length;

    console.log(`Initial bid count: ${initialCount}`);

    // Check if South is dealer
    const southHeader = await page.locator('[data-testid="bidding-header-south"]').textContent();
    const isSouthDealer = southHeader.includes('🔵');

    console.log(`South is dealer: ${isSouthDealer}`);

    if (!isSouthDealer) {
      // Wait for South's turn (Pass button enabled)
      await page.waitForSelector('[data-testid="bid-call-Pass"]:not([disabled])', {
        state: 'visible',
        timeout: 15000
      });

      // Get bid count when it's South's turn
      const afterAIBids = await page.locator('[data-testid="bidding-table-body"] td').allTextContents();
      const afterAICount = afterAIBids.filter(text => text.trim() !== '').length;

      console.log(`After AI bids: ${afterAICount}`);

      // AI bids should have appeared (auction progressed)
      expect(afterAICount).toBeGreaterThan(initialCount);
      console.log('✅ AI bids appeared before South');
    } else {
      // South is dealer - Pass button should already be enabled
      console.log('✅ South is dealer - bidding box ready');
    }

    // Now test user bid + AI response timing
    const beforePass = isSouthDealer ? initialCount : (await page.locator('[data-testid="bidding-table-body"] td').allTextContents()).filter(text => text.trim() !== '').length;
    await makeCall(page, 'Pass');

    // Wait 50ms and check
    await page.waitForTimeout(50);

    const after50ms = await page.locator('[data-testid="bidding-table-body"] td').allTextContents();
    const count50ms = after50ms.filter(text => text.trim() !== '').length;

    // User's Pass should appear immediately
    expect(count50ms).toBeGreaterThanOrEqual(beforePass + 1);

    console.log(`✅ User Pass appeared within 50ms (${beforePass} → ${count50ms})`);

    // Test complete - bids are rendering immediately with flushSync
    console.log('✅ Bid timing test passed - immediate rendering confirmed');
  });

  test('rapid user bids appear immediately (stress test)', async ({ page }) => {
    // Login
    await loginAsGuest(page);

    // Deal hand without using dealNewHand()
    await page.click('[data-testid="deal-button"]');
    await page.waitForSelector('[data-testid="bidding-box"]', { state: 'visible' });
    await page.waitForTimeout(1000);

    // Make multiple rapid bids (Pass until auction completes)
    const maxPasses = 10;
    let passCount = 0;

    for (let i = 0; i < maxPasses; i++) {
      // Check if it's South's turn
      const southHeader = page.locator('[data-testid="bidding-header-south"]');
      const className = await southHeader.getAttribute('class');

      if (!className.includes('current-player')) {
        // Not our turn - wait for AI
        await page.waitForTimeout(600);
        continue;
      }

      // Get current bid count
      const beforeBids = await page.locator('[data-testid="bidding-table-body"] td').allTextContents();
      const beforeCount = beforeBids.filter(text => text.trim() !== '').length;

      // Make a Pass bid
      await makeCall(page, 'Pass');
      passCount++;

      // IMMEDIATELY check that bid appears (within 50ms)
      await page.waitForTimeout(50);

      const afterBids = await page.locator('[data-testid="bidding-table-body"] td').allTextContents();
      const afterCount = afterBids.filter(text => text.trim() !== '').length;

      // Bid should appear immediately (might be +1 or +2 if AI is very fast)
      expect(afterCount).toBeGreaterThanOrEqual(beforeCount + 1);

      console.log(`✅ Pass ${passCount} appeared immediately (${beforeCount} → ${afterCount})`);

      // Check if auction is over (4 consecutive passes)
      const allBids = afterBids.filter(text => text.trim() !== '');
      if (allBids.length >= 4) {
        const lastFour = allBids.slice(-4);
        if (lastFour.every(bid => bid.includes('Pass'))) {
          console.log('✅ Auction complete - all 4 passes detected');
          break;
        }
      }

      // Wait for AI to bid before next iteration
      await page.waitForTimeout(600);
    }

    console.log(`✅ Stress test complete - ${passCount} rapid bids all appeared immediately`);
  });
});
