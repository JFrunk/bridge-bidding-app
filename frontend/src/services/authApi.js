/**
 * Auth V2 API — All authentication endpoint calls.
 *
 * Centralizes auth API communication so AuthContext stays lean.
 * All methods return { success, data?, error? }.
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

/**
 * POST helper with credentials (sends/receives cookies).
 */
async function authPost(endpoint, body = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    return { success: false, status: response.status, error: data.error || 'Request failed' };
  }

  return { success: true, status: response.status, data };
}

// ─── Password Auth ───────────────────────────────────────────

export async function registerUser({ email, password, displayName, guestId }) {
  return authPost('/api/auth/v2/register', {
    email,
    password,
    display_name: displayName,
    guest_id: guestId,
  });
}

export async function loginUser({ email, password }) {
  return authPost('/api/auth/v2/login', { email, password });
}

// ─── Magic Link ──────────────────────────────────────────────

export async function requestMagicLink(email) {
  return authPost('/api/auth/v2/magic-link/request', { email });
}

export async function verifyMagicLink(token) {
  return authPost('/api/auth/v2/magic-link/verify', { token });
}

// ─── Email Verification ─────────────────────────────────────

export async function verifyEmail(token) {
  return authPost('/api/auth/v2/verify-email', { token });
}

export async function resendVerification(email) {
  return authPost('/api/auth/v2/resend-verification', { email });
}

// ─── Password Reset ─────────────────────────────────────────

export async function requestPasswordReset(email) {
  return authPost('/api/auth/v2/forgot-password', { email });
}

export async function resetPassword({ token, password }) {
  return authPost('/api/auth/v2/reset-password', { token, password });
}

// ─── Google OAuth ────────────────────────────────────────────

export async function googleAuth({ idToken, guestId }) {
  return authPost('/api/auth/v2/google', {
    id_token: idToken,
    guest_id: guestId,
  });
}

// ─── Token Management ────────────────────────────────────────

export async function refreshAccessToken() {
  return authPost('/api/auth/refresh');
}

export async function logoutV2() {
  return authPost('/api/auth/logout-v2');
}
