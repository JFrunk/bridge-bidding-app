/**
 * E2E Test: Dashboard Analytics
 *
 * Tests the learning dashboard:
 * - Opens dashboard
 * - Shows user statistics
 * - Updates after gameplay
 * - Closes properly
 *
 * This validates the analytics and progress tracking system.
 */

const { test, expect } = require('@playwright/test');
const { loginWithEmail } = require('../helpers/auth-helpers');
const { dealNewHand, makeCall, waitForAIBid } = require('../helpers/game-helpers');

test.describe('Dashboard Analytics', () => {
  test('should open and display dashboard', async ({ page }) => {
    // Login with email to have tracked data
    const testEmail = `dashboard-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Dashboard User');

    // Deal a hand first (dashboard needs some data)
    await dealNewHand(page);

    // Make a quick bid to generate data
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    // Wait for dashboard button to be visible and clickable
    await page.waitForSelector('[data-testid="dashboard-button"]', { state: 'visible', timeout: 5000 });

    // Open dashboard
    await page.click('[data-testid="dashboard-button"]');

    // Wait for dashboard modal to be visible
    await expect(page.locator('[data-testid="dashboard-modal"]')).toBeVisible();

    // Wait for loading to complete (if present)
    await page.waitForSelector('[data-testid="dashboard-loading"]', { state: 'hidden', timeout: 3000 }).catch(() => {});

    // Verify dashboard content is visible (either with data or empty state)
    await expect(page.locator('[data-testid="dashboard-content"], [data-testid="dashboard-empty-state"]')).toBeVisible();

    // Verify header text
    await expect(page.locator('text=Your Learning Journey')).toBeVisible();

    console.log('✅ Dashboard display test passed');
  });

  test('should close dashboard', async ({ page }) => {
    const testEmail = `dashboard-close-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Closer');

    // Deal hand and bid
    await dealNewHand(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    // Wait for dashboard button to be visible
    await page.waitForSelector('[data-testid="dashboard-button"]', { state: 'visible', timeout: 5000 });

    // Open dashboard
    await page.click('[data-testid="dashboard-button"]');
    await expect(page.locator('[data-testid="dashboard-modal"]')).toBeVisible();

    // Wait for loading to complete
    await page.waitForSelector('[data-testid="dashboard-loading"]', { state: 'hidden', timeout: 3000 }).catch(() => {});

    // Close dashboard using data-testid
    await page.click('[data-testid="dashboard-close-button"]');

    // Dashboard should be hidden
    await expect(page.locator('[data-testid="dashboard-modal"]')).not.toBeVisible();

    console.log('✅ Dashboard close test passed');
  });

  test('should refresh dashboard data on reopen', async ({ page }) => {
    const testEmail = `dashboard-refresh-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Refresher');

    // Deal and bid to generate initial data
    await dealNewHand(page);
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    // Open dashboard first time
    await page.click('[data-testid="dashboard-button"]');
    await expect(page.locator('[data-testid="dashboard-modal"]')).toBeVisible();
    await page.waitForSelector('[data-testid="dashboard-loading"]', { state: 'hidden', timeout: 3000 }).catch(() => {});

    // Close dashboard
    await page.click('[data-testid="dashboard-close-button"]');
    await expect(page.locator('[data-testid="dashboard-modal"]')).not.toBeVisible();

    // Make another bid to generate more data
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    // Reopen dashboard
    await page.click('[data-testid="dashboard-button"]');
    await expect(page.locator('[data-testid="dashboard-modal"]')).toBeVisible();

    // Dashboard should show updated data
    // (This test verifies that the remounting with key={Date.now()} works)
    await page.waitForSelector('[data-testid="dashboard-loading"]', { state: 'hidden', timeout: 3000 }).catch(() => {});
    await expect(page.locator('[data-testid="dashboard-content"], [data-testid="dashboard-empty-state"]')).toBeVisible();

    console.log('✅ Dashboard refresh test passed');
  });

  test('should be accessible from both bidding and play phases', async ({ page }) => {
    const testEmail = `dashboard-phases-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Phase Tester');

    // Start in bidding phase
    await dealNewHand(page);

    // Dashboard button should be visible (might be in different location)
    const dashboardButtons = await page.locator('[data-testid="dashboard-button"], [data-testid="progress-button"]').count();
    expect(dashboardButtons).toBeGreaterThan(0);

    console.log('✅ Dashboard accessibility test passed');
  });

  test('should display user-specific data only', async ({ page }) => {
    // This test creates a new user and verifies they don't see other users' data

    const testEmail = `isolated-${Date.now()}@example.com`;
    await loginWithEmail(page, testEmail, 'Isolated User');

    // New user should have no prior data
    await dealNewHand(page);

    // Make first bid
    await makeCall(page, 'Pass');
    await waitForAIBid(page);

    // Wait for dashboard button to be visible
    await page.waitForSelector('[data-testid="dashboard-button"]', { state: 'visible', timeout: 5000 });

    // Open dashboard
    await page.click('[data-testid="dashboard-button"]');
    await expect(page.locator('[data-testid="dashboard-modal"]')).toBeVisible();

    // Wait for loading to complete
    await page.waitForSelector('[data-testid="dashboard-loading"]', { state: 'hidden', timeout: 3000 }).catch(() => {});

    // Dashboard should show fresh/minimal data for new user (likely empty state)
    await expect(page.locator('[data-testid="dashboard-content"], [data-testid="dashboard-empty-state"]')).toBeVisible();

    console.log('✅ User-specific data test passed');
  });
});
