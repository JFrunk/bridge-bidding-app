#!/bin/bash
# Usage Statistics for Bridge Bidding App
# Run: ssh oracle-bridge "bash /opt/bridge-bidding-app/deploy/oracle/usage_stats.sh"
# Email: ssh oracle-bridge "bash /opt/bridge-bidding-app/deploy/oracle/usage_stats.sh --email"

LOG_FILE="/var/log/bridge-backend/access.log"
SEND_EMAIL=false

# Parse arguments
if [[ "$1" == "--email" ]]; then
    SEND_EMAIL=true
fi

# Capture all output
generate_report() {
    echo "========================================"
    echo "  Bridge Buddy Usage Stats"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""

    # Total requests today
    TODAY=$(date '+%d/%b/%Y')
    TODAY_REQUESTS=$(sudo grep "$TODAY" "$LOG_FILE" 2>/dev/null | wc -l)
    echo "Requests today: $TODAY_REQUESTS"

    # Unique user IDs today (from user_id= in URLs)
    UNIQUE_USERS_TODAY=$(sudo grep "$TODAY" "$LOG_FILE" 2>/dev/null | grep -oE 'user_id=[0-9]+' | sort -u | wc -l)
    echo "Unique users today: $UNIQUE_USERS_TODAY"

    # User IDs active today
    echo ""
    echo "Active user IDs today:"
    sudo grep "$TODAY" "$LOG_FILE" 2>/dev/null | grep -oE 'user_id=[0-9]+' | sort | uniq -c | sort -rn | head -10

    # Sessions started today
    SESSIONS_TODAY=$(sudo grep "$TODAY" "$LOG_FILE" 2>/dev/null | grep -c "start-session\|deal-hands")
    echo ""
    echo "Game sessions started today: $SESSIONS_TODAY"

    # Hands played today (bids evaluated)
    HANDS_TODAY=$(sudo grep "$TODAY" "$LOG_FILE" 2>/dev/null | grep -c "evaluate-bid\|submit-answer")
    echo "Bids/answers submitted today: $HANDS_TODAY"

    echo ""
    echo "========================================"
    echo "  Last 7 Days Summary"
    echo "========================================"

    for i in 0 1 2 3 4 5 6; do
        DATE=$(date -d "$i days ago" '+%d/%b/%Y' 2>/dev/null || date -v-${i}d '+%d/%b/%Y')
        COUNT=$(sudo grep "$DATE" "$LOG_FILE" 2>/dev/null | wc -l)
        USERS=$(sudo grep "$DATE" "$LOG_FILE" 2>/dev/null | grep -oE 'user_id=[0-9]+' | sort -u | wc -l)
        echo "$DATE: $COUNT requests, $USERS unique users"
    done

    echo ""
    echo "========================================"
    echo "  Database User Stats"
    echo "========================================"

    cd /opt/bridge-bidding-app/backend
    source venv/bin/activate

    python3 << 'PYTHON'
import sqlite3

try:
    conn = sqlite3.connect('bridge.db')
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM users')
    total = cur.fetchone()[0]
    print(f"Total registered users: {total}")

    cur.execute("SELECT COUNT(*) FROM users WHERE date(last_activity) = date('now')")
    today = cur.fetchone()[0]
    print(f"Active today (DB): {today}")

    cur.execute("SELECT COUNT(*) FROM users WHERE last_activity >= date('now', '-7 days')")
    week = cur.fetchone()[0]
    print(f"Active this week: {week}")

    cur.execute("SELECT COUNT(*) FROM users WHERE last_activity >= date('now', '-30 days')")
    month = cur.fetchone()[0]
    print(f"Active this month: {month}")

    cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-7 days')")
    new_week = cur.fetchone()[0]
    print(f"New users this week: {new_week}")

    cur.execute("SELECT COUNT(*) FROM session_hands")
    hands = cur.fetchone()[0]
    print(f"Total hands played: {hands}")

    cur.execute("SELECT COUNT(*) FROM bidding_decisions")
    bids = cur.fetchone()[0]
    print(f"Total bidding decisions: {bids}")

    conn.close()
except Exception as e:
    print(f"Database error: {e}")
PYTHON

    echo ""
    echo "========================================"
}

# Generate and optionally email report
REPORT=$(generate_report)

if [[ "$SEND_EMAIL" == true ]]; then
    cd /opt/bridge-bidding-app/backend
    source venv/bin/activate
    set -a; source .env 2>/dev/null; set +a

    python3 << PYTHON
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

report = '''$REPORT'''

sender = os.getenv('EMAIL_SENDER')
password = os.getenv('EMAIL_PASSWORD')
recipient = os.getenv('EMAIL_RECIPIENT', sender)

if not sender or not password:
    print("ERROR: EMAIL_SENDER and EMAIL_PASSWORD env vars required")
    exit(1)

subject = f"📊 Bridge Buddy Daily Stats - {datetime.now().strftime('%Y-%m-%d')}"

msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = sender
msg['To'] = recipient

# Plain text
msg.attach(MIMEText(report, 'plain'))

# HTML version
html = f"""
<html>
<body style="font-family: monospace; background: #f5f5f5; padding: 20px;">
<div style="background: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
<h2 style="color: #1a5f2a; margin-top: 0;">📊 Bridge Buddy Daily Stats</h2>
<pre style="background: #f8f8f8; padding: 15px; border-radius: 4px; overflow-x: auto;">{report}</pre>
<p style="color: #666; font-size: 12px; margin-bottom: 0;">
<a href="https://app.mybridgebuddy.com">app.mybridgebuddy.com</a>
</p>
</div>
</body>
</html>
"""
msg.attach(MIMEText(html, 'html'))

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print(f"✅ Stats emailed to {recipient}")
except Exception as e:
    print(f"❌ Email failed: {e}")
PYTHON

else
    echo "$REPORT"
fi
