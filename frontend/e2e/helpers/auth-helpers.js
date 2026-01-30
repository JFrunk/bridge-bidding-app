// Authentication helper functions for E2E tests

/**
 * Ensure no modal is blocking interactions
 * Closes any existing login modal before proceeding
 */
export async function ensureNoModal(page) {
  try {
    const overlay = page.locator('[data-testid="login-overlay"]');
    const isVisible = await overlay.isVisible({ timeout: 1000 }).catch(() => false);

    if (isVisible) {
      await page.click('[data-testid="login-close-button"]');
      await page.waitForSelector('[data-testid="login-overlay"]', { state: 'hidden', timeout: 3000 });
    }
  } catch (e) {
    // No modal present or already closed, continue
  }
}

/**
 * Login as guest user
 */
export async function loginAsGuest(page) {
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('domcontentloaded');

  // Wait for either the modal or the sign-in button to appear (indicates app loaded)
  try {
    const entryPoint = page.locator('[data-testid="login-modal"], [data-testid="sign-in-button"]').first();
    await entryPoint.waitFor({ state: 'visible', timeout: 15000 });
  } catch (e) {
    console.log('⚠️ Timeout waiting for app entry point - continuing anyway');
  }

  // Check if login modal is already visible
  const loginModal = page.locator('[data-testid="login-modal"]');
  const modalVisible = await loginModal.isVisible().catch(() => false);

  if (!modalVisible) {
    // Modal not visible, try clicking sign-in button
    const signInButton = page.locator('[data-testid="sign-in-button"]');
    if (await signInButton.isVisible()) {
      await signInButton.click();
      await page.waitForSelector('[data-testid="login-modal"]', { state: 'visible', timeout: 5000 });
    }
  }

  // Click guest button (handles both "Continue as Guest" and "login-guest-button")
  const guestButton = page.locator('[data-testid="login-guest-button"], button:has-text("Continue as Guest")');
  await guestButton.waitFor({ state: 'visible', timeout: 10000 });
  await guestButton.click({ force: true });

  // Wait for modal to close
  await page.waitForSelector('[data-testid="login-modal"]', { state: 'hidden', timeout: 10000 });
}

/**
 * Login with email
 * Uses direct API call to support custom display_name parameter
 */
export async function loginWithEmail(page, email, displayName = '') {
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('domcontentloaded');

  // Use API call directly to support display_name parameter
  const loginData = {
    email: email,
    create_if_not_exists: true
  };

  if (displayName) {
    loginData.display_name = displayName;
  }

  await page.evaluate(async (data) => {
    const response = await fetch('http://localhost:5001/api/auth/simple-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    // Store in localStorage to simulate login
    const userData = {
      id: result.user_id,
      email: result.email,
      phone: result.phone,
      display_name: result.display_name,
      isGuest: false
    };

    localStorage.setItem('bridge_user', JSON.stringify(userData));
  }, loginData);

  // Reload to apply login
  await page.reload();
  await page.waitForLoadState('domcontentloaded');

  // Verify logged in
  await page.waitForSelector('[data-testid="user-menu"]', { state: 'visible', timeout: 5000 });
}

/**
 * Login with phone number
 * Uses direct API call to support custom display_name parameter
 */
export async function loginWithPhone(page, phone, displayName = '') {
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('domcontentloaded');

  // Use API call directly to support display_name parameter
  const loginData = {
    phone: phone,
    create_if_not_exists: true
  };

  if (displayName) {
    loginData.display_name = displayName;
  }

  await page.evaluate(async (data) => {
    const response = await fetch('http://localhost:5001/api/auth/simple-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    // Store in localStorage to simulate login
    const userData = {
      id: result.user_id,
      email: result.email,
      phone: result.phone,
      display_name: result.display_name,
      isGuest: false
    };

    localStorage.setItem('bridge_user', JSON.stringify(userData));
  }, loginData);

  // Reload to apply login
  await page.reload();
  await page.waitForLoadState('domcontentloaded');

  // Verify logged in
  await page.waitForSelector('[data-testid="user-menu"]', { state: 'visible', timeout: 5000 });
}

/**
 * Logout current user
 */
export async function logout(page) {
  // Open user menu
  await page.click('[data-testid="user-menu-trigger"]');
  // Click logout button in menu
  await page.click('[data-testid="user-menu-logout"]');

  // Verify logged out
  await page.waitForSelector('[data-testid="sign-in-button"]', { state: 'visible' });
}

/**
 * Get current user's display name
 */
export async function getUserDisplayName(page) {
  const displayName = await page.locator('[data-testid="user-display-name"]').textContent();
  return displayName.replace('👤 ', '').trim();
}
