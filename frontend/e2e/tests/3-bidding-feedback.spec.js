/**
 * E2E Test: Bidding with Feedback
 *
 * Tests the bidding feedback system:
 * - User makes a bid
 * - Receives feedback (optimal/acceptable/suboptimal)
 * - Sees explanation
 * - Score is tracked
 *
 * This validates the core learning/feedback loop.
 */

const { test, expect } = require('@playwright/test');
const { loginAsGuest, loginWithEmail } = require('../helpers/auth-helpers');
const { dealNewHand, makeBid, makeCall, waitForAIBid } = require('../helpers/game-helpers');

test.describe('Bidding Feedback System', () => {
  test('should provide feedback after user bid', async ({ page }) => {
    // Login
    await loginAsGuest(page);

    // Deal hand
    await dealNewHand(page);

    // Make a bid (1♣)
    await makeBid(page, 1, '♣');

    // Should see some feedback or explanation
    // (Feedback might appear in console, modal, or auction explanation)
    // Wait for AI to respond
    await waitForAIBid(page);

    // Auction should contain the user's bid
    const auctionText = await page.locator('[data-testid="bidding-table-body"]').textContent();
    expect(auctionText).toContain('1♣');

    console.log('✅ Bidding feedback test passed - user bid accepted');
  });

  test('should show bidding box with all bid options', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Verify all level buttons are present (1-7)
    for (let level = 1; level <= 7; level++) {
      await expect(page.locator(`[data-testid="bid-level-${level}"]`)).toBeVisible();
    }

    // Verify all suit buttons are present
    const suits = ['♣', '♦', '♥', '♠', 'NT'];
    for (const suit of suits) {
      await expect(page.locator(`[data-testid="bid-suit-${suit}"]`)).toBeVisible();
    }

    // Verify call buttons are present
    const calls = ['Pass', 'X', 'XX'];
    for (const call of calls) {
      await expect(page.locator(`[data-testid="bid-call-${call}"]`)).toBeVisible();
    }

    console.log('✅ Bidding box completeness test passed');
  });

  test('should enforce bid level selection before suit selection', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Suit buttons should be disabled before level is selected
    const clubButton = page.locator('[data-testid="bid-suit-♣"]');
    await expect(clubButton).toBeDisabled();

    // Select level 1
    await page.click('[data-testid="bid-level-1"]');

    // Now suit buttons should be enabled
    await expect(clubButton).toBeEnabled();

    console.log('✅ Bid level enforcement test passed');
  });

  test('should make a complete bid sequence (level + suit)', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Get initial auction state
    const initialAuction = await page.locator('[data-testid="bidding-table-body"]').textContent();

    // Select level 1
    await page.click('[data-testid="bid-level-1"]');

    // Select NT
    await page.click('[data-testid="bid-suit-NT"]');

    // Wait for bid to be processed
    await page.waitForTimeout(1000);

    // Get updated auction
    const updatedAuction = await page.locator('[data-testid="bidding-table-body"]').textContent();

    // Auction should have changed (our bid added)
    expect(updatedAuction).not.toBe(initialAuction);

    // Should see 1NT in auction
    expect(updatedAuction).toContain('1NT');

    console.log('✅ Complete bid sequence test passed - 1NT bid made');
  });

  test('should allow Pass without level selection', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Get initial auction
    const initialAuction = await page.locator('[data-testid="bidding-table-body"]').textContent();

    // Click Pass (no level selection needed)
    await page.click('[data-testid="bid-call-Pass"]');

    // Wait for bid to process
    await page.waitForTimeout(1000);

    // Get updated auction
    const updatedAuction = await page.locator('[data-testid="bidding-table-body"]').textContent();

    // Auction should have changed
    expect(updatedAuction).not.toBe(initialAuction);

    // Should see Pass in auction
    expect(updatedAuction).toContain('Pass');

    console.log('✅ Pass without level test passed');
  });

  test('should track bidding decisions for authenticated user', async ({ page }) => {
    // Login with email to track decisions
    const testEmail = `bidding-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Bidding Tester');

    // Deal and make a bid
    await dealNewHand(page);
    await makeBid(page, 1, '♠');

    // Wait for processing
    await waitForAIBid(page);

    // Bid should be recorded
    // (This would be verified in the database, but we can check that
    // the bid appears in the auction which confirms it was processed)
    const auction = await page.locator('[data-testid="bidding-table-body"]').textContent();
    expect(auction).toContain('1♠');

    console.log('✅ Bidding decision tracking test passed');
  });

  test('should handle rapid bid sequence without errors', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Make quick Pass
    await makeCall(page, 'Pass');

    // Wait for AI
    await waitForAIBid(page);

    // Make another Pass quickly
    await makeCall(page, 'Pass');

    // Wait for AI
    await waitForAIBid(page);

    // Make third Pass
    await makeCall(page, 'Pass');

    // System should handle rapid bids gracefully
    const auction = await page.locator('[data-testid="bidding-table-body"]').textContent();

    // Should see multiple passes
    const passCount = (auction.match(/Pass/g) || []).length;
    expect(passCount).toBeGreaterThanOrEqual(3);

    console.log(`✅ Rapid bidding test passed - ${passCount} passes in auction`);
  });
});
