# Weekly Progress Email

**Status:** Planned
**Priority:** Medium
**Created:** 2026-01-02

## Overview

Send weekly progress summary emails to active users to encourage engagement and show improvement over time.

## Target Audience

Users who have played at least one hand in the past week and have an email address on file.

## Proposed Content

### Email Structure

1. **Header**
   - "Your Weekly Bridge Progress"
   - Week date range (e.g., "Dec 25 - Jan 1")

2. **5-Bar Progress Summary** (visual bars like in-app dashboard)
   - Bidding Accuracy: XX%
   - Play Accuracy: XX%
   - Conventions Mastery: XX%
   - Contract Success: XX%
   - Overall Score: XX%

3. **Week-over-Week Trends**
   - Show arrows (↑↓→) comparing to previous week
   - Highlight biggest improvement area
   - Note any areas that declined

4. **Activity Summary**
   - Hands played this week: X
   - Total bids made: X
   - Contracts declared: X (made: X)

5. **Achievements/Milestones** (if any)
   - "You mastered Stayman this week!"
   - "First time making a 4-level contract!"
   - "5-day practice streak!"

6. **Personalized Tip**
   - Based on their weakest area
   - Example: "Your takeout double responses need work. Try the Competitive Bidding scenario."

7. **Call-to-Action**
   - "Continue Practicing" button → app.mybridgebuddy.com

8. **Footer**
   - Unsubscribe link (required for compliance)
   - "Manage email preferences" link

## Technical Requirements

### Database Queries Needed

```sql
-- Find active users from past week
SELECT DISTINCT u.id, u.email, u.display_name
FROM users u
JOIN bidding_decisions bd ON u.id = bd.user_id
WHERE bd.timestamp >= datetime('now', '-7 days')
  AND u.email IS NOT NULL;

-- Get weekly stats for a user
SELECT
  COUNT(*) as total_bids,
  AVG(score) as avg_score,
  SUM(CASE WHEN score >= 8 THEN 1 ELSE 0 END) as optimal_bids
FROM bidding_decisions
WHERE user_id = ?
  AND timestamp >= datetime('now', '-7 days');

-- Get previous week for comparison
SELECT AVG(score) as prev_avg_score
FROM bidding_decisions
WHERE user_id = ?
  AND timestamp >= datetime('now', '-14 days')
  AND timestamp < datetime('now', '-7 days');
```

### Scheduler Options

1. **Cron job on Oracle Cloud** (simplest)
   ```bash
   # Run every Sunday at 9am EST
   0 14 * * 0 cd /opt/bridge-bidding-app/backend && python3 send_weekly_emails.py
   ```

2. **APScheduler in Flask** (runs with app)
   - Pros: No separate process needed
   - Cons: Emails only send when server is running

3. **Manual script** (MVP approach)
   - Run `python3 send_weekly_emails.py` when desired
   - Good for testing before automating

### Email Preferences

Need to add user preferences for email frequency:
- `email_weekly_summary`: boolean (default: true)
- `email_achievements`: boolean (default: true)

Could add to `user_settings` table or create new `email_preferences` table.

## Implementation Steps

1. Create `send_weekly_progress_email()` function in email_service.py
2. Create database queries for weekly stats calculation
3. Design HTML email template (matching welcome email style)
4. Add email preferences to user settings
5. Create `send_weekly_emails.py` script for batch sending
6. Set up cron job on production server
7. Add unsubscribe endpoint `/api/email/unsubscribe`

## Email Template Draft

**Subject:** Your Bridge Progress This Week 🃏

```
Hi {name},

Here's your weekly progress summary for {date_range}:

YOUR PROGRESS
─────────────
Bidding:     ████████░░ 80% (↑5%)
Play:        ██████░░░░ 60% (→)
Conventions: █████████░ 90% (↑10%)
Contracts:   ███████░░░ 70% (↓5%)

THIS WEEK
─────────
🎯 Hands played: 15
📊 Average bid score: 7.8/10
✓ Contracts made: 8/12

HIGHLIGHT
─────────
🌟 Your convention accuracy improved 10% this week!
   Keep practicing Jacoby Transfers.

TIP
───
💡 Your contract success rate dipped slightly.
   Focus on card play in the "Declarer Play" mode.

[Continue Practicing →]

---
The My Bridge Buddy Team

Unsubscribe: {unsubscribe_link}
```

## Future Enhancements

- Monthly summary emails (more detailed)
- Achievement badges in email
- Comparison with community averages
- Personalized practice recommendations
- Re-engagement emails for inactive users (hasn't logged in for 2 weeks)

## Related Files

- `backend/engine/notifications/email_service.py` - Email sending infrastructure
- `backend/server.py` - API endpoints
- `docs/features/FEATURES_SUMMARY.md` - Feature list

## Notes

- Must include unsubscribe option for CAN-SPAM/GDPR compliance
- Consider time zones for send time optimization
- Batch emails to avoid rate limiting (Gmail: 500/day)
- Track email open rates if possible (pixel tracking)
