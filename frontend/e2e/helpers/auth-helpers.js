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
  await page.waitForLoadState('networkidle');

  // Check if login modal is already visible (auto-shows on app load)
  const loginModal = page.locator('[data-testid="login-modal"]');
  const modalVisible = await loginModal.isVisible({ timeout: 2000 }).catch(() => false);

  if (!modalVisible) {
    // Modal not visible, try clicking sign-in button
    const signInButton = page.locator('[data-testid="sign-in-button"]');
    const buttonExists = await signInButton.isVisible({ timeout: 2000 }).catch(() => false);

    if (buttonExists) {
      await signInButton.click();
      await page.waitForSelector('[data-testid="login-modal"]', { state: 'visible' });
    }
  }

  // Click guest button (handles both "Continue as Guest" and "login-guest-button")
  const guestButton = page.locator('[data-testid="login-guest-button"], button:has-text("Continue as Guest")');
  await guestButton.click();

  // Wait for modal to close
  await page.waitForSelector('[data-testid="login-modal"]', { state: 'hidden', timeout: 5000 });
}

/**
 * Login with email
 * Uses direct API call to support custom display_name parameter
 */
export async function loginWithEmail(page, email, displayName = '') {
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');

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
  await page.waitForLoadState('networkidle');

  // Verify logged in
  await page.waitForSelector('[data-testid="user-menu"]', { state: 'visible', timeout: 5000 });
}

/**
 * Login with phone number
 * Uses direct API call to support custom display_name parameter
 */
export async function loginWithPhone(page, phone, displayName = '') {
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');

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
  await page.waitForLoadState('networkidle');

  // Verify logged in
  await page.waitForSelector('[data-testid="user-menu"]', { state: 'visible', timeout: 5000 });
}

/**
 * Logout current user
 */
export async function logout(page) {
  await page.click('[data-testid="logout-button"]');

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
