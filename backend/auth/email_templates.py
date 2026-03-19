"""
Auth email templates — HTML + plain text for transactional auth emails.

Per AUTH_PRD §7:
- Email Verification (24h expiry)
- Magic Link (15min expiry)
- Password Reset (1h expiry)
- Password Changed notification
"""


def _wrap_html(title: str, content: str) -> str:
    """Wrap content in the standard My Bridge Buddy email template."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
             max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
  <div style="background: #1a5f2a; color: white; padding: 24px; border-radius: 12px 12px 0 0;
              text-align: center;">
    <h1 style="margin: 0; font-size: 24px;">{title}</h1>
  </div>
  <div style="background: white; border: 1px solid #ddd; border-top: none; padding: 28px;
              border-radius: 0 0 12px 12px;">
    {content}
    <hr style="border: none; border-top: 1px solid #eee; margin: 28px 0;">
    <p style="font-size: 12px; color: #999; text-align: center;">
      My Bridge Buddy &mdash; Your personal bridge training companion
    </p>
  </div>
</body>
</html>"""


def _button(url: str, label: str) -> str:
    """Render a CTA button."""
    return f"""<div style="text-align: center; margin: 28px 0;">
      <a href="{url}"
         style="display: inline-block; background: #1a5f2a; color: white;
                padding: 14px 36px; text-decoration: none; border-radius: 8px;
                font-weight: bold; font-size: 16px;">{label}</a>
    </div>"""


# ─── Email Verification ──────────────────────────────────────


def verification_email(app_url: str, token: str, display_name: str = '') -> dict:
    """Build email verification email. Returns dict with subject, html, text."""
    verify_url = f"{app_url}/auth/verify?token={token}"
    name = display_name or 'there'

    html = _wrap_html("Verify Your Email", f"""
    <p style="font-size: 16px; color: #333;">Hi {name},</p>
    <p style="font-size: 15px; color: #555; line-height: 1.6;">
      Thanks for creating an account with My Bridge Buddy!
      Please verify your email address to secure your account.
    </p>
    {_button(verify_url, "Verify Email Address")}
    <p style="font-size: 13px; color: #888; text-align: center;">
      This link expires in 24 hours.<br>
      If you didn't create this account, you can safely ignore this email.
    </p>
    <p style="font-size: 12px; color: #aaa; word-break: break-all;">
      Or copy this link: {verify_url}
    </p>""")

    text = f"""Hi {name},

Thanks for creating an account with My Bridge Buddy!
Please verify your email by visiting this link:

{verify_url}

This link expires in 24 hours.
If you didn't create this account, you can safely ignore this email.

— My Bridge Buddy"""

    return {
        'subject': 'Verify your email — My Bridge Buddy',
        'html': html,
        'text': text,
    }


# ─── Magic Link ──────────────────────────────────────────────


def magic_link_email(app_url: str, token: str) -> dict:
    """Build magic link login email. Returns dict with subject, html, text."""
    magic_url = f"{app_url}/auth/magic?token={token}"

    html = _wrap_html("Your Login Link", f"""
    <p style="font-size: 16px; color: #333;">Hi,</p>
    <p style="font-size: 15px; color: #555; line-height: 1.6;">
      Click the button below to sign in to My Bridge Buddy.
      No password needed.
    </p>
    {_button(magic_url, "Sign In to My Bridge Buddy")}
    <p style="font-size: 13px; color: #888; text-align: center;">
      This link expires in 15 minutes and can only be used once.<br>
      If you didn't request this, you can safely ignore this email.
    </p>
    <p style="font-size: 12px; color: #aaa; word-break: break-all;">
      Or copy this link: {magic_url}
    </p>""")

    text = f"""Hi,

Click this link to sign in to My Bridge Buddy:

{magic_url}

This link expires in 15 minutes and can only be used once.
If you didn't request this, you can safely ignore this email.

— My Bridge Buddy"""

    return {
        'subject': 'Your login link — My Bridge Buddy',
        'html': html,
        'text': text,
    }


# ─── Password Reset ──────────────────────────────────────────


def password_reset_email(app_url: str, token: str) -> dict:
    """Build password reset email. Returns dict with subject, html, text."""
    reset_url = f"{app_url}/auth/reset-password?token={token}"

    html = _wrap_html("Reset Your Password", f"""
    <p style="font-size: 16px; color: #333;">Hi,</p>
    <p style="font-size: 15px; color: #555; line-height: 1.6;">
      We received a request to reset your password. Click the button
      below to choose a new one.
    </p>
    {_button(reset_url, "Reset Password")}
    <p style="font-size: 13px; color: #888; text-align: center;">
      This link expires in 1 hour.<br>
      If you didn't request a password reset, you can safely ignore this email.
      Your password will remain unchanged.
    </p>
    <p style="font-size: 12px; color: #aaa; word-break: break-all;">
      Or copy this link: {reset_url}
    </p>""")

    text = f"""Hi,

We received a request to reset your password. Visit this link to choose a new one:

{reset_url}

This link expires in 1 hour.
If you didn't request a password reset, you can safely ignore this email.
Your password will remain unchanged.

— My Bridge Buddy"""

    return {
        'subject': 'Reset your password — My Bridge Buddy',
        'html': html,
        'text': text,
    }


# ─── Password Changed Notification ───────────────────────────


def password_changed_email() -> dict:
    """Build password changed notification. Returns dict with subject, html, text."""

    html = _wrap_html("Password Changed", """
    <p style="font-size: 16px; color: #333;">Hi,</p>
    <p style="font-size: 15px; color: #555; line-height: 1.6;">
      Your My Bridge Buddy password was successfully changed.
    </p>
    <div style="background: #fff3cd; padding: 15px; border-radius: 8px;
                border-left: 4px solid #ffc107; margin: 20px 0;">
      <p style="margin: 0; font-size: 14px; color: #856404;">
        If you did not make this change, please contact us immediately
        by replying to this email.
      </p>
    </div>""")

    text = """Hi,

Your My Bridge Buddy password was successfully changed.

If you did not make this change, please contact us immediately
by replying to this email.

— My Bridge Buddy"""

    return {
        'subject': 'Password changed — My Bridge Buddy',
        'html': html,
        'text': text,
    }
