# PRD: Authentication System

**Status:** Draft
**Author:** Simon Roy
**Created:** 2026-03-09
**Target:** v2.x release

---

## 1. Problem Statement

The application currently uses password-less authentication where anyone can log in with any email address — no verification, no credential check. This creates three problems:

1. **No account security.** Any user can access any other user's account by entering their email.
2. **No identity verification.** We cannot confirm users own the email addresses they provide.
3. **No credential standard.** Users expect password-based login or social sign-in from a modern web application. The current "enter your email to log in" flow creates confusion and erodes trust.

### Current State

- Users log in by entering email or phone — auto-creates account if new
- No passwords, no email verification, no OAuth
- Guest mode with persistent negative IDs (works well, keep as-is)
- Sessions are in-memory (lost on server restart)
- User data (progress, stats, bids) is already persisted in PostgreSQL and keyed by `user_id`
- Guest-to-registered migration already works (data transferred on registration)

---

## 2. Goals

| Goal | Metric |
|------|--------|
| Secure user accounts with verified credentials | 100% of new accounts have verified email |
| Provide frictionless login options | Offer password, Google, and magic link |
| Enable account recovery | Password reset via email within 5 minutes |
| Maintain backward compatibility | Existing users can still access their data |
| Keep guest mode intact | No changes to guest flow or guest→registered migration |

### Non-Goals

- Native mobile app authentication (iOS/Android)
- Facebook or Apple OAuth (deferred — see Appendix A)
- Two-factor authentication (future consideration)
- Admin panel / user management dashboard
- Role-based access control

---

## 3. Features

### 3.1 Password Authentication

#### Registration

**Flow:**
1. User navigates to login screen, selects "Create Account"
2. User enters: email, display name, password, confirm password
3. Frontend validates: email format, password strength, password match
4. Backend creates user with `password_hash` (argon2), sets `email_verified = false`
5. Backend sends verification email (see §3.4)
6. User lands on "Check your email" confirmation screen
7. User can begin using the app immediately (unverified), with a persistent banner prompting verification

**Password Requirements:**
- Minimum 8 characters
- At least one letter and one number
- Checked against top-10,000 common passwords list (server-side)
- Strength indicator shown in UI (weak / fair / strong)

**Validation Rules:**
- Email: valid format, unique in `users` table
- Display name: 2-30 characters, no leading/trailing whitespace
- Password: see above

#### Login

**Flow:**
1. User enters email + password
2. Backend verifies credentials against `password_hash`
3. On success: issue JWT access token (15min) + refresh token (30 days, HttpOnly cookie)
4. On failure: generic "Invalid email or password" message (no enumeration)
5. After 5 failed attempts on same email within 15 minutes: temporary 15-minute lockout

**Session Management:**
- Access token: JWT, 15-minute expiry, stored in memory (not localStorage)
- Refresh token: opaque token, 30-day expiry, HttpOnly secure cookie
- Refresh endpoint: `/api/auth/refresh` — issues new access token using valid refresh token
- Logout: invalidate refresh token server-side, clear cookie

---

### 3.2 Google Sign-In

**Flow:**
1. User clicks "Sign in with Google" button on login screen
2. Google Identity Services SDK opens consent popup
3. User authorizes; Google returns ID token to frontend
4. Frontend sends ID token to backend `/api/auth/google`
5. Backend verifies token with Google's public keys
6. If email matches existing user → log in (link Google provider if not already linked)
7. If email is new → create account with `email_verified = true` (Google pre-verifies), `auth_provider = 'google'`
8. Issue JWT access + refresh tokens (same as password login)

**Account Linking:**
- If a user registered with password and later signs in with Google using the same email → accounts are linked automatically
- The user can then log in with either method
- `auth_providers` table tracks which providers are linked to each user

**Google Setup Requirements:**
- Google Cloud Console project with OAuth 2.0 credentials
- Authorized redirect URIs for production and development
- OAuth consent screen (external, unverified is fine for <100 users; submit for verification before scaling)
- Client ID exposed to frontend; client secret stays on backend

**Data from Google:**
- Email (verified)
- Display name
- Profile picture URL (store URL, don't download)
- Google user ID (stored as `provider_id`)

---

### 3.3 Magic Link Login

**Flow:**
1. User selects "Email me a login link" on login screen
2. User enters email address
3. Backend generates a single-use token (cryptographically random, 64 chars)
4. Backend stores token with 15-minute expiry and user_id association
5. Backend sends email containing magic link: `https://app.mybridgebuddy.com/auth/magic?token=xxx`
6. User clicks link → frontend sends token to `/api/auth/magic-verify`
7. Backend validates token (exists, not expired, not used) → issues JWT session
8. Token is marked as used (single-use enforcement)

**Edge Cases:**
- If email doesn't match any account → show "If an account exists, we sent a link" (no enumeration)
- If token is expired → show "Link expired, request a new one" with button
- If token is already used → show "Link already used, request a new one"
- Multiple requests → only the latest token is valid (previous ones invalidated)

**Why Magic Link:**
- Replaces the current password-less email login with a *secure* version
- Good UX for users who dislike passwords
- Leverages the email infrastructure already needed for verification and reset

---

### 3.4 Email Verification

**Flow:**
1. After registration (password or magic link — Google is pre-verified), backend sends verification email
2. Email contains link: `https://app.mybridgebuddy.com/auth/verify?token=xxx`
3. Token: single-use, 24-hour expiry
4. User clicks link → frontend sends token to `/api/auth/verify-email`
5. Backend validates → sets `email_verified = true` on user record
6. Frontend shows "Email verified" confirmation

**Unverified User Restrictions:**
- Can use the app fully (play hands, track progress)
- Persistent but dismissable banner: "Verify your email to secure your account"
- Cannot reset password until email is verified
- Banner reappears on each session until verified

**Resend Verification:**
- Button in the banner and in account settings
- Rate limited: 1 per minute, 5 per hour
- Each resend invalidates previous token

---

### 3.5 Password Reset

**Flow:**
1. User clicks "Forgot password?" on login screen
2. User enters email address
3. Backend sends reset email (regardless of whether account exists — no enumeration)
4. Email contains link: `https://app.mybridgebuddy.com/auth/reset-password?token=xxx`
5. Token: single-use, 1-hour expiry
6. User clicks link → frontend shows "Set new password" form
7. User enters new password + confirmation
8. Frontend sends token + new password to `/api/auth/reset-password`
9. Backend validates token, hashes new password, updates `users.password_hash`
10. All existing refresh tokens for this user are invalidated (force re-login on all devices)
11. Frontend redirects to login with success message

**Constraints:**
- Only works for verified email addresses
- New password cannot match the previous password
- Rate limited: 3 reset requests per email per hour

---

## 4. Data Model Changes

### Modified: `users` table

```sql
ALTER TABLE users ADD COLUMN password_hash TEXT;
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN profile_picture_url TEXT;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
```

### New: `auth_providers` table

```sql
CREATE TABLE auth_providers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,              -- 'google', 'password', 'magic_link'
    provider_id TEXT,                    -- External provider's user ID
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider, provider_id)
);
CREATE INDEX idx_auth_providers_user ON auth_providers(user_id);
```

### New: `auth_tokens` table

```sql
CREATE TABLE auth_tokens (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,     -- SHA-256 of the token (never store raw)
    token_type TEXT NOT NULL,            -- 'email_verify', 'password_reset', 'magic_link'
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,                   -- NULL until used
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_auth_tokens_hash ON auth_tokens(token_hash);
CREATE INDEX idx_auth_tokens_user_type ON auth_tokens(user_id, token_type);
```

### New: `refresh_tokens` table

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,     -- SHA-256 of the refresh token
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP                 -- NULL until revoked
);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
```

---

## 5. API Endpoints

### Authentication

| Method | Endpoint | Purpose | Auth Required | Rate Limit |
|--------|----------|---------|---------------|------------|
| POST | `/api/auth/register` | Create account with password | No | 5/hour per IP |
| POST | `/api/auth/login` | Password login | No | 10/min per IP, lockout after 5 failures per email |
| POST | `/api/auth/google` | Google OAuth token exchange | No | 10/min per IP |
| POST | `/api/auth/magic-link` | Request magic link email | No | 3/min per IP |
| POST | `/api/auth/magic-verify` | Verify magic link token | No | 10/min per IP |
| POST | `/api/auth/refresh` | Refresh access token | Refresh cookie | 30/min |
| POST | `/api/auth/logout` | Revoke refresh token | Yes | — |
| POST | `/api/auth/verify-email` | Verify email token | No | 10/min per IP |
| POST | `/api/auth/resend-verification` | Resend verification email | Yes | 1/min, 5/hour |
| POST | `/api/auth/forgot-password` | Request password reset | No | 3/hour per email |
| POST | `/api/auth/reset-password` | Set new password with token | No | 5/hour per IP |

### Account Management

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/api/auth/me` | Get current user profile | Yes |
| PUT | `/api/auth/me` | Update display name, profile | Yes |
| POST | `/api/auth/change-password` | Change password (requires current) | Yes |
| GET | `/api/auth/providers` | List linked auth providers | Yes |
| DELETE | `/api/auth/providers/:provider` | Unlink a provider (must keep ≥1) | Yes |

---

## 6. Frontend Changes

### New Pages/Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/login` | `LoginPage` | Email+password login, Google button, magic link option |
| `/register` | `RegisterPage` | Create account form |
| `/auth/verify` | `VerifyEmailPage` | Email verification landing |
| `/auth/reset-password` | `ResetPasswordPage` | Set new password form |
| `/auth/magic` | `MagicLinkPage` | Magic link verification landing |
| `/account` | `AccountSettingsPage` | Password change, linked providers, email settings |

### Modified Components

| Component | Changes |
|-----------|---------|
| `SimpleLogin.jsx` | Replace with new `LoginPage` — redesigned with tabs for password / magic link, Google button |
| `AuthContext.jsx` | Add JWT management, refresh token rotation, Google auth flow |
| `api.js` | Add Authorization header from JWT, auto-refresh on 401 |
| `App.jsx` | Add new routes, email verification banner |

### Login Screen Layout

```
┌──────────────────────────────────┐
│     🂠 My Bridge Buddy           │
│                                  │
│  ┌────────────┬───────────────┐  │
│  │  Password  │  Magic Link   │  │
│  └────────────┴───────────────┘  │
│                                  │
│  Email         [_____________]   │
│  Password      [_____________]   │
│                                  │
│  [        Sign In           ]    │
│                                  │
│  Forgot password?                │
│                                  │
│  ─────────── or ──────────────   │
│                                  │
│  [G  Sign in with Google    ]    │
│                                  │
│  ─────────────────────────────   │
│  Don't have an account?          │
│  Create one · Continue as guest  │
└──────────────────────────────────┘
```

---

## 7. Email Templates

Four transactional emails required:

| Email | Subject | Token Expiry |
|-------|---------|-------------|
| Email Verification | "Verify your email — My Bridge Buddy" | 24 hours |
| Password Reset | "Reset your password — My Bridge Buddy" | 1 hour |
| Magic Link | "Your login link — My Bridge Buddy" | 15 minutes |
| Password Changed | "Your password was changed — My Bridge Buddy" | N/A (notification only) |

**Template style:** Plain HTML, mobile-friendly, single CTA button, app branding. No tracking pixels.

### Email Transport (Phased)

**Phase 1: Gmail SMTP (launch)**
- Use the dedicated service Gmail account with an App Password
- From address: service Gmail address
- Daily limit: 500 emails/day (sufficient for early user base)
- Setup: Enable 2FA on Gmail → generate App Password → configure `smtplib`
- No external dependencies or DNS changes required
- Deliverability: good for Gmail-to-Gmail; adequate for others at low volume

**Phase 2: Resend (scale trigger: >100 emails/day or deliverability issues)**
- Migrate to Resend API (free tier: 100/day, 3,000/month)
- From address: `noreply@mybridgebuddy.com` (requires SPF + DKIM DNS records)
- Higher deliverability, custom domain, better sender reputation
- Swap is transparent — email sending is abstracted behind a common interface

**Implementation:** All email sending goes through a single `send_email(to, subject, html_body)` function. Phase 1 uses `smtplib` + Gmail SMTP. Phase 2 swaps the implementation to Resend API. No auth or template code changes needed.

---

## 8. Migration Strategy for Existing Users

### Problem
~N existing users have accounts with email/phone but no password and no verified email.

### Approach

1. **No forced migration.** Existing users are not locked out.
2. **On next login attempt via the new login page:**
   - If user enters email that exists but has no password → show prompt: "This account was created before passwords were required. Set a password or use a magic link to sign in."
   - Magic link flow works immediately (sends to their existing email).
   - "Set password" link sends a password-reset-style email to establish first password.
3. **Existing `simple-login` endpoint** kept active for 90 days with deprecation header, then removed.
4. **Guest users** unaffected — guest flow remains identical.
5. **Guest→registered migration** updated to include password in registration payload.

---

## 9. Dependencies

| Dependency | Purpose | Backend/Frontend | Free? |
|------------|---------|-----------------|-------|
| `argon2-cffi` | Password hashing | Backend | Yes |
| `PyJWT` | JWT creation/verification | Backend | Yes |
| `google-auth` | Google ID token verification | Backend | Yes |
| `smtplib` | Gmail SMTP email sending (Phase 1) | Backend | Yes (stdlib) |
| `resend` | Transactional email API (Phase 2) | Backend | Yes (free tier) |
| `@react-oauth/google` | Google Sign-In button | Frontend | Yes |

**Infrastructure:**
- Service Gmail account with 2FA enabled + App Password (Phase 1 email)
- Resend account + DNS records for `mybridgebuddy.com` (Phase 2 email — deferred)
- Google Cloud Console OAuth credentials (client ID + secret)
- `JWT_SECRET` environment variable on production server

---

## 10. Security Requirements

| Requirement | Implementation |
|-------------|---------------|
| Passwords hashed with argon2id | `argon2-cffi` with default params |
| Tokens never stored raw | SHA-256 hash stored in `auth_tokens` table |
| No user enumeration | All "user not found" responses identical to "success" |
| Brute force protection | 5 failed attempts → 15-min lockout per email |
| CSRF protection | SameSite=Strict on cookies + CSRF token for state-changing requests |
| XSS prevention | Tokens in HttpOnly cookies, not localStorage |
| Secure transport | HTTPS enforced (already in place) |
| Token single-use | Magic link and reset tokens marked used after first verification |
| Session revocation | Password reset invalidates all refresh tokens |
| Rate limiting | Per-endpoint limits (see §5) |

---

## 11. Implementation Phases

### Phase 1: Core Infrastructure (Backend)
- Database migrations (new tables + columns)
- Argon2 password hashing utility
- JWT access/refresh token issuance and validation
- Auth token generation (verification, reset, magic link)
- Refresh token rotation endpoint

### Phase 2: Password Auth (Full Stack)
- Registration endpoint + frontend form
- Login endpoint + frontend form
- Password strength validation (shared rules)
- Account lockout on failed attempts

### Phase 3: Email System
- Abstract `send_email()` interface with Gmail SMTP backend (Phase 1 transport)
- Service Gmail App Password configuration (2FA + app-specific password)
- Email verification flow (send + verify endpoint + frontend page)
- Password reset flow (request + reset endpoint + frontend page)
- Password changed notification email
- Verification banner in app shell
- Future: swap `send_email()` implementation to Resend when scale requires it

### Phase 4: Magic Link
- Magic link request endpoint
- Magic link verification endpoint + frontend page
- Token invalidation on new request
- Login page tab for magic link option

### Phase 5: Google Sign-In
- Google Cloud Console setup (OAuth credentials)
- Backend token verification endpoint
- Frontend Google button integration
- Account linking (same email → merged)
- Auth providers management (link/unlink)

### Phase 6: Migration & Cleanup
- Existing user migration prompts
- Account settings page (change password, providers, email)
- Deprecate old `simple-login` endpoint
- Update AuthContext for JWT flow
- Update `api.js` for auto-refresh on 401

---

## 12. Testing Requirements

| Area | Tests |
|------|-------|
| Registration | Valid input, duplicate email, weak password, common password rejection |
| Login | Correct credentials, wrong password, wrong email, locked account, unverified email |
| Password reset | Valid flow, expired token, used token, unverified email rejection |
| Magic link | Valid flow, expired token, used token, multiple requests (only latest valid) |
| Google OAuth | Valid token, invalid token, new user creation, account linking |
| JWT refresh | Valid refresh, expired refresh, revoked refresh |
| Rate limiting | Verify all endpoint limits enforce correctly |
| Migration | Existing user login prompt, password establishment, data continuity |
| E2E | Full registration→verify→login→logout→reset→login flow |

---

## Appendix A: Deferred Providers

### Facebook Login — Not Recommended
- App Review process is slow (weeks) and requires Privacy Policy, Terms of Service
- Meta deprecates SDKs frequently; high maintenance burden
- Declining user trust in Facebook login
- Minimal overlap with bridge player demographics
- Revisit only if user research explicitly demands it

### Apple Sign-In — Conditional
- Requires Apple Developer Program ($99/year)
- Mandatory if the app is published on the iOS App Store with any social login
- Not justified for web-only deployment
- Implement only when/if an iOS native app is built

---

## Appendix B: Future Considerations

- **Two-factor authentication (TOTP)** — Add after password auth is stable
- **Passkeys / WebAuthn** — Modern passwordless standard, consider as magic link upgrade
- **Account deletion** — GDPR compliance, user self-service data export and deletion
- **Session management UI** — Show active sessions, allow remote logout
