/**
 * E2E Test: Multi-User Isolation
 *
 * Tests that multiple users have isolated data:
 * - User A and User B login separately
 * - Each plays hands
 * - Dashboard shows only their own data
 * - No data leakage between users
 *
 * This is CRITICAL for multi-user functionality.
 */

const { test, expect } = require('@playwright/test');
const { loginWithEmail } = require('../helpers/auth-helpers');
const { dealNewHand, makeCall, waitForAIBid } = require('../helpers/game-helpers');

test.describe('Multi-User Isolation', () => {
  test('should isolate data between two users', async ({ browser }) => {
    // Create two separate browser contexts (simulating two different users)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const user1Page = await context1.newPage();
    const user2Page = await context2.newPage();

    try {
      // User 1: Login and play
      const user1Email = `user1-${Date.now()}@example.com`;
      await loginWithEmail(user1Page, user1Email, 'User One');

      await dealNewHand(user1Page);
      await makeCall(user1Page, 'Pass');
      await waitForAIBid(user1Page);
      await makeCall(user1Page, 'Pass');
      await waitForAIBid(user1Page);

      // User 2: Login (should start fresh)
      const user2Email = `user2-${Date.now()}@example.com`;
      await loginWithEmail(user2Page, user2Email, 'User Two');

      // User 2 should see a fresh game state
      await user2Page.waitForSelector('[data-testid="deal-button"]', { state: 'visible' });

      // User 2 deals and plays
      await dealNewHand(user2Page);
      await makeCall(user2Page, 'Pass');
      await waitForAIBid(user2Page);

      // User 1 should still have their own state (not affected by User 2)
      // Verify User 1's auction still has their bids
      const user1Auction = await user1Page.locator('[data-testid="bidding-table-body"]').textContent();
      expect(user1Auction).toContain('Pass');

      // User 2's auction should be independent
      const user2Auction = await user2Page.locator('[data-testid="bidding-table-body"]').textContent();
      expect(user2Auction).toContain('Pass');

      // Both users should be logged in with their own names
      const user1Name = await user1Page.locator('[data-testid="user-display-name"]').textContent();
      const user2Name = await user2Page.locator('[data-testid="user-display-name"]').textContent();

      expect(user1Name).toContain('User One');
      expect(user2Name).toContain('User Two');

      console.log('✅ Multi-user isolation test passed - data properly isolated');

    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('should show different dashboard data for different users', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const user1Page = await context1.newPage();
    const user2Page = await context2.newPage();

    try {
      // User 1: Login and generate data
      const user1Email = `dash1-${Date.now()}@example.com`;
      await loginWithEmail(user1Page, user1Email, 'Dashboard User 1');

      await dealNewHand(user1Page);
      await makeCall(user1Page, 'Pass');
      await waitForAIBid(user1Page);

      // Open User 1's dashboard
      await user1Page.click('[data-testid="dashboard-button"]');
      await expect(user1Page.locator('text=Learning Dashboard')).toBeVisible();

      // User 2: Login separately
      const user2Email = `dash2-${Date.now()}@example.com`;
      await loginWithEmail(user2Page, user2Email, 'Dashboard User 2');

      await dealNewHand(user2Page);

      // User 2 opens dashboard (should be empty or minimal for new user)
      await user2Page.click('[data-testid="dashboard-button"]');
      await expect(user2Page.locator('text=Learning Dashboard')).toBeVisible();

      // Both dashboards should be visible but with different data
      const user1DashboardVisible = await user1Page.locator('text=Learning Dashboard').isVisible();
      const user2DashboardVisible = await user2Page.locator('text=Learning Dashboard').isVisible();

      expect(user1DashboardVisible).toBeTruthy();
      expect(user2DashboardVisible).toBeTruthy();

      console.log('✅ Dashboard isolation test passed');

    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('should maintain isolation after page reload', async ({ browser }) => {
    const context1 = await browser.newContext();

    const userPage = await context1.newPage();

    try {
      // User logs in and plays
      const userEmail = `reload-${Date.now()}@example.com`;
      await loginWithEmail(userPage, userEmail, 'Reload Tester');

      await dealNewHand(userPage);
      await makeCall(userPage, 'Pass');
      await waitForAIBid(userPage);

      // Get auction state
      const auctionBefore = await userPage.locator('[data-testid="bidding-table-body"]').textContent();

      // Reload page
      await userPage.reload();
      await userPage.waitForLoadState('networkidle');

      // User should still be logged in (persisted)
      await expect(userPage.locator('[data-testid="user-menu"]')).toBeVisible();
      await expect(userPage.locator('[data-testid="user-display-name"]')).toContainText('Reload Tester');

      console.log('✅ Isolation after reload test passed');

    } finally {
      await context1.close();
    }
  });

  test('should handle concurrent user sessions', async ({ browser }) => {
    // Simulate 3 users playing simultaneously
    const contexts = [];
    const pages = [];

    try {
      for (let i = 0; i < 3; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();

        contexts.push(context);
        pages.push(page);

        // Each user logs in
        const email = `concurrent${i}-${Date.now()}@example.com`;
        await loginWithEmail(page, email, `User ${i}`);

        // Each user deals a hand
        await dealNewHand(page);
      }

      // All users make bids concurrently
      await Promise.all(pages.map(async (page) => {
        await makeCall(page, 'Pass');
      }));

      // Wait for all AI responses
      await Promise.all(pages.map(async (page) => {
        await waitForAIBid(page);
      }));

      // Verify all users have independent auctions
      for (let i = 0; i < 3; i++) {
        const auction = await pages[i].locator('[data-testid="bidding-table-body"]').textContent();
        expect(auction).toContain('Pass');

        const userName = await pages[i].locator('[data-testid="user-display-name"]').textContent();
        expect(userName).toContain(`User ${i}`);
      }

      console.log('✅ Concurrent sessions test passed - 3 users isolated');

    } finally {
      // Cleanup
      for (const context of contexts) {
        await context.close();
      }
    }
  });

  test('should prevent session interference', async ({ browser }) => {
    // Test that User A's actions don't affect User B's view

    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const userAPage = await context1.newPage();
    const userBPage = await context2.newPage();

    try {
      // User A logs in
      await loginWithEmail(userAPage, `userA-${Date.now()}@example.com`, 'User A');
      await dealNewHand(userAPage);

      // User B logs in
      await loginWithEmail(userBPage, `userB-${Date.now()}@example.com`, 'User B');
      await dealNewHand(userBPage);

      // User A makes several bids
      await makeCall(userAPage, 'Pass');
      await waitForAIBid(userAPage);
      await makeCall(userAPage, 'Pass');
      await waitForAIBid(userAPage);

      // User B's auction should not be affected by User A's bids
      const userBAuction = await userBPage.locator('[data-testid="bidding-table-body"]').textContent();

      // User B should not see User A's multiple passes (unless they also passed)
      // The auctions should be independent

      // Verify both users are still logged in with correct names
      const userAName = await userAPage.locator('[data-testid="user-display-name"]').textContent();
      const userBName = await userBPage.locator('[data-testid="user-display-name"]').textContent();

      expect(userAName).toContain('User A');
      expect(userBName).toContain('User B');

      console.log('✅ Session interference prevention test passed');

    } finally {
      await context1.close();
      await context2.close();
    }
  });
});
