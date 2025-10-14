# Frontend Integration Guide - Common Mistake Detection System

**Status:** Frontend Components Complete ✅
**Last Updated:** 2025-10-13

---

## 📦 What's Included

### Components

1. **LearningDashboard.js** - Main dashboard component
2. **CelebrationNotification.js** - Toast/modal celebration notifications
3. **analyticsService.js** - API service layer

### Files Created

```
frontend/src/
├── services/
│   └── analyticsService.js          # API calls for analytics endpoints
└── components/
    └── learning/
        ├── LearningDashboard.js      # Main dashboard component
        ├── LearningDashboard.css     # Dashboard styles
        ├── CelebrationNotification.js # Celebration notifications
        └── CelebrationNotification.css # Notification styles
```

---

## 🚀 Quick Start

### Step 1: Add Learning Dashboard to Your App

In your main app component (e.g., `App.js`):

```jsx
import React, { useState } from 'react';
import LearningDashboard from './components/learning/LearningDashboard';

function App() {
  const [userId] = useState(1); // Get from auth or create guest user

  const handlePracticeClick = (recommendation) => {
    console.log('Starting practice:', recommendation);
    // Navigate to practice mode with the recommended focus
    // Example: navigate to convention practice with specific category filter
  };

  return (
    <div className="App">
      {/* Your existing app components */}

      {/* Add Learning Dashboard */}
      <LearningDashboard
        userId={userId}
        onPracticeClick={handlePracticeClick}
      />
    </div>
  );
}

export default App;
```

### Step 2: Show Celebrations After Practice

When a user completes a practice hand:

```jsx
import React, { useState, useEffect } from 'react';
import { CelebrationToastContainer } from './components/learning/CelebrationNotification';
import { recordPractice, getCelebrations, acknowledgeCelebration } from './services/analyticsService';

function PracticeMode() {
  const [userId] = useState(1);
  const [pendingCelebrations, setPendingCelebrations] = useState([]);

  const handlePracticeComplete = async (practiceData) => {
    try {
      // Record the practice hand
      const result = await recordPractice({
        user_id: userId,
        convention_id: practiceData.conventionId,
        user_bid: practiceData.userBid,
        correct_bid: practiceData.correctBid,
        was_correct: practiceData.wasCorrect,
        hints_used: practiceData.hintsUsed,
        time_taken_seconds: practiceData.timeTaken
      });

      // Show feedback hint if there's an error
      if (result.feedback && result.feedback.hint) {
        showFeedbackHint(result.feedback.hint);
      }

      // Check for new celebrations
      const celebrationsData = await getCelebrations(userId, true);
      if (celebrationsData.celebrations.length > 0) {
        setPendingCelebrations(celebrationsData.celebrations);
      }

    } catch (error) {
      console.error('Failed to record practice:', error);
    }
  };

  const handleCelebrationClose = async (celebrationId) => {
    try {
      await acknowledgeCelebration(celebrationId);
      setPendingCelebrations(prev =>
        prev.filter(c => c.id !== celebrationId)
      );
    } catch (error) {
      console.error('Failed to acknowledge celebration:', error);
    }
  };

  return (
    <div>
      {/* Your practice mode UI */}

      {/* Celebration notifications */}
      <CelebrationToastContainer
        celebrations={pendingCelebrations}
        onClose={handleCelebrationClose}
      />
    </div>
  );
}
```

### Step 3: Add to Navigation

Add the Learning Dashboard to your navigation:

```jsx
import { Link } from 'react-router-dom';

function Navigation() {
  return (
    <nav>
      <Link to="/">Home</Link>
      <Link to="/practice">Practice</Link>
      <Link to="/learning">My Progress</Link> {/* New link */}
    </nav>
  );
}
```

And add the route:

```jsx
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LearningDashboard from './components/learning/LearningDashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/practice" element={<Practice />} />
        <Route path="/learning" element={<LearningDashboard userId={1} onPracticeClick={handlePracticeClick} />} />
      </Routes>
    </Router>
  );
}
```

---

## 🔌 API Integration Examples

### Recording Practice with Error Categorization

```jsx
import { recordPractice } from './services/analyticsService';

const practiceData = {
  user_id: 1,
  convention_id: 'stayman',
  hand: {
    // Hand data (optional, needed for categorization)
    cards: [/* card objects */]
  },
  user_bid: '2♦',
  correct_bid: '2♣',
  was_correct: false,
  auction_context: {
    // Optional context for better categorization
    vulnerability: { ns: false, ew: false },
    dealer: 'N',
    previous_bids: ['1NT', 'Pass']
  },
  hints_used: 0,
  time_taken_seconds: 45
};

try {
  const result = await recordPractice(practiceData);

  console.log('XP earned:', result.xp_earned);
  console.log('User stats:', result.user_stats);

  if (result.feedback) {
    console.log('Category:', result.feedback.category);
    console.log('Hint:', result.feedback.hint);
    // Display hint to user
    showHintToUser(result.feedback.hint);
  }
} catch (error) {
  console.error('Failed to record practice:', error);
}
```

### Getting Dashboard Data

```jsx
import { getDashboardData } from './services/analyticsService';

const loadDashboard = async () => {
  try {
    const data = await getDashboardData(userId);

    // User stats
    console.log('Level:', data.user_stats.current_level);
    console.log('Streak:', data.user_stats.current_streak);

    // Insights
    console.log('Overall trend:', data.insights.overall_trend);
    console.log('Growth areas:', data.insights.top_growth_areas);
    console.log('Recent wins:', data.insights.recent_wins);

    // Celebrations
    console.log('Pending celebrations:', data.pending_celebrations);

    // Recommendations
    console.log('Practice recommendations:', data.practice_recommendations);

  } catch (error) {
    console.error('Failed to load dashboard:', error);
  }
};
```

### Getting Practice Recommendations

```jsx
import { getPracticeRecommendations } from './services/analyticsService';

const loadRecommendations = async () => {
  try {
    const data = await getPracticeRecommendations(userId, 5);

    data.recommendations.forEach(rec => {
      console.log(`${rec.category_name}: ${rec.reason}`);
      console.log(`  Priority: ${rec.priority}`);
      console.log(`  Recommended hands: ${rec.recommended_hands}`);
      console.log(`  Current accuracy: ${Math.round(rec.accuracy * 100)}%`);
    });

  } catch (error) {
    console.error('Failed to load recommendations:', error);
  }
};
```

---

## 🎨 Component Props Reference

### LearningDashboard

```jsx
<LearningDashboard
  userId={number}              // Required: User ID
  onPracticeClick={function}   // Optional: Callback when "Practice Now" is clicked
                               // Receives: { conventionId, category, recommendedHands }
/>
```

### CelebrationNotification

```jsx
<CelebrationNotification
  celebration={object}         // Required: Celebration object from API
  onClose={function}          // Optional: Callback when closed
  autoClose={boolean}         // Optional: Auto-close notification (default: true)
  autoCloseDelay={number}     // Optional: Delay in ms (default: 5000)
  variant={'toast' | 'modal'} // Optional: Display variant (default: 'toast')
/>
```

**Celebration object structure:**
```javascript
{
  id: 42,
  milestone_type: 'streak_milestone',
  title: '7-Day Streak!',
  message: 'A full week of practice! You\'re dedicated!',
  emoji: '🔥',
  xp_reward: 50,
  achieved_at: '2025-10-13T14:30:00'
}
```

### CelebrationToastContainer

```jsx
<CelebrationToastContainer
  celebrations={array}         // Required: Array of celebration objects
  onClose={function}          // Optional: Callback with celebrationId when closed
/>
```

---

## 🎯 Usage Patterns

### Pattern 1: Dashboard as Main Tab

Show the dashboard as a dedicated tab/page:

```jsx
import LearningDashboard from './components/learning/LearningDashboard';

function LearningPage() {
  const userId = getCurrentUserId();

  const handlePracticeClick = (recommendation) => {
    // Navigate to practice with recommended focus
    navigate('/practice', {
      state: {
        conventionId: recommendation.conventionId,
        category: recommendation.category
      }
    });
  };

  return (
    <div className="page">
      <LearningDashboard userId={userId} onPracticeClick={handlePracticeClick} />
    </div>
  );
}
```

### Pattern 2: Dashboard Widget on Home

Show a condensed dashboard widget on the home page:

```jsx
function HomePage() {
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    getDashboardData(userId).then(setDashboardData);
  }, [userId]);

  return (
    <div>
      {/* Condensed stats widget */}
      {dashboardData && (
        <div className="stats-widget">
          <h3>Your Progress</h3>
          <p>Level {dashboardData.user_stats.current_level}</p>
          <p>{dashboardData.user_stats.current_streak} day streak 🔥</p>
          <Link to="/learning">View Full Dashboard →</Link>
        </div>
      )}
    </div>
  );
}
```

### Pattern 3: Post-Practice Summary

Show insights after completing a practice session:

```jsx
function PracticeSummary({ sessionResults }) {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    // Get updated insights after practice
    getMistakePatterns(userId, 'needs_attention').then(data => {
      setInsights(data);
    });
  }, [sessionResults]);

  return (
    <div className="practice-summary">
      <h2>Practice Complete!</h2>

      {/* Show session results */}
      <div className="results">
        <p>Correct: {sessionResults.correct} / {sessionResults.total}</p>
        <p>XP Earned: +{sessionResults.xpEarned}</p>
      </div>

      {/* Show areas to improve */}
      {insights && insights.patterns.length > 0 && (
        <div className="improvement-tips">
          <h3>Areas to Focus On:</h3>
          {insights.patterns.slice(0, 2).map(pattern => (
            <div key={pattern.id}>
              <p>{pattern.error_category}</p>
              <p>Current accuracy: {Math.round(pattern.current_accuracy * 100)}%</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Pattern 4: Celebration on Achievement

Show immediate celebration when milestone is reached:

```jsx
import CelebrationNotification from './components/learning/CelebrationNotification';

function PracticeSession() {
  const [celebration, setCelebration] = useState(null);

  const checkForCelebrations = async () => {
    const data = await getCelebrations(userId, true);
    if (data.celebrations.length > 0) {
      // Show the first pending celebration as modal
      setCelebration(data.celebrations[0]);
    }
  };

  const handleCelebrationClose = async () => {
    if (celebration) {
      await acknowledgeCelebration(celebration.id);
      setCelebration(null);

      // Check for next celebration
      checkForCelebrations();
    }
  };

  return (
    <div>
      {/* Practice UI */}

      {/* Show celebration modal */}
      {celebration && (
        <CelebrationNotification
          celebration={celebration}
          onClose={handleCelebrationClose}
          variant="modal"
          autoClose={false}
        />
      )}
    </div>
  );
}
```

---

## 🎨 Customization

### Styling

All components use CSS files that can be customized:

- **LearningDashboard.css** - Dashboard layout and card styles
- **CelebrationNotification.css** - Notification and modal styles

### Colors

Main colors used (can be customized in CSS):

```css
/* Primary gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Success/wins */
background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);

/* Celebrations */
background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);

/* Needs attention */
border-left-color: #e74c3c;

/* Improving */
border-left-color: #f39c12;

/* Resolved */
border-left-color: #2ecc71;
```

### Component Customization

You can wrap or extend components:

```jsx
import LearningDashboard from './components/learning/LearningDashboard';

function CustomDashboard({ userId }) {
  return (
    <div className="my-custom-wrapper">
      <h1>My Custom Header</h1>
      <LearningDashboard userId={userId} />
      <div className="my-custom-footer">Footer content</div>
    </div>
  );
}
```

---

## 🔧 Advanced Integration

### User Management

If you don't have a user yet, create one:

```jsx
import { createUser, getUserInfo } from './services/analyticsService';

// Create user
const newUser = await createUser({
  username: 'player1',
  email: 'player@example.com',
  display_name: 'Player One'
});

console.log('Created user:', newUser.user_id);

// Get user info
const userInfo = await getUserInfo(newUser.user_id);
console.log('User stats:', userInfo.stats);
console.log('User settings:', userInfo.settings);
```

### Guest User Mode

For users who don't want to create an account:

```jsx
// In your app initialization
let userId = localStorage.getItem('guestUserId');

if (!userId) {
  // Create guest user
  const guestUser = await createUser({
    username: `guest_${Date.now()}`,
    display_name: 'Guest Player'
  });
  userId = guestUser.user_id;
  localStorage.setItem('guestUserId', userId);
}

// Use this userId for all API calls
```

### Running Analysis

Periodically update all pattern statuses:

```jsx
import { runAnalysis } from './services/analyticsService';

// Run analysis (e.g., daily or after significant practice)
const results = await runAnalysis(userId);
console.log('Patterns analyzed:', results.results.patterns_analyzed);
console.log('Patterns resolved:', results.results.resolved_patterns);
```

---

## 🧪 Testing

### Manual Testing Checklist

1. **Dashboard Display**
   - [ ] User stats load correctly
   - [ ] Level and XP progress bar displays
   - [ ] Streak counter shows current streak
   - [ ] Accuracy percentages are correct

2. **Celebrations**
   - [ ] Toast notifications appear bottom-right
   - [ ] Modal celebrations can be opened
   - [ ] Clicking closes notifications
   - [ ] Auto-close works after delay

3. **Growth Areas**
   - [ ] Categories display with correct status
   - [ ] Accuracy percentages are shown
   - [ ] Status badges have correct colors

4. **Practice Recommendations**
   - [ ] Recommendations load and display
   - [ ] Priority levels are correct
   - [ ] "Practice Now" button triggers callback
   - [ ] Recommended hand counts are shown

5. **Recent Wins**
   - [ ] Mastered patterns show up
   - [ ] Improvement percentages display
   - [ ] Status badges are correct

6. **Responsive Design**
   - [ ] Dashboard works on mobile
   - [ ] Cards stack properly on small screens
   - [ ] Notifications don't overflow

### Test with Mock Data

Create a test component with mock data:

```jsx
const mockDashboardData = {
  user_stats: {
    total_xp: 1250,
    current_level: 3,
    xp_to_next_level: 900,
    current_streak: 7,
    total_hands: 120,
    overall_accuracy: 0.78,
    recent_accuracy: 0.85
  },
  insights: {
    total_patterns: 8,
    overall_trend: 'improving',
    top_growth_areas: [
      {
        category: 'wrong_level',
        category_name: 'Bid Level',
        recent_occurrences: 5,
        accuracy: 0.65,
        status: 'needs_attention',
        recommended_hands: 15
      }
    ],
    recent_wins: [
      {
        category: 'wrong_strain',
        category_name: 'Suit Selection',
        accuracy: 0.92,
        improvement_rate: 0.35,
        status: 'resolved'
      }
    ]
  },
  pending_celebrations: [
    {
      id: 1,
      title: '7-Day Streak!',
      message: 'A full week of practice! You\'re dedicated!',
      emoji: '🔥',
      xp_reward: 50
    }
  ],
  practice_recommendations: [
    {
      category_name: 'Bid Level',
      priority: 1,
      reason: 'Let\'s work on Bid Level - you\'re at 65% and improving!',
      recommended_hands: 15,
      accuracy: 0.65
    }
  ]
};

// Use in your component for testing
<LearningDashboard userId={1} onPracticeClick={console.log} />
```

---

## 📚 Further Resources

- [Backend API Documentation](../backend/MISTAKE_DETECTION_QUICKSTART.md)
- [Implementation Status](../IMPLEMENTATION_STATUS.md)
- [Design Document](../COMMON_MISTAKE_SYSTEM_DESIGN.md)

---

## ✅ Integration Checklist

Before going live:

- [ ] Backend database initialized (`schema_user_management.sql`)
- [ ] Backend API endpoints registered in `server.py`
- [ ] Frontend analytics service configured with correct API URL
- [ ] LearningDashboard component added to app
- [ ] CelebrationNotification integrated into practice flow
- [ ] Practice recording updated to use new `/api/practice/record` endpoint
- [ ] Navigation updated to include Learning Dashboard link
- [ ] User management implemented (or guest user fallback)
- [ ] Error handling tested
- [ ] Responsive design verified on mobile
- [ ] Celebrations display correctly
- [ ] Practice recommendations work and navigate correctly

---

**The frontend is ready! Follow this guide to integrate the Common Mistake Detection System into your app.**
