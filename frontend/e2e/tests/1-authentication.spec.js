/**
 * E2E Test: Authentication Flow
 *
 * Tests user authentication including:
 * - Guest login
 * - Email login
 * - Phone login
 * - Logout
 * - Login persistence across page reloads
 */

const { test, expect } = require('@playwright/test');
const { loginAsGuest, loginWithEmail, loginWithPhone, logout, ensureNoModal } = require('../helpers/auth-helpers');

test.describe('Authentication Flow', () => {
  test('should login as guest', async ({ page }) => {
    await loginAsGuest(page);

    // Verify guest user is logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-display-name"]')).toContainText('Guest');
  });

  test('should login with email', async ({ page }) => {
    const testEmail = `test-${Date.now()}@example.com`;
    const displayName = 'Test User';

    await loginWithEmail(page, testEmail, displayName);

    // Verify user is logged in with correct display name
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-display-name"]')).toContainText(displayName);
  });

  test('should login with phone number', async ({ page }) => {
    const testPhone = `${Date.now()}`.slice(-10);
    const displayName = 'Phone User';

    await loginWithPhone(page, testPhone, displayName);

    // Verify user is logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-display-name"]')).toContainText(displayName);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await loginAsGuest(page);

    // Verify logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

    // Logout
    await logout(page);

    // Verify logged out - should see sign in button
    await expect(page.locator('[data-testid="sign-in-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-menu"]')).not.toBeVisible();
  });

  test('should persist login across page reload', async ({ page }) => {
    const testEmail = `persist-${Date.now()}@example.com`;
    const displayName = 'Persistent User';

    // Login
    await loginWithEmail(page, testEmail, displayName);

    // Verify logged in
    await expect(page.locator('[data-testid="user-display-name"]')).toContainText(displayName);

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify still logged in after reload
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-display-name"]')).toContainText(displayName);
  });

  test('should switch between email and phone login methods', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Ensure no modal is blocking
    await ensureNoModal(page);

    // Open login modal
    await page.click('[data-testid="sign-in-button"]');
    await page.waitForSelector('[data-testid="login-modal"]', { state: 'visible' });

    // Default should be email
    await expect(page.locator('[data-testid="login-email-input"]')).toBeVisible();

    // Switch to phone
    await page.click('[data-testid="login-toggle-phone"]');
    await expect(page.locator('[data-testid="login-phone-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-email-input"]')).not.toBeVisible();

    // Switch back to email
    await page.click('[data-testid="login-toggle-email"]');
    await expect(page.locator('[data-testid="login-email-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-phone-input"]')).not.toBeVisible();

    // Close modal
    await page.click('[data-testid="login-close-button"]');
    await expect(page.locator('[data-testid="login-modal"]')).not.toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Ensure no modal is blocking
    await ensureNoModal(page);

    // Open login modal
    await page.click('[data-testid="sign-in-button"]');
    await page.waitForSelector('[data-testid="login-modal"]', { state: 'visible' });

    // Try to submit without email
    await page.click('[data-testid="login-submit-button"]');

    // Browser validation should prevent submission (empty required field)
    // Modal should still be visible
    await expect(page.locator('[data-testid="login-modal"]')).toBeVisible();
  });
});
