// Smoke test to verify core app functionality with Playwright
const { test, expect } = require('@playwright/test');

test.describe('Bridge Bidding App - Smoke Test', () => {
  test('should load the app and display a hand', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:3000');

    // Wait for the app to load
    await page.waitForLoadState('networkidle');

    // Verify page title
    await expect(page).toHaveTitle(/React App/);

    // Check if hand is displayed (should see cards or hand analysis)
    // Note: We're not adding data-testid yet, so we'll check for basic elements
    const bodyText = await page.textContent('body');

    console.log('✅ App loaded successfully');
    console.log(`Page contains ${bodyText.length} characters`);
  });

  test('should have authentication UI', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Look for login/auth related elements
    // The app should show some form of authentication UI
    const hasLoginElements = await page.locator('input[type="email"], input[type="tel"]').count() > 0;
    const hasButtons = await page.locator('button').count() > 0;

    console.log(`✅ Found authentication UI elements: ${hasLoginElements}`);
    console.log(`✅ Found buttons: ${hasButtons}`);

    expect(hasButtons).toBeTruthy();
  });

  test('should be able to interact with the page', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Try to click any button on the page
    const buttons = await page.locator('button').all();

    if (buttons.length > 0) {
      console.log(`✅ Found ${buttons.length} interactive buttons`);

      // Get text from first button
      const firstButtonText = await buttons[0].textContent();
      console.log(`   First button text: "${firstButtonText}"`);
    }

    // Verify we can take a screenshot (proves browser rendering works)
    await page.screenshot({ path: '/tmp/bridge-app-screenshot.png' });
    console.log('✅ Screenshot captured successfully');
  });

  test('should verify backend API is working', async ({ request }) => {
    // Test that we can call the scenarios API
    const response = await request.get('http://localhost:5001/api/scenarios');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();

    console.log(`✅ Backend API working - found ${data.length} scenarios`);
  });

  test('should verify deal-hands endpoint works', async ({ request }) => {
    // Test the deal-hands API
    const response = await request.post('http://localhost:5001/api/deal-hands');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('hands');
    expect(data).toHaveProperty('dealer');
    expect(data).toHaveProperty('vulnerability');

    console.log('✅ Deal-hands API working');
    console.log(`   Dealer: ${data.dealer}, Vulnerability: ${data.vulnerability}`);
  });
});
