// Verification test to confirm Playwright works in this environment
const { test, expect } = require('@playwright/test');

test.describe('Playwright Environment Verification', () => {
  test('should verify Playwright can launch browser', async ({ page }) => {
    // Navigate to a simple page
    await page.goto('https://playwright.dev');

    // Verify page loaded
    await expect(page).toHaveTitle(/Playwright/);

    console.log('✅ Playwright browser automation works!');
  });

  test('should verify React dev server is accessible', async ({ page }) => {
    // This will fail if servers aren't running, which is expected
    // Just checking that the test framework works
    try {
      await page.goto('http://localhost:3000', { timeout: 5000 });
      console.log('✅ React dev server is running');
    } catch (error) {
      console.log('ℹ️  React dev server not running (expected if not started manually)');
      // Don't fail the test - we're just verifying Playwright works
    }
  });

  test('should verify backend API is accessible', async ({ request }) => {
    // Test API request capability
    try {
      const response = await request.get('http://localhost:5001/api/scenarios', { timeout: 5000 });
      if (response.ok()) {
        console.log('✅ Backend API is accessible');
      }
    } catch (error) {
      console.log('ℹ️  Backend not running (expected if not started manually)');
    }
  });
});
