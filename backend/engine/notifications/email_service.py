"""
Email notification service for Bridge Bidding App.
Sends email notifications for review requests using Gmail SMTP.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional


class EmailService:
    """Email service using Gmail SMTP."""

    def __init__(self):
        """Initialize email service with environment variables."""
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')  # Gmail App Password
        self.recipient_email = os.getenv('EMAIL_RECIPIENT', self.sender_email)
        self.app_url = os.getenv('APP_URL', 'http://localhost:5001')

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.sender_email and self.sender_password)

    def send_review_request_notification(self, review_data: Dict[str, Any], filename: str) -> bool:
        """
        Send email notification for a new review request.

        Args:
            review_data: The review request data
            filename: The filename of the saved review request

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            print("⚠️  Email not configured - skipping notification")
            return False

        try:
            subject = self._build_subject(review_data)
            html_body = self._build_html_body(review_data, filename)
            text_body = self._build_text_body(review_data, filename)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())

            print(f"✅ Email notification sent for review request: {filename}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email notification: {e}")
            return False

    def _build_subject(self, review_data: Dict[str, Any]) -> str:
        """Build email subject line."""
        phase = review_data.get('game_phase', 'unknown')
        timestamp = review_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                date_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = timestamp[:16]
        else:
            date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        return f"🃏 Bridge Review Request ({phase}) - {date_str}"

    def _format_hand(self, hand_data: Dict[str, Any]) -> str:
        """Format a hand for display."""
        cards = hand_data.get('cards', [])
        points = hand_data.get('points', {})

        # Group cards by suit
        suits = {'♠': [], '♥': [], '♦': [], '♣': []}
        for card in cards:
            suit = card.get('suit', '')
            rank = card.get('rank', '')
            if suit in suits:
                suits[suit].append(rank)

        # Format each suit
        lines = []
        for suit in ['♠', '♥', '♦', '♣']:
            cards_in_suit = suits.get(suit, [])
            if cards_in_suit:
                # Sort by rank (A, K, Q, J, T, 9, 8, ...)
                rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
                cards_in_suit.sort(key=lambda r: rank_order.get(r, int(r) if r.isdigit() else 0), reverse=True)
                lines.append(f"{suit} {''.join(cards_in_suit)}")
            else:
                lines.append(f"{suit} -")

        hcp = points.get('hcp', 0)
        total = points.get('total_points', hcp)

        return '\n'.join(lines) + f"\n({hcp} HCP, {total} total)"

    def _format_auction(self, auction: list) -> str:
        """Format auction history."""
        if not auction:
            return "No bids yet"

        lines = []
        positions = ['North', 'East', 'South', 'West']

        for i, bid_data in enumerate(auction):
            pos = positions[i % 4]
            bid = bid_data.get('bid', '?')
            explanation = bid_data.get('explanation', '')
            # Truncate long explanations
            if len(explanation) > 100:
                explanation = explanation[:97] + "..."
            lines.append(f"{pos}: {bid}")
            if explanation:
                lines.append(f"  → {explanation}")

        return '\n'.join(lines)

    def _build_text_body(self, review_data: Dict[str, Any], filename: str) -> str:
        """Build plain text email body."""
        user_concern = review_data.get('user_concern', 'No specific concern noted')
        game_phase = review_data.get('game_phase', 'unknown')
        vulnerability = review_data.get('vulnerability', 'None')
        dealer = review_data.get('dealer', 'N')
        user_position = review_data.get('user_position', 'South')

        # Format hands
        all_hands = review_data.get('all_hands', {})
        hands_text = ""
        for position in ['North', 'East', 'South', 'West']:
            hand = all_hands.get(position, {})
            if hand:
                hands_text += f"\n{position}:\n{self._format_hand(hand)}\n"

        # Format auction
        auction = review_data.get('auction', [])
        auction_text = self._format_auction(auction)

        body = f"""
NEW BRIDGE REVIEW REQUEST
========================

User's Concern:
{user_concern}

Game Details:
- Phase: {game_phase}
- Dealer: {dealer}
- Vulnerability: {vulnerability}
- User Position: {user_position}

HANDS:
{hands_text}

AUCTION:
{auction_text}

---
View all review requests: {self.app_url}/api/admin/review-requests
Request file: {filename}
"""

        # Add play data if present
        play_data = review_data.get('play_data')
        if play_data:
            contract = play_data.get('contract', {})
            body += f"""
PLAY DATA:
- Contract: {contract.get('string', 'Unknown')}
- Declarer: {contract.get('declarer', 'Unknown')}
- Tricks NS: {play_data.get('tricks_taken_ns', 0)}
- Tricks EW: {play_data.get('tricks_taken_ew', 0)}
"""

        return body

    def _build_html_body(self, review_data: Dict[str, Any], filename: str) -> str:
        """Build HTML email body."""
        user_concern = review_data.get('user_concern', 'No specific concern noted')
        game_phase = review_data.get('game_phase', 'unknown')
        vulnerability = review_data.get('vulnerability', 'None')
        dealer = review_data.get('dealer', 'N')
        user_position = review_data.get('user_position', 'South')

        # Format hands as HTML
        all_hands = review_data.get('all_hands', {})
        hands_html = ""
        for position in ['North', 'East', 'South', 'West']:
            hand = all_hands.get(position, {})
            if hand:
                hand_text = self._format_hand(hand).replace('\n', '<br>')
                marker = " 👤" if position == user_position else ""
                hands_html += f"""
                <div style="flex: 1; min-width: 150px; padding: 10px; background: #f5f5f5; border-radius: 8px; margin: 5px;">
                    <strong>{position}{marker}</strong><br>
                    <pre style="font-family: monospace; margin: 5px 0;">{hand_text}</pre>
                </div>
                """

        # Format auction as HTML
        auction = review_data.get('auction', [])
        auction_html = ""
        positions = ['North', 'East', 'South', 'West']
        for i, bid_data in enumerate(auction):
            pos = positions[i % 4]
            bid = bid_data.get('bid', '?')
            explanation = bid_data.get('explanation', '')
            if len(explanation) > 100:
                explanation = explanation[:97] + "..."
            auction_html += f"""
            <tr>
                <td style="padding: 5px; border-bottom: 1px solid #eee;"><strong>{pos}</strong></td>
                <td style="padding: 5px; border-bottom: 1px solid #eee; font-size: 18px;">{bid}</td>
                <td style="padding: 5px; border-bottom: 1px solid #eee; color: #666; font-size: 12px;">{explanation}</td>
            </tr>
            """

        # Play data section
        play_html = ""
        play_data = review_data.get('play_data')
        if play_data:
            contract = play_data.get('contract', {})
            play_html = f"""
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px;">
                <h3 style="margin-top: 0;">🎴 Play Data</h3>
                <p><strong>Contract:</strong> {contract.get('string', 'Unknown')}</p>
                <p><strong>Declarer:</strong> {contract.get('declarer', 'Unknown')}</p>
                <p><strong>Tricks:</strong> NS: {play_data.get('tricks_taken_ns', 0)} | EW: {play_data.get('tricks_taken_ew', 0)}</p>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
            <div style="background: #1a5f2a; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">🃏 Bridge Review Request</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Phase: {game_phase.title()} | Dealer: {dealer} | Vuln: {vulnerability}</p>
            </div>

            <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #1a5f2a;">💬 User's Concern</h3>
                    <p style="margin-bottom: 0; font-size: 16px;">{user_concern}</p>
                </div>

                <h3>🎴 Hands</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    {hands_html}
                </div>

                <h3>📋 Auction</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {auction_html if auction_html else '<tr><td>No bids yet</td></tr>'}
                </table>

                {play_html}

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <a href="{self.app_url}/api/admin/review-requests"
                       style="display: inline-block; background: #1a5f2a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        View All Review Requests →
                    </a>
                    <p style="margin-top: 15px; color: #666; font-size: 12px;">
                        Request file: {filename}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get the singleton email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_review_notification(review_data: Dict[str, Any], filename: str) -> bool:
    """
    Convenience function to send a review request notification.

    Args:
        review_data: The review request data
        filename: The filename of the saved review request

    Returns:
        True if email sent successfully, False otherwise
    """
    return get_email_service().send_review_request_notification(review_data, filename)


def send_welcome_email(user_email: str, display_name: str = None) -> bool:
    """
    Send welcome email to new users.

    Args:
        user_email: The user's email address
        display_name: Optional display name for personalization

    Returns:
        True if email sent successfully, False otherwise
    """
    service = get_email_service()
    if not service.is_configured():
        print("⚠️  Email not configured - skipping welcome email")
        return False

    try:
        name = display_name or user_email.split('@')[0]
        created_date = datetime.now().strftime('%B %d, %Y')
        app_url = service.app_url.replace('localhost:5001', 'app.mybridgebuddy.com')
        if 'localhost' in app_url:
            app_url = 'https://app.mybridgebuddy.com'

        subject = "Welcome to My Bridge Buddy! 🃏"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: #1a5f2a; color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">🃏 Welcome to My Bridge Buddy!</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">Your personal bridge training companion</p>
            </div>

            <div style="background: white; border: 1px solid #ddd; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
                <p style="font-size: 18px; color: #333;">Hi {name},</p>

                <p style="font-size: 16px; color: #555; line-height: 1.6;">
                    Thanks for joining <strong>My Bridge Buddy</strong> - your personal bridge training companion!
                </p>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h3 style="margin-top: 0; color: #1a5f2a; font-size: 18px;">What You Can Do:</h3>

                    <p style="margin: 12px 0; font-size: 15px; color: #444;">
                        🎯 <strong>Practice Bidding</strong><br>
                        <span style="color: #666; font-size: 14px;">Learn the Standard American Yellow Card (SAYC) system with real-time feedback on every bid.</span>
                    </p>

                    <p style="margin: 12px 0; font-size: 15px; color: #444;">
                        🤖 <strong>Play Against AI</strong><br>
                        <span style="color: #666; font-size: 14px;">Complete hands against AI opponents at adjustable difficulty levels.</span>
                    </p>

                    <p style="margin: 12px 0; font-size: 15px; color: #444;">
                        📊 <strong>Track Your Progress</strong><br>
                        <span style="color: #666; font-size: 14px;">View your dashboard to see bidding accuracy, common mistakes, and improvement over time.</span>
                    </p>

                    <p style="margin: 12px 0; font-size: 15px; color: #444;">
                        📚 <strong>Learn Conventions</strong><br>
                        <span style="color: #666; font-size: 14px;">Master Stayman, Jacoby Transfers, Blackwood, and more with guided scenarios.</span>
                    </p>
                </div>

                <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h3 style="margin-top: 0; color: #1a5f2a; font-size: 16px;">Your Account</h3>
                    <p style="margin: 5px 0; font-size: 14px; color: #555;">
                        <strong>Email:</strong> {user_email}<br>
                        <strong>Created:</strong> {created_date}
                    </p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{app_url}"
                       style="display: inline-block; background: #1a5f2a; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                        Start Playing →
                    </a>
                </div>

                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; font-size: 14px; color: #856404;">
                        💡 <strong>Tip:</strong> Keep this email! If you ever forget which email you used to sign up,
                        just search your inbox for "Bridge Buddy" to find it.
                    </p>
                </div>

                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #2196f3;">
                    <p style="margin: 0; font-size: 14px; color: #0d47a1;">
                        🤝 <strong>Share the Love:</strong> Know someone who wants to improve their bridge game?
                        Forward this email or share the link: <a href="{app_url}" style="color: #1a5f2a;">{app_url}</a>
                    </p>
                </div>

                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

                <p style="font-size: 16px; color: #333; margin-bottom: 5px;">Happy bidding!</p>
                <p style="font-size: 14px; color: #666; margin-top: 0;"><strong>The My Bridge Buddy Team</strong></p>

                <p style="font-size: 12px; color: #999; margin-top: 20px;">
                    Questions or feedback? Just reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
WELCOME TO MY BRIDGE BUDDY!
===========================

Hi {name},

Thanks for joining My Bridge Buddy - your personal bridge training companion!

WHAT YOU CAN DO:

🎯 Practice Bidding
Learn the Standard American Yellow Card (SAYC) system with real-time feedback on every bid.

🤖 Play Against AI
Complete hands against AI opponents at adjustable difficulty levels.

📊 Track Your Progress
View your dashboard to see bidding accuracy, common mistakes, and improvement over time.

📚 Learn Conventions
Master Stayman, Jacoby Transfers, Blackwood, and more with guided scenarios.

---

YOUR ACCOUNT:

Email: {user_email}
Created: {created_date}

Return to the app anytime: {app_url}

---

💡 TIP: Keep this email! If you ever forget which email you used to sign up,
just search your inbox for "Bridge Buddy" to find it.

---

🤝 SHARE THE LOVE:

Know someone who wants to improve their bridge game?
Forward this email or share the link: {app_url}

---

Happy bidding!
The My Bridge Buddy Team

Questions or feedback? Just reply to this email.
"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = service.sender_email
        msg['To'] = user_email
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(service.smtp_server, service.smtp_port) as server:
            server.starttls()
            server.login(service.sender_email, service.sender_password)
            server.sendmail(service.sender_email, user_email, msg.as_string())

        print(f"✅ Welcome email sent to: {user_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        return False


def send_feedback_notification(feedback_data: Dict[str, Any], filename: str) -> bool:
    """
    Send email notification for general user feedback.

    Args:
        feedback_data: The feedback data
        filename: The filename of the saved feedback

    Returns:
        True if email sent successfully, False otherwise
    """
    service = get_email_service()
    if not service.is_configured():
        print("⚠️  Email not configured - skipping feedback notification")
        return False

    try:
        feedback_type = feedback_data.get('feedback_type', 'unknown')
        description = feedback_data.get('description', 'No description')
        context = feedback_data.get('context', 'unknown')
        timestamp = feedback_data.get('timestamp', '')

        # Build email
        subject = f"📝 Bridge Feedback ({feedback_type}) - {context}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #0077be; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">📝 User Feedback</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Type: {feedback_type} | Context: {context}</p>
            </div>
            <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #0077be;">💬 Feedback</h3>
                    <p style="margin-bottom: 0; font-size: 16px;">{description or 'No description provided'}</p>
                </div>
                <p style="color: #666; font-size: 12px;">
                    Timestamp: {timestamp}<br>
                    File: {filename}
                </p>
                <div style="margin-top: 20px;">
                    <a href="{service.app_url}/api/admin/review-requests"
                       style="display: inline-block; background: #0077be; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px;">
                        View All Requests →
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
USER FEEDBACK
=============
Type: {feedback_type}
Context: {context}
Timestamp: {timestamp}

Description:
{description}

File: {filename}
"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = service.sender_email
        msg['To'] = service.recipient_email
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(service.smtp_server, service.smtp_port) as server:
            server.starttls()
            server.login(service.sender_email, service.sender_password)
            server.sendmail(service.sender_email, service.recipient_email, msg.as_string())

        print(f"✅ Feedback email notification sent: {filename}")
        return True

    except Exception as e:
        print(f"❌ Failed to send feedback email: {e}")
        return False
