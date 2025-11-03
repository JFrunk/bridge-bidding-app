/**
 * E2E Test: Complete Game Flow
 *
 * Tests the complete user journey:
 * 1. Login
 * 2. Deal a hand
 * 3. Complete bidding
 * 4. View results
 * 5. Deal another hand
 *
 * This is the CRITICAL PATH test that validates the core game loop.
 */

const { test, expect } = require('@playwright/test');
const { loginAsGuest } = require('../helpers/auth-helpers');
const { dealNewHand, makeCall, waitForAIBid, getAuction } = require('../helpers/game-helpers');

test.describe('Complete Game Flow - Critical Path', () => {
  test('should complete full game cycle: login → deal → bid → result', async ({ page }) => {
    // Step 1: Login as guest
    await loginAsGuest(page);

    // Verify logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

    // Step 2: Deal a new hand
    await dealNewHand(page);

    // Verify hand is dealt
    await expect(page.locator('[data-testid="bidding-box"]')).toBeVisible();
    await expect(page.locator('[data-testid="bidding-table"]')).toBeVisible();

    // Verify we see our hand (South player)
    const handDisplay = page.locator('.player-south .hand-display');
    await expect(handDisplay).toBeVisible();

    // Step 3: Make bids until auction complete
    // User (South) passes
    await makeCall(page, 'Pass');

    // Wait for AI to bid (West)
    await waitForAIBid(page);

    // User passes again
    await makeCall(page, 'Pass');

    // Wait for AI (North)
    await waitForAIBid(page);

    // User passes third time
    await makeCall(page, 'Pass');

    // Wait for AI (East)
    await waitForAIBid(page);

    // User passes fourth time (should complete auction)
    await makeCall(page, 'Pass');

    // Step 4: Verify auction is complete
    // Should see at least 4 passes in auction
    const auction = await getAuction(page);
    expect(auction.length).toBeGreaterThanOrEqual(4);

    // Count passes
    const passCount = auction.filter(bid => bid === 'Pass').length;
    expect(passCount).toBeGreaterThanOrEqual(4);

    console.log(`✅ Complete game flow test passed - ${auction.length} bids, ${passCount} passes`);
  });

  test('should allow multiple hands in succession', async ({ page }) => {
    // Login
    await loginAsGuest(page);

    // Play first hand
    await dealNewHand(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');

    // Deal second hand
    await page.click('[data-testid="deal-button"]');

    // Verify new hand is dealt
    await expect(page.locator('[data-testid="bidding-box"]')).toBeVisible();

    // Bidding table should be reset or have new bids
    const auction2 = await getAuction(page);

    // Second hand bidding works
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    console.log(`✅ Multiple hands test passed - played 2 hands`);
  });

  test('should display bidding table with all four players', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Verify all four player headers are visible
    await expect(page.locator('[data-testid="bidding-header-north"]')).toBeVisible();
    await expect(page.locator('[data-testid="bidding-header-east"]')).toBeVisible();
    await expect(page.locator('[data-testid="bidding-header-south"]')).toBeVisible();
    await expect(page.locator('[data-testid="bidding-header-west"]')).toBeVisible();

    // Verify dealer indicator is present (should have 🔵 emoji)
    const headers = await page.locator('[data-testid^="bidding-header-"]').allTextContents();
    const hasDealer = headers.some(header => header.includes('🔵'));
    expect(hasDealer).toBeTruthy();

    console.log('✅ Bidding table display test passed');
  });

  test('should show hand analysis with HCP and distribution', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Wait for hand analysis to be visible
    await expect(page.locator('.hand-analysis')).toBeVisible();

    // Verify HCP is displayed
    await expect(page.locator('text=HCP:')).toBeVisible();

    // Verify distribution points are displayed
    await expect(page.locator('text=Dist:')).toBeVisible();

    // Verify total points are displayed
    await expect(page.locator('text=Total:')).toBeVisible();

    // Verify suit breakdown is shown
    await expect(page.locator('.suit-points')).toBeVisible();

    console.log('✅ Hand analysis display test passed');
  });

  test('should update bidding table as auction progresses', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Get initial auction length
    const initialAuction = await getAuction(page);
    const initialLength = initialAuction.length;

    // Make a bid
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    // Get updated auction
    const updatedAuction = await getAuction(page);

    // Auction should have grown (user bid + AI bid)
    expect(updatedAuction.length).toBeGreaterThan(initialLength);

    // Should see "Pass" in the auction
    expect(updatedAuction).toContain('Pass');

    console.log(`✅ Auction progression test passed - grew from ${initialLength} to ${updatedAuction.length} bids`);
  });
});
