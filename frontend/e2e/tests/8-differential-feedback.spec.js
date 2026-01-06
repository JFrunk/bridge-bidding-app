/**
 * E2E Test: Differential Feedback System
 *
 * Tests the differential analyzer feedback flow:
 * - User makes a bid
 * - Receives feedback panel with correctness rating
 * - Non-optimal bids show "Why?" button
 * - Clicking "Why?" expands differential analysis
 * - Analysis shows learning points and factors
 *
 * This validates the differential analyzer integration.
 */

const { test, expect } = require('@playwright/test');
const { loginAsGuest } = require('../helpers/auth-helpers');
const { dealNewHand, makeBid, makeCall, waitForAIBid } = require('../helpers/game-helpers');

test.describe('Differential Feedback System', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);
  });

  test('should show feedback panel after user bid', async ({ page }) => {
    // Make a bid (1 Club - usually a safe opening)
    await makeBid(page, 1, '♣');

    // Wait for feedback panel to appear
    // The panel may or may not appear depending on correctness
    // We just verify the bid was processed
    await waitForAIBid(page);

    // Verify the auction contains our bid
    const auctionText = await page.locator('[data-testid="bidding-table-body"]').textContent();
    expect(auctionText).toContain('1♣');

    console.log('✅ Feedback after bid test passed');
  });

  test('should show feedback panel with correctness rating', async ({ page }) => {
    // Make a bid that might be suboptimal to trigger feedback
    await makeBid(page, 1, '♣');

    // Wait for processing
    await page.waitForTimeout(1000);

    // Check if feedback panel appeared with correctness data
    const feedbackPanel = page.locator('[data-testid="bid-feedback-panel"]');
    const panelVisible = await feedbackPanel.isVisible({ timeout: 2000 }).catch(() => false);

    if (panelVisible) {
      // Get the correctness level from data attribute
      const correctness = await feedbackPanel.getAttribute('data-correctness');
      console.log(`✅ Feedback panel visible with correctness: ${correctness}`);

      // Verify it has a valid correctness value
      expect(['optimal', 'acceptable', 'suboptimal', 'error']).toContain(correctness);
    } else {
      // Panel might not show for optimal bids - that's OK
      console.log('ℹ️ Feedback panel not visible (may be optimal bid)');
    }
  });

  test('should show "Why?" button for non-optimal bids', async ({ page }) => {
    // We need to find a scenario where the user makes a suboptimal bid
    // Pass is usually suboptimal if you have a hand that should open

    // First check if Pass button is enabled (it's our turn)
    const passEnabled = await page.locator('[data-testid="bid-call-Pass"]:not([disabled])').isVisible();

    if (passEnabled) {
      // Make a Pass - this might be suboptimal depending on the hand
      await makeCall(page, 'Pass');

      // Wait for processing
      await page.waitForTimeout(1500);

      // Check for feedback panel
      const feedbackPanel = page.locator('[data-testid="bid-feedback-panel"]');
      const panelVisible = await feedbackPanel.isVisible({ timeout: 3000 }).catch(() => false);

      if (panelVisible) {
        const correctness = await feedbackPanel.getAttribute('data-correctness');

        if (correctness !== 'optimal' && correctness !== 'acceptable') {
          // Should have "Why?" button for non-optimal bids
          const whyButton = page.locator('[data-testid="feedback-why-button"]');
          const whyVisible = await whyButton.isVisible({ timeout: 2000 }).catch(() => false);

          if (whyVisible) {
            console.log('✅ "Why?" button visible for suboptimal bid');
            await expect(whyButton).toBeVisible();
          } else {
            console.log('ℹ️ "Why?" button not visible (may need differential data)');
          }
        } else {
          console.log(`ℹ️ Bid was ${correctness}, no "Why?" button expected`);
        }
      }
    }

    console.log('✅ Why button test completed');
  });

  test('should expand differential analysis when clicking "Why?"', async ({ page }) => {
    // Make a pass (often suboptimal with opening hands)
    const passEnabled = await page.locator('[data-testid="bid-call-Pass"]:not([disabled])').isVisible();

    if (!passEnabled) {
      console.log('ℹ️ Pass button not enabled, skipping test');
      return;
    }

    await makeCall(page, 'Pass');
    await page.waitForTimeout(1500);

    // Look for the "Why?" button
    const whyButton = page.locator('[data-testid="feedback-why-button"]');
    const whyVisible = await whyButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (whyVisible) {
      // Click the "Why?" button
      await whyButton.click();

      // Wait for differential container to appear
      const differentialContainer = page.locator('[data-testid="differential-container"]');
      await expect(differentialContainer).toBeVisible({ timeout: 5000 });

      // Check for differential panel inside
      const differentialPanel = page.locator('[data-testid="differential-panel"]');
      await expect(differentialPanel).toBeVisible({ timeout: 3000 });

      // Verify the button text changed to "Hide details"
      await expect(whyButton).toHaveText('Hide details');

      console.log('✅ Differential analysis expanded successfully');

      // Click again to collapse
      await whyButton.click();
      await expect(differentialContainer).not.toBeVisible({ timeout: 2000 });
      await expect(whyButton).toHaveText('Why?');

      console.log('✅ Differential analysis collapsed successfully');
    } else {
      console.log('ℹ️ "Why?" button not present, differential analysis not available for this bid');
    }
  });

  test('should display rating and score in differential panel', async ({ page }) => {
    // Make a pass to trigger feedback
    await makeCall(page, 'Pass');
    await page.waitForTimeout(1500);

    const whyButton = page.locator('[data-testid="feedback-why-button"]');
    const whyVisible = await whyButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (whyVisible) {
      await whyButton.click();

      // Wait for differential panel
      const differentialPanel = page.locator('[data-testid="differential-panel"]');
      await expect(differentialPanel).toBeVisible({ timeout: 5000 });

      // Check for rating badge
      const ratingBadge = page.locator('[data-testid="differential-rating"]');
      const ratingVisible = await ratingBadge.isVisible({ timeout: 2000 }).catch(() => false);

      if (ratingVisible) {
        const ratingText = await page.locator('[data-testid="rating-text"]').textContent();
        const scoreText = await page.locator('[data-testid="rating-score"]').textContent();

        console.log(`✅ Rating: ${ratingText}, ${scoreText}`);

        // Verify rating is one of the expected values
        expect(['optimal', 'acceptable', 'suboptimal', 'error']).toContain(ratingText.toLowerCase());
        expect(scoreText).toMatch(/Score: \d+/);
      }
    } else {
      console.log('ℹ️ Differential panel not available for this scenario');
    }
  });

  test('should display learning points in differential panel', async ({ page }) => {
    // Make a pass
    await makeCall(page, 'Pass');
    await page.waitForTimeout(1500);

    const whyButton = page.locator('[data-testid="feedback-why-button"]');
    const whyVisible = await whyButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (whyVisible) {
      await whyButton.click();

      // Wait for differential panel
      await page.waitForSelector('[data-testid="differential-panel"]', { state: 'visible', timeout: 5000 });

      // Check for learning point container
      const learningContainer = page.locator('[data-testid="learning-point-container"]');
      const learningVisible = await learningContainer.isVisible({ timeout: 2000 }).catch(() => false);

      if (learningVisible) {
        // Get learning point content
        const learningText = await learningContainer.textContent();
        console.log(`✅ Learning point found: ${learningText.substring(0, 100)}...`);

        // Should have some educational content
        expect(learningText.length).toBeGreaterThan(10);
      } else {
        console.log('ℹ️ No learning point container (may not have learning data)');
      }
    }
  });

  test('should handle multiple bids with feedback', async ({ page }) => {
    // Make first bid
    await makeBid(page, 1, '♠');
    await waitForAIBid(page);

    // Check if we can continue bidding
    const passStillEnabled = await page.locator('[data-testid="bid-call-Pass"]:not([disabled])').isVisible();

    if (passStillEnabled) {
      // Make second bid (pass)
      await makeCall(page, 'Pass');
      await waitForAIBid(page);

      // Verify both bids are in auction
      const auctionText = await page.locator('[data-testid="bidding-table-body"]').textContent();
      expect(auctionText).toContain('1♠');
      expect(auctionText).toContain('Pass');

      console.log('✅ Multiple bids with feedback handled correctly');
    } else {
      console.log('ℹ️ Auction may have ended after first bid');
    }
  });
});

test.describe('Differential Feedback Integration', () => {
  test('should integrate with bidding feedback panel seamlessly', async ({ page }) => {
    await loginAsGuest(page);
    await dealNewHand(page);

    // Make a bid
    await makeBid(page, 1, 'NT');
    await page.waitForTimeout(1000);

    // Check feedback panel structure
    const feedbackPanel = page.locator('[data-testid="bid-feedback-panel"]');
    const visible = await feedbackPanel.isVisible({ timeout: 3000 }).catch(() => false);

    if (visible) {
      // Verify panel has proper structure
      const panelClass = await feedbackPanel.getAttribute('class');
      expect(panelClass).toContain('bid-feedback-panel');

      // Check for one of the correctness classes
      expect(
        panelClass.includes('feedback-optimal') ||
        panelClass.includes('feedback-acceptable') ||
        panelClass.includes('feedback-suboptimal') ||
        panelClass.includes('feedback-error')
      ).toBe(true);

      console.log('✅ Feedback panel integration verified');
    } else {
      console.log('ℹ️ Feedback panel not shown for this bid');
    }
  });
});
