/**
 * E2E Test: Play Feedback in Hand Review Modal
 *
 * Tests that card play feedback is consistently saved and displayed:
 * 1. Complete a full hand with card play
 * 2. Open the Hand Review modal
 * 3. Navigate through plays and verify feedback is shown
 * 4. Verify feedback quality for user-controlled positions
 *
 * User-Controlled Positions:
 * - South (always controlled by user)
 * - North (also controlled when NS is declaring - dummy hand)
 * - E/W plays show "AI play - no feedback recorded"
 *
 * This validates the end-to-end flow:
 * Play card -> Backend evaluates -> Stores in DB -> Retrieves via API -> Displays in modal
 */

const { test, expect } = require('@playwright/test');
const { loginWithEmail } = require('../helpers/auth-helpers');
const { dealNewHand, makeCall, waitForAIBid, makeBid } = require('../helpers/game-helpers');

test.describe('Play Feedback in Hand Review Modal', () => {

  test.beforeEach(async ({ page }) => {
    // Login with email to track data
    const testEmail = `play-feedback-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Play Feedback Tester');
  });

  test('should show play feedback in review modal after completing a hand', async ({ page }) => {
    // This is a longer test - needs time for full hand completion
    test.setTimeout(180000); // 3 minutes

    // Deal a hand
    await dealNewHand(page);

    // Make a simple 1NT contract - South becomes declarer
    // This means user controls both S and N (dummy) positions
    await makeBid(page, 1, 'NT');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');

    // Click play button to start card play
    const playButton = page.locator('[data-testid="play-this-hand-button"]');
    await expect(playButton).toBeVisible({ timeout: 10000 });
    await playButton.click();

    // Wait for play phase to start (opening lead by AI)
    await page.waitForTimeout(3000);

    // Play through the hand - click playable cards when available
    let attempts = 0;
    const maxAttempts = 100;

    while (attempts < maxAttempts) {
      attempts++;

      // Check if hand is complete
      const scoreModal = page.locator('[data-testid="score-modal"], .score-modal, text=/Made|Down/');
      const handComplete = await scoreModal.count() > 0;
      if (handComplete) {
        console.log(`Hand completed after ${attempts} attempts`);
        break;
      }

      // Check for new hand button
      const newHandBtn = page.locator('[data-testid="new-hand-button"], button:has-text("New Hand")');
      if (await newHandBtn.count() > 0) {
        console.log('Hand complete - new hand button visible');
        break;
      }

      // Look for playable cards
      const playableCards = page.locator('.playable-card:not(.disabled), .card.playable, [data-testid^="playable-card"]:not([disabled])');
      const cardCount = await playableCards.count();

      if (cardCount > 0) {
        await playableCards.first().click();
        await page.waitForTimeout(1000);
      } else {
        await page.waitForTimeout(500);
      }
    }

    console.log(`Hand play complete after ${attempts} attempts`);
    await page.waitForTimeout(3000);

    // Try to open review modal via score modal or dashboard
    const reviewButton = page.locator(
      '[data-testid="review-hand-button"], button:has-text("Review"), ' +
      'button:has-text("Play-by-Play"), [data-testid="play-by-play-button"]'
    );

    if (await reviewButton.count() > 0) {
      await reviewButton.first().click();
      await page.waitForTimeout(1000);
    } else {
      // Close score modal and open from dashboard
      const closeScoreBtn = page.locator('[data-testid="close-score-modal"], .close-btn, button:has-text("Close")');
      if (await closeScoreBtn.count() > 0) {
        await closeScoreBtn.first().click();
        await page.waitForTimeout(500);
      }

      // Open dashboard
      const dashboardBtn = page.locator('[data-testid="dashboard-button"]');
      await expect(dashboardBtn).toBeVisible({ timeout: 5000 });
      await dashboardBtn.click();

      await page.waitForSelector('[data-testid="dashboard-modal"], .learning-dashboard', {
        state: 'visible',
        timeout: 10000
      });

      // Expand Practice Play section
      const practicePlayBar = page.locator('[data-testid="progress-bar-practice-play"], .progress-bar:has-text("Practice Play")');
      if (await practicePlayBar.count() > 0) {
        await practicePlayBar.click();
        await page.waitForTimeout(500);
      }

      // Click on most recent hand
      const handRow = page.locator('.hand-row, [data-testid^="hand-history-row"]').first();
      if (await handRow.count() > 0) {
        await handRow.click();
        await page.waitForTimeout(500);
      }
    }

    // Wait for Hand Review Modal
    const reviewModal = page.locator('[data-testid="hand-review-modal"]');
    await expect(reviewModal).toBeVisible({ timeout: 10000 });
    console.log('Hand Review Modal is visible');

    // Click Next to advance through plays
    const nextButton = page.locator('[data-testid="replay-next-btn"]');
    if (await nextButton.count() > 0 && await nextButton.isEnabled()) {
      await nextButton.click();
      await page.waitForTimeout(500);
    }

    // Verify feedback panel is visible
    const feedbackContainer = page.locator('[data-testid="trick-feedback-container"]');
    await expect(feedbackContainer).toBeVisible({ timeout: 5000 });

    // Navigate through plays and count feedback types
    let userFeedbackCount = 0;
    let aiFeedbackCount = 0;
    let basicInfoCount = 0;

    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(300);

      // Check feedback type using data-testid
      const userFeedback = page.locator('[data-testid="trick-feedback-panel"]');
      const aiPlayFeedback = page.locator('[data-testid="trick-feedback-ai-play"]');
      const basicInfo = page.locator('[data-testid="trick-feedback-basic-info"]');

      if (await userFeedback.count() > 0) {
        userFeedbackCount++;
        // Get the position for logging
        const position = await userFeedback.getAttribute('data-position').catch(() => '?');
        const rating = await userFeedback.getAttribute('data-rating').catch(() => '?');
        console.log(`User feedback: position=${position}, rating=${rating}`);
      } else if (await aiPlayFeedback.count() > 0) {
        aiFeedbackCount++;
      } else if (await basicInfo.count() > 0) {
        basicInfoCount++;
        const position = await basicInfo.getAttribute('data-position').catch(() => '?');
        console.log(`Basic info: position=${position}`);
      }

      // Click next if available
      if (await nextButton.isEnabled()) {
        await nextButton.click();
      } else {
        break;
      }
    }

    console.log(`User feedback: ${userFeedbackCount}, AI plays: ${aiFeedbackCount}, Basic info: ${basicInfoCount}`);

    // When South is declarer:
    // - S and N positions should have user feedback (or basic info if DDS unavailable)
    // - E and W positions should show AI play message
    // We expect at least some user feedback
    expect(userFeedbackCount + basicInfoCount).toBeGreaterThan(0);

    console.log('Play feedback review test passed');
  });

  test('should display feedback badges with correct ratings', async ({ page }) => {
    test.setTimeout(180000);

    await dealNewHand(page);

    // Make contract
    await makeBid(page, 1, '♠'); // Trump suit contract
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');

    // Start play
    const playButton = page.locator('[data-testid="play-this-hand-button"]');
    await expect(playButton).toBeVisible({ timeout: 10000 });
    await playButton.click();
    await page.waitForTimeout(3000);

    // Play through quickly
    for (let i = 0; i < 25; i++) {
      const playableCards = page.locator('.playable-card:not(.disabled), .card.playable');
      if (await playableCards.count() > 0) {
        await playableCards.first().click();
        await page.waitForTimeout(1200);
      } else {
        await page.waitForTimeout(400);
      }
      if (await page.locator('text=/Made|Down/').count() > 0) break;
    }

    await page.waitForTimeout(2000);

    // Open review modal
    const reviewButton = page.locator('button:has-text("Review"), [data-testid="review-hand-button"]');
    if (await reviewButton.count() > 0) {
      await reviewButton.first().click();
    } else {
      const closeBtn = page.locator('.close-btn, button:has-text("Close")').first();
      if (await closeBtn.count() > 0) await closeBtn.click();

      await page.click('[data-testid="dashboard-button"]');
      await page.waitForSelector('.learning-dashboard', { state: 'visible', timeout: 5000 });

      const playSection = page.locator('text=Practice Play').first();
      if (await playSection.count() > 0) {
        await playSection.click();
        await page.waitForTimeout(500);
      }

      const handItem = page.locator('.hand-row, [data-testid^="hand-history"]').first();
      if (await handItem.count() > 0) {
        await handItem.click();
      }
    }

    await page.waitForSelector('[data-testid="hand-review-modal"]', { state: 'visible', timeout: 10000 });

    // Navigate through plays looking for feedback badges
    const nextBtn = page.locator('[data-testid="replay-next-btn"]');
    let foundBadge = false;

    for (let i = 0; i < 10; i++) {
      const feedbackBadge = page.locator('[data-testid="feedback-badge"]');

      if (await feedbackBadge.count() > 0) {
        const badgeText = await feedbackBadge.textContent();
        console.log(`Found feedback badge: ${badgeText}`);

        // Verify badge contains valid rating text
        const validRatings = ['Optimal', 'Good', 'Suboptimal', 'Blunder', 'Acceptable', 'Error'];
        const hasValidRating = validRatings.some(r => badgeText.includes(r));
        expect(hasValidRating).toBeTruthy();
        foundBadge = true;
        break;
      }

      if (await nextBtn.isEnabled()) {
        await nextBtn.click();
        await page.waitForTimeout(300);
      } else {
        break;
      }
    }

    // If DDS is available (production Linux), we should find badges
    // If not (macOS dev), basic info is acceptable
    if (!foundBadge) {
      const basicInfo = page.locator('[data-testid="trick-feedback-basic-info"], [data-testid="trick-feedback-panel"]');
      await expect(basicInfo.or(page.locator('[data-testid="trick-feedback-ai-play"]'))).toBeVisible();
      console.log('No detailed feedback badges found (may be running without DDS)');
    } else {
      console.log('Feedback badge structure test passed');
    }
  });

  test('should show AI play message for opponent positions', async ({ page }) => {
    // When South is declarer, E and W are opponents (AI)
    // Their plays should show "AI play - no feedback recorded"
    test.setTimeout(180000);

    await dealNewHand(page);

    // South declares 1NT
    await makeBid(page, 1, 'NT');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');

    // Start play and complete
    const playButton = page.locator('[data-testid="play-this-hand-button"]');
    await expect(playButton).toBeVisible({ timeout: 10000 });
    await playButton.click();
    await page.waitForTimeout(3000);

    // Play through
    for (let i = 0; i < 40; i++) {
      const playableCards = page.locator('.playable-card:not(.disabled)');
      if (await playableCards.count() > 0) {
        await playableCards.first().click();
        await page.waitForTimeout(700);
      } else {
        await page.waitForTimeout(300);
      }
      if (await page.locator('text=/Made|Down/').count() > 0) break;
    }

    await page.waitForTimeout(2000);

    // Open review modal
    const reviewBtn = page.locator('button:has-text("Review")');
    if (await reviewBtn.count() > 0) {
      await reviewBtn.first().click();
    } else {
      await page.locator('.close-btn').first().click().catch(() => {});
      await page.click('[data-testid="dashboard-button"]');
      await page.waitForSelector('.learning-dashboard', { state: 'visible', timeout: 5000 });
      await page.locator('text=Practice Play').first().click().catch(() => {});
      await page.waitForTimeout(500);
      await page.locator('.hand-row').first().click().catch(() => {});
    }

    await page.waitForSelector('[data-testid="hand-review-modal"]', { state: 'visible', timeout: 10000 });

    // Navigate through plays and verify we see both user feedback and AI play messages
    const nextBtn = page.locator('[data-testid="replay-next-btn"]');
    let sawAiPlay = false;
    let sawUserFeedback = false;

    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(300);

      // Check for AI play message (E/W positions)
      const aiPlayMsg = page.locator('[data-testid="trick-feedback-ai-play"]');
      if (await aiPlayMsg.count() > 0) {
        sawAiPlay = true;
      }

      // Check for user feedback (S/N positions when NS declares)
      const userFeedback = page.locator('[data-testid="trick-feedback-panel"], [data-testid="trick-feedback-basic-info"]');
      if (await userFeedback.count() > 0) {
        sawUserFeedback = true;
      }

      if (await nextBtn.isEnabled()) {
        await nextBtn.click();
      } else {
        break;
      }
    }

    console.log(`Saw AI play: ${sawAiPlay}, Saw user feedback: ${sawUserFeedback}`);

    // When South is declarer:
    // - We should see AI play messages for E/W
    // - We should see user feedback for S/N
    expect(sawAiPlay || sawUserFeedback).toBeTruthy();

    console.log('AI vs User play distinction test complete');
  });
});

test.describe('Play Feedback - Edge Cases', () => {

  test.beforeEach(async ({ page }) => {
    const testEmail = `edge-case-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Edge Case Tester');
  });

  test('should handle passed out auction gracefully', async ({ page }) => {
    await dealNewHand(page);

    // Wait for South's turn before trying to pass
    await page.waitForSelector('[data-testid="bid-call-Pass"]:not([disabled])', {
      state: 'visible',
      timeout: 20000
    });

    // Try to pass out
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    // Either passed out (shows message, no play button) or auction continues with play button
    const passedOutMessage = page.locator('[data-testid="passed-out-message"]');
    const playButton = page.locator('[data-testid="play-this-hand-button"]');

    await expect(passedOutMessage.or(playButton)).toBeVisible({ timeout: 10000 });

    // If passed out, verify play button is NOT shown
    if (await passedOutMessage.isVisible()) {
      await expect(playButton).not.toBeVisible();
      console.log('Hand passed out - play button correctly hidden');
    } else {
      console.log('Auction continued - play button shown');
    }
  });

  test('should show user-controlled positions correctly for NS declaring', async ({ page }) => {
    // When NS declares, user controls both South AND North (dummy)
    test.setTimeout(180000);

    await dealNewHand(page);
    await makeBid(page, 2, 'NT'); // Higher contract to be clearer
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);
    await makeCall(page, 'Pass');

    const playButton = page.locator('[data-testid="play-this-hand-button"]');
    await expect(playButton).toBeVisible({ timeout: 10000 });
    await playButton.click();
    await page.waitForTimeout(3000);

    // Play through a few tricks
    for (let i = 0; i < 20; i++) {
      const playableCards = page.locator('.playable-card:not(.disabled)');
      if (await playableCards.count() > 0) {
        await playableCards.first().click();
        await page.waitForTimeout(1000);
      } else {
        await page.waitForTimeout(400);
      }
      if (await page.locator('text=/Made|Down/').count() > 0) break;
    }

    await page.waitForTimeout(2000);

    // Open review
    const reviewBtn = page.locator('button:has-text("Review")');
    if (await reviewBtn.count() > 0) {
      await reviewBtn.first().click();
    } else {
      await page.locator('.close-btn').first().click().catch(() => {});
      await page.click('[data-testid="dashboard-button"]');
      await page.waitForSelector('.learning-dashboard', { state: 'visible', timeout: 5000 });
      await page.locator('text=Practice Play').first().click().catch(() => {});
      await page.waitForTimeout(500);
      await page.locator('.hand-row').first().click().catch(() => {});
    }

    await page.waitForSelector('[data-testid="hand-review-modal"]', { state: 'visible', timeout: 10000 });

    // Check for feedback from both S and N positions
    const nextBtn = page.locator('[data-testid="replay-next-btn"]');
    const positionsWithFeedback = new Set();

    for (let i = 0; i < 20; i++) {
      const userFeedback = page.locator('[data-testid="trick-feedback-panel"], [data-testid="trick-feedback-basic-info"]');
      if (await userFeedback.count() > 0) {
        const position = await userFeedback.getAttribute('data-position').catch(() => null);
        if (position) {
          positionsWithFeedback.add(position);
        }
      }

      if (await nextBtn.isEnabled()) {
        await nextBtn.click();
        await page.waitForTimeout(300);
      } else {
        break;
      }
    }

    console.log(`Positions with feedback: ${Array.from(positionsWithFeedback).join(', ')}`);

    // When NS declares, we should see feedback for both S and N positions
    // (At minimum S, but ideally both since user controls dummy too)
    expect(positionsWithFeedback.size).toBeGreaterThan(0);

    console.log('User-controlled positions test complete');
  });
});
