# User Flow Guide - Multi-User Bridge Practice App

## Quick Start

### For New Users
1. Open the app → Login screen appears
2. Choose "Email" or "Phone"
3. Enter your email or phone number
4. Click "Continue" → Account created automatically!
5. Start playing bridge with your personalized dashboard

### For Returning Users
1. Open the app → Automatically logged in!
2. Your progress and stats are preserved
3. Continue where you left off

### For Quick Play (Guest Mode)
1. Open the app → Login screen appears
2. Click "Continue as Guest"
3. Play immediately (uses default guest account)
4. Can login later to preserve progress

---

## What's Tracked Per User

### ✅ Bidding Feedback
- Every bid you make is evaluated
- Correctness rating (optimal, acceptable, suboptimal, error)
- Score 0-10
- Helpful hints for improvement
- Stored forever in your personal history

### ✅ Dashboard Statistics
- **Bidding Quality**: Optimal rate, avg score, error rate
- **Recent Decisions**: Last 10 bids with feedback
- **Gameplay Stats**: Contracts made/failed, declarer success rate (after completing hands)
- **Learning Insights**: Patterns, growth areas, recommendations

### ✅ Session Tracking
- Chicago-style 4-hand sessions
- Score tracking (NS vs EW)
- Current dealer and vulnerability
- Hand completion count

---

## User Scenarios

### Scenario 1: Solo Learner
**You:** Learning bridge on your own
- Login with your email
- Practice bidding and play
- Dashboard shows YOUR progress only
- Come back anytime, progress is saved

### Scenario 2: Multiple Family Members
**Setup:** Dad, Mom, and kids all learning bridge

**Dad:**
- Logs in with dad@family.com
- Sees only his stats and progress

**Mom:**
- Logs in with mom@family.com
- Has separate account and progress
- Her dashboard shows her stats only

**Kids:**
- Can share guest account for quick play
- Or create individual accounts

**Result:** Everyone's progress tracked separately!

### Scenario 3: Guest → Registered User
1. Start as guest (quick play)
2. Make some bids and progress
3. Realize you want to save progress
4. Login with email
5. Future progress saved to your account
   *(Note: Guest session data stays with guest account)*

---

## Data Separation Examples

### Example 1: Two Users Bidding

**User 1 (Alice):**
```
- Email: alice@example.com
- User ID: 2
- Bidding decisions: 25
- Optimal rate: 72%
- Avg score: 8.1
```

**User 2 (Bob):**
```
- Email: bob@example.com
- User ID: 3
- Bidding decisions: 18
- Optimal rate: 65%
- Avg score: 7.4
```

**Dashboard shows:**
- Alice sees her 25 decisions, 72% optimal rate
- Bob sees his 18 decisions, 65% optimal rate
- **No mixing!**

### Example 2: Database View

```sql
-- Alice's data
SELECT * FROM bidding_decisions WHERE user_id = 2;
-- 25 records

-- Bob's data
SELECT * FROM bidding_decisions WHERE user_id = 3;
-- 18 records
```

---

## Frontend Implementation

### How User ID Flows Through App

```javascript
// 1. User logs in
simpleLogin('alice@example.com', 'email')
// Returns: { user_id: 2, email: 'alice@example.com' }

// 2. Stored in context
const { userId } = useAuth();
// userId = 2

// 3. Used in API calls
fetch('/api/evaluate-bid', {
  body: JSON.stringify({
    user_bid: '1NT',
    user_id: userId,  // = 2
    ...
  })
})

// 4. Backend saves with user_id
INSERT INTO bidding_decisions (user_id, ...) VALUES (2, ...);

// 5. Dashboard queries user's data
fetch(`/api/analytics/dashboard?user_id=${userId}`)
// Returns ONLY user 2's data
```

---

## Session Management

### What Happens When You Play

**1. Start Session:**
```javascript
POST /api/session/start
{ user_id: 2, session_type: 'chicago' }

→ Creates game_session record with user_id=2
→ Returns session_id
```

**2. Make Bids:**
```javascript
POST /api/evaluate-bid
{ user_bid: '1NT', user_id: 2, session_id: 'abc123' }

→ Evaluates bid
→ Stores in bidding_decisions table
→ Links to user_id=2
```

**3. Complete Hand:**
```javascript
POST /api/session/complete-hand
{ score_data: {...}, user_id: 2, session_id: 'abc123' }

→ Saves hand result
→ Updates session stats
→ Links to user's session
```

**4. View Progress:**
```javascript
GET /api/analytics/dashboard?user_id=2

→ Returns bidding stats for user 2
→ Returns gameplay stats for user 2
→ Returns recommendations for user 2
```

---

## Privacy & Data Isolation

### What You See
✅ Your own bidding decisions
✅ Your own gameplay stats
✅ Your own dashboard
✅ Your own session history

### What You DON'T See
❌ Other users' bids
❌ Other users' stats
❌ Other users' progress
❌ Other users' sessions

### Backend Guarantees
- All API endpoints filter by `user_id`
- Database queries include `WHERE user_id = ?`
- No way to access another user's data
- Sessions tied to specific user

---

## Troubleshooting

### "Why is my dashboard empty?"
**Answer:** You need to make some bids first!
1. Click "Deal Hand"
2. Make bidding decisions
3. Dashboard updates in real-time
4. Each bid adds to your statistics

### "I see someone else's data!"
**Check:**
1. Which user are you logged in as?
2. Open browser console: `localStorage.getItem('bridge_user')`
3. Should show YOUR user_id
4. If showing wrong user, logout and login again

### "Where's my old data?"
**If you were using guest mode:**
- Guest data stays with guest account (user_id=1)
- Login to your account to start fresh tracking
- Future data saved to YOUR account

**If you logged in before:**
- Check you're using same email/phone
- Data is preserved forever
- Try logging out and back in

### "Can I have multiple accounts?"
**Yes!**
- Use different emails
- Each gets unique user_id
- Completely separate progress
- Example: Work email vs personal email

---

## Best Practices

### For Solo Users
✅ **Do:** Login with your email
✅ **Do:** Use same email every time
✅ **Do:** Let app remember you (localStorage)
❌ **Don't:** Use guest mode if you want to track progress

### For Families/Teams
✅ **Do:** Each person creates own account
✅ **Do:** Use memorable emails/phones
✅ **Do:** Logout when switching users
❌ **Don't:** Share one account (data will mix)

### For Development/Testing
✅ **Do:** Use test emails (test1@test.com, test2@test.com)
✅ **Do:** Clear localStorage to reset
✅ **Do:** Check database to verify separation
```bash
sqlite3 backend/bridge.db "SELECT user_id, COUNT(*) FROM bidding_decisions GROUP BY user_id;"
```

---

## Technical Details

### Authentication Method
- **Simple Auth**: Email or phone only, no password
- **Why?** Easy onboarding, low friction
- **Security**: Appropriate for learning app
- **Backend API**: `/api/auth/simple-login`

### Data Storage
- **User Data**: `localStorage.bridge_user`
- **Format**: `{id: 2, email: "...", display_name: "..."}`
- **Persistence**: Survives page refresh
- **Cleared**: Only on logout or manual clear

### Database Schema
```sql
-- Users table
users: id, email, phone

-- Bidding decisions (per user)
bidding_decisions: id, user_id, user_bid, optimal_bid, score, ...

-- Game sessions (per user)
game_sessions: id, user_id, hands_completed, ns_score, ew_score, ...

-- Session hands (linked via session → user)
session_hands: id, session_id, score, user_was_declarer, ...
```

---

## Summary

✅ **Each user has:**
- Unique ID in database
- Separate bidding history
- Individual dashboard
- Personal progress tracking
- Isolated sessions

✅ **The app provides:**
- Easy login (email/phone)
- Automatic account creation
- Data persistence
- Privacy (no data mixing)
- Guest mode for quick play

✅ **You can:**
- Track your improvement
- Compare your progress over time
- Switch between users
- Keep data private
- Learn at your own pace

---

**Ready to play?** Login and start making bids! Your dashboard will populate as you play. 🃏
