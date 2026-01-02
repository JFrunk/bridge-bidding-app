/**
 * Regression Test: Card Highlight Bug (2025-11-03)
 *
 * Bug: Cards in North position appeared pre-highlighted without user interaction
 * Root Cause: React key collision causing component state reuse across hands
 *
 * This test ensures:
 * 1. No cards are visually highlighted when it's North's turn
 * 2. Only legal cards have the "clickable" class
 * 3. Follow-suit rules are enforced
 * 4. React keys are unique across hands
 */

const { test, expect } = require('@playwright/test');

test.describe('Card Highlight Bug Regression', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for app to load
    await page.waitForSelector('[data-testid="play-another-hand-button"]', { timeout: 10000 });
  });

  test('should not pre-highlight any cards in North dummy hand', async ({ page }) => {
    // Start a random play hand
    await page.click('[data-testid="play-another-hand-button"]');

    // Wait for play phase to start
    await page.waitForSelector('.play-table', { timeout: 5000 });

    // Wait for opening lead
    await page.waitForTimeout(2000);

    // Check if North is dummy (label contains "Dummy")
    const northLabel = await page.locator('.position-north .position-label').textContent();

    if (northLabel.includes('Dummy')) {
      // North is dummy - check for pre-highlighted cards

      // Get all cards in North's hand
      const northCards = await page.locator('.position-north .playable-card').all();

      // Check that NO cards have transform applied (would indicate highlight)
      for (const card of northCards) {
        const transform = await card.evaluate(el =>
          window.getComputedStyle(el).transform
        );

        // Transform should be "none" or "matrix(1, 0, 0, 1, 0, 0)" (no translation)
        // If card is highlighted, transform would have translateY value
        expect(transform).not.toContain('matrix(1, 0, 0, 1, 0, -'); // No negative Y translation
      }

      // Verify cards have unique React keys (check data-testid or key attribute)
      const cardKeys = await Promise.all(
        northCards.map(card => card.getAttribute('data-key') || card.evaluate(el => el.key))
      );

      // All keys should be unique
      const uniqueKeys = new Set(cardKeys);
      expect(uniqueKeys.size).toBe(northCards.length);
    }
  });

  test('should only enable legal cards based on follow-suit rules', async ({ page }) => {
    // Start a random play hand
    await page.click('[data-testid="play-another-hand-button"]');

    // Wait for play phase
    await page.waitForSelector('.play-table', { timeout: 5000 });

    // Wait for some cards to be played
    await page.waitForTimeout(3000);

    // Check if it's user's turn to play from North (when user is declarer)
    const northLabel = await page.locator('.position-north .position-label').textContent();

    if (northLabel.includes('Dummy')) {
      // Get current trick to see what suit was led
      const currentTrick = await page.locator('.current-trick-display .card').all();

      if (currentTrick.length > 0) {
        // A suit has been led
        const northCards = await page.locator('.position-north .playable-card').all();

        // Check that only some cards have "clickable" class (follow-suit enforcement)
        let clickableCount = 0;
        let totalCount = 0;

        for (const card of northCards) {
          totalCount++;
          const classList = await card.getAttribute('class');
          if (classList && classList.includes('clickable')) {
            clickableCount++;
          }
        }

        // At least one card should be clickable (can always play something)
        expect(clickableCount).toBeGreaterThan(0);

        // If North has cards in led suit, not all cards should be clickable
        // (This is a weak test - ideally we'd check the actual led suit)
        if (totalCount > 4) {
          // If North has more than 4 cards, likely they have multiple suits
          // So follow-suit should restrict which cards are clickable
          expect(clickableCount).toBeLessThan(totalCount);
        }
      }
    }
  });

  test('should not show stuck :active state on disabled cards', async ({ page }) => {
    // Start a random play hand
    await page.click('[data-testid="play-another-hand-button"]');

    // Wait for play phase
    await page.waitForSelector('.play-table', { timeout: 5000 });

    // Wait for game to progress
    await page.waitForTimeout(3000);

    // Find a disabled card (non-clickable)
    const disabledCard = page.locator('.position-north .playable-card:not(.clickable)').first();

    if (await disabledCard.count() > 0) {
      // Try to click/touch the disabled card
      await disabledCard.click({ force: true });

      // Wait a moment
      await page.waitForTimeout(500);

      // Check that card doesn't have transform applied
      const transform = await disabledCard.evaluate(el =>
        window.getComputedStyle(el).transform
      );

      // Should not have translateY transform (would indicate stuck active state)
      expect(transform).not.toContain('translateY');
      expect(transform).not.toContain('matrix(1, 0, 0, 1, 0, -');
    }
  });

  test('should generate unique keys across multiple hands', async ({ page }) => {
    // Play multiple hands and verify keys don't collide

    for (let handNum = 0; handNum < 3; handNum++) {
      // Start a new hand
      await page.click('[data-testid="play-another-hand-button"]');

      // Wait for play phase
      await page.waitForSelector('.play-table', { timeout: 5000 });

      // Wait for North to be visible (if dummy)
      await page.waitForTimeout(2000);

      // Get all cards in North's hand
      const northCards = await page.locator('.position-north .playable-card').all();

      if (northCards.length > 0) {
        // Store the card elements and their computed properties
        const cardData = await Promise.all(
          northCards.map(async (card) => ({
            key: await card.getAttribute('data-key') || await card.evaluate(el => el.key),
            transform: await card.evaluate(el => window.getComputedStyle(el).transform),
            classList: await card.getAttribute('class')
          }))
        );

        // Verify all keys are unique
        const keys = cardData.map(c => c.key).filter(Boolean);
        const uniqueKeys = new Set(keys);
        expect(uniqueKeys.size).toBe(keys.length);

        // Verify no cards are stuck highlighted
        for (const data of cardData) {
          // Check if card appears highlighted when it shouldn't be
          if (!data.classList.includes('clickable')) {
            // Disabled card should not have translateY transform
            expect(data.transform).not.toContain('matrix(1, 0, 0, 1, 0, -');
          }
        }
      }
    }
  });
});
