# Learning Mode Implementation Plan

**Created:** 2025-12-25
**Status:** Phase 4 Complete (Frontend Ready)
**Last Updated:** 2025-12-27
**Companion Document:** [LEARNING_MODE_CURRICULUM.md](LEARNING_MODE_CURRICULUM.md)

## Progress Summary

| Phase | Status | Commit |
|-------|--------|--------|
| Phase 0: Infrastructure Validation | ✅ Complete | n/a |
| Phase 1: Curriculum Structure | ✅ Complete | `feat(learning): Implement Phase 1` |
| Phase 2: Hand Generation | ✅ Complete | `feat(learning): Implement Phase 2` |
| Phase 3: Learning Mode API | ✅ Complete | `feat(learning): Implement Phase 3` |
| Phase 4: Frontend Learning Mode | ✅ Complete | `feat(learning): Implement Phase 4` |
| Phase 5: Testing & QA | 🔜 In Progress | - |

### Phase 4 Enhancements (2025-12-27)

**Session-Specific Accuracy:**
- Fixed accuracy display to use session stats from `handHistory` instead of cumulative DB stats
- Display shows "this session" accuracy after answering hands
- No longer confusingly shows "0 of 2" on first hand

**Bid Shortcuts with Pass Trap:**
- All 8 bid shortcut scenarios now include Pass as a "trap" option
- Essential for teaching force bids (e.g., 2♣ game-forcing cannot pass)
- Helps users learn when Pass is legal vs illegal

**Educational Feedback Improvements:**
- Replaced generic "combined under 25 points" messages with specific requirements
- Explains Stayman requires 8+ HCP (not just game points)
- Explains transfer usage for weak hands with 5+ card majors
- Added case for 4-card major with weak points (cannot use Stayman)

---

## Guiding Principle: Leverage, Don't Replicate

This project has extensive existing infrastructure that was built but never fully integrated. The implementation plan focuses on **wiring together existing components** rather than building new ones.

---

## Existing Assets Inventory

### Already Complete (DO NOT REBUILD)

| Asset | Location | What It Does |
|-------|----------|--------------|
| **Convention Registry** | `backend/engine/ai/conventions/convention_registry.py` | 17 conventions with metadata, levels, prerequisites, passing criteria |
| **Skill Tree** | `backend/engine/learning/skill_tree.py` | 6-level progression with unlock logic |
| **Learning Path API** | `backend/engine/learning/learning_path_api.py` | 10 endpoints for progress tracking |
| **Analytics API** | `backend/engine/learning/analytics_api.py` | Dashboard, mistakes, recommendations |
| **User Manager** | `backend/engine/learning/user_manager.py` | XP, streaks, gamification |
| **Celebration Manager** | `backend/engine/learning/celebration_manager.py` | Milestone achievements |
| **Error Categorizer** | `backend/engine/learning/error_categorizer.py` | Mistake classification |
| **Mistake Analyzer** | `backend/engine/learning/mistake_analyzer.py` | Pattern detection |
| **Scenario Loader** | `backend/core/scenario_loader.py` | Hand generation for conventions |
| **Frontend Dashboard** | `frontend/src/components/learning/LearningDashboard.js` | Stats display |
| **Frontend Service** | `frontend/src/services/analyticsService.js` | API integration |
| **Database Schema** | `backend/database/schema_convention_levels.sql` | Progress tables |
| **Quality Testing** | `backend/test_bidding_quality_score.py` | Bidding validation |

### Gaps to Fill

| Gap | What's Needed | Approach |
|-----|---------------|----------|
| **Levels 0-4 Topics** | Non-convention fundamentals | Extend skill_tree.py with new topics |
| **Topic Hand Generation** | Hands for fundamentals | Extend hand_constructor.py |
| **Learning Mode UI** | Guided practice flow | New React component using existing services |
| **Interleaved Review** | Mixed-topic sessions | New API endpoint, reuse scenario system |
| **Level Assessment** | Mastery tests | New API endpoint, reuse evaluation |
| **Scorecard View** | Progress visualization | New React component using existing dashboard data |

---

## Implementation Phases

### Phase 0: Validation (1 day)
**Goal:** Confirm existing infrastructure works before building on it

| Task | How to Test | Expected Result |
|------|-------------|-----------------|
| Verify API endpoints registered | `curl localhost:5001/api/skill-tree` | Returns 6-level structure |
| Verify database tables exist | `sqlite3 bridge.db ".tables"` | Shows user_convention_progress, etc. |
| Verify convention registry | `curl localhost:5001/api/conventions/by-level` | Returns 17 conventions in 3 levels |
| Verify analytics API | `curl localhost:5001/api/analytics/dashboard?user_id=1` | Returns dashboard data |
| Test record-practice | `POST /api/conventions/record-practice` | Updates progress |
| Test next-recommended | `curl localhost:5001/api/conventions/next-recommended?user_id=1` | Returns recommendation |

**Testing Script:**
```bash
#!/bin/bash
# test_learning_infrastructure.sh

BASE_URL="http://localhost:5001"

echo "Testing Learning Infrastructure..."

echo -n "1. Skill Tree API: "
curl -s "$BASE_URL/api/skill-tree" | jq -r '.levels | length' | xargs echo "levels"

echo -n "2. Conventions by Level: "
curl -s "$BASE_URL/api/conventions/by-level" | jq -r '[.essential, .intermediate, .advanced] | map(length) | add' | xargs echo "conventions"

echo -n "3. Analytics Dashboard: "
curl -s "$BASE_URL/api/analytics/dashboard?user_id=1" | jq -r 'has("bidding_stats")'

echo -n "4. Next Recommended: "
curl -s "$BASE_URL/api/conventions/next-recommended?user_id=1" | jq -r '.recommended.name // "none"'

echo "Done."
```

---

### Phase 1: Extend Curriculum Structure (2 days)
**Goal:** Add Levels 0-4 (fundamentals) to existing skill tree

#### 1.1 Extend Skill Tree Definition

**File:** `backend/engine/learning/skill_tree.py`

**Current:** 6 levels focused on conventions
**Needed:** 9 levels (0-8) per curriculum document

```python
# Add to SKILL_TREE in skill_tree.py

SKILL_TREE = {
    # NEW: Levels 0-4 for fundamentals
    'level_0': {
        'id': 'level_0',
        'name': 'Foundations',
        'description': 'Hand evaluation and bidding language',
        'order': 0,
        'prerequisites': [],
        'skills': [
            {
                'id': 'hand_evaluation',
                'name': 'Hand Evaluation',
                'type': 'skill',
                'hands_required': 5,
                'passing_accuracy': 0.80,
                'subtopics': ['hcp_counting', 'distribution_points', 'balanced_recognition']
            },
            {
                'id': 'suit_quality',
                'name': 'Suit Quality',
                'type': 'skill',
                'hands_required': 5,
                'passing_accuracy': 0.80
            },
            {
                'id': 'bidding_language',
                'name': 'Bidding Language',
                'type': 'skill',
                'hands_required': 5,
                'passing_accuracy': 0.80
            }
        ]
    },
    'level_1': {
        'id': 'level_1',
        'name': 'Opening Bids',
        'description': 'When and what to open',
        'order': 1,
        'prerequisites': ['level_0'],
        'skills': [
            {'id': 'when_to_open', 'name': 'When to Open', 'hands_required': 5},
            {'id': 'one_of_suit', 'name': 'Opening 1 of a Suit', 'hands_required': 8},
            {'id': 'one_nt_opening', 'name': 'Opening 1NT', 'hands_required': 5},
            {'id': 'two_club_opening', 'name': 'Opening 2♣', 'hands_required': 4},
            {'id': 'two_nt_opening', 'name': 'Opening 2NT', 'hands_required': 3}
        ]
    },
    # ... levels 2-4 similarly

    # EXISTING: Remap current levels to 5-8
    'level_5': {
        # Current 'level_2' (Essential Conventions) becomes level_5
        # ...
    }
}
```

#### 1.2 Add Topic Metadata to Convention Registry Pattern

**File:** `backend/engine/ai/topics/topic_registry.py` (NEW - but follows convention_registry.py pattern)

```python
# Follow exact pattern of convention_registry.py
# Reuse ConventionMetadata dataclass structure

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class TopicLevel(Enum):
    FOUNDATIONS = 'foundations'
    OPENING = 'opening'
    RESPONDING = 'responding'
    REBIDS = 'rebids'

@dataclass
class TopicMetadata:
    """Mirrors ConventionMetadata structure for consistency"""
    id: str
    name: str
    level: TopicLevel
    description: str
    hands_required: int
    passing_accuracy: float
    prerequisites: List[str]
    # ... same pattern as ConventionMetadata
```

**Testing:** Unit test that all topics load and have valid metadata

---

### Phase 2: Hand Generation for Fundamentals (3 days)
**Goal:** Generate practice hands for Levels 0-4 topics

#### 2.1 Extend Hand Constructor

**File:** `backend/engine/hand_constructor.py`

**Existing:** `generate_hand_for_convention()` - works for conventions
**Needed:** `generate_hand_for_topic()` - works for fundamentals

```python
def generate_hand_for_topic(topic_id: str, subtopic: str = None) -> Dict:
    """
    Generate a hand appropriate for practicing a fundamental topic.

    Reuses existing generate_hand_with_constraints() internally.
    """

    TOPIC_CONSTRAINTS = {
        'hcp_counting': {
            # Random HCP, user must count correctly
            'hcp_range': (0, 40),  # Full range for variety
            'test_type': 'count_hcp'
        },
        'when_to_open': {
            # Mix of opening and non-opening hands
            'hcp_range': (8, 16),  # Edge cases
            'test_type': 'should_open'
        },
        'one_of_suit': {
            # Valid opening hands
            'hcp_range': (12, 21),
            'is_balanced': False,  # Mix
            'test_type': 'what_to_open'
        },
        'one_nt_opening': {
            # 1NT candidates and near-misses
            'hcp_range': (14, 18),
            'test_type': 'is_1nt_opening'
        },
        # ... other topics
    }

    constraints = TOPIC_CONSTRAINTS.get(topic_id, {})
    return generate_hand_with_constraints(**constraints)
```

#### 2.2 Topic Scenarios File

**File:** `backend/scenarios/topic_scenarios.json` (NEW - follows bidding_scenarios.json pattern)

```json
{
  "topics": [
    {
      "id": "hcp_counting",
      "name": "HCP Counting",
      "level": 0,
      "hands": [
        {
          "description": "Count the HCP in this hand",
          "setup": {"hcp_range": [10, 15]},
          "question_type": "count_hcp",
          "correct_answer_field": "hcp"
        }
      ]
    },
    {
      "id": "when_to_open",
      "name": "Should You Open?",
      "level": 1,
      "hands": [
        {
          "description": "Should you open this hand?",
          "setup": {"hcp_range": [11, 14]},
          "question_type": "yes_no",
          "evaluation": "rule_of_20"
        }
      ]
    }
  ]
}
```

**Testing:**
- Unit test each topic generates valid hands
- Integration test that generated hands match topic requirements

---

### Phase 3: Learning Mode API (2 days) ✅ COMPLETE
**Goal:** Add endpoints for guided learning flow
**Status:** Implemented and tested 2025-12-25

#### Implementation Summary

**File:** `backend/engine/learning/learning_path_api.py`

**New Endpoints Added:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/learning/start-session` | POST | Start skill/convention practice |
| `/api/learning/submit-answer` | POST | Submit answer, get feedback + next hand |
| `/api/learning/review` | GET | Interleaved review for level |
| `/api/learning/level-assessment` | GET | Level mastery test (20 hands) |
| `/api/learning/status` | GET | User's comprehensive learning status |

**Features Implemented:**
- HCP counting, yes/no, and bidding question evaluation
- Bid normalization (ASCII "1H" ↔ Unicode "1♥")
- Automatic next hand generation on answer submit
- Mastery detection (80% accuracy, 85% for Level 8)
- Prerequisite checking for assessments

#### 3.1 New Endpoints (extend learning_path_api.py)

**DO NOT create new file** - add to existing `learning_path_api.py`:

```python
def start_learning_session():
    """
    POST /api/learning/start-session

    Starts a new learning session for a topic.
    Returns the first hand to practice.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    topic_id = data.get('topic_id')  # or convention_id

    # Reuse existing progress tracking
    progress = get_user_convention_status(user_id, topic_id)

    # Generate hand using existing infrastructure
    hand = generate_hand_for_topic(topic_id) if is_topic(topic_id) else generate_hand_for_convention(topic_id)

    return jsonify({
        'session_id': create_session_id(),
        'topic_id': topic_id,
        'hand': hand,
        'progress': progress,
        'hands_required': get_hands_required(topic_id),
        'current_accuracy': progress.get('accuracy', 0) if progress else 0
    })


def submit_learning_answer():
    """
    POST /api/learning/submit-answer

    Submit answer for current hand, get feedback and next hand.
    Reuses existing evaluate-bid infrastructure.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    topic_id = data.get('topic_id')
    answer = data.get('answer')
    hand_data = data.get('hand_data')

    # REUSE existing evaluation
    if is_convention(topic_id):
        # Use existing /api/evaluate-bid logic
        result = evaluate_bid_internal(hand_data, answer)
    else:
        # Use topic-specific evaluation
        result = evaluate_topic_answer(topic_id, hand_data, answer)

    # REUSE existing record-practice
    record_convention_practice_internal(user_id, topic_id, result['is_correct'])

    # Check for completion
    progress = get_user_convention_status(user_id, topic_id)
    is_complete = check_mastery(progress, topic_id)

    # Generate next hand or return completion
    if is_complete:
        return jsonify({
            'result': result,
            'completed': True,
            'final_accuracy': progress['accuracy'],
            'next_topic': get_next_recommended(user_id)
        })
    else:
        next_hand = generate_hand_for_topic(topic_id) if is_topic(topic_id) else generate_hand_for_convention(topic_id)
        return jsonify({
            'result': result,
            'completed': False,
            'next_hand': next_hand,
            'progress': progress
        })


def get_interleaved_review():
    """
    GET /api/learning/review?user_id=X&level=Y

    Returns a mixed set of hands from completed topics in a level.
    For interleaved practice after blocked learning.
    """
    user_id = request.args.get('user_id', type=int)
    level = request.args.get('level', type=int)

    # Get completed topics in this level
    completed = get_completed_topics_in_level(user_id, level)

    if len(completed) < 2:
        return jsonify({'error': 'Need 2+ completed topics for review'}), 400

    # Generate mixed hands
    hands = []
    for _ in range(10):  # 10 review hands
        topic = random.choice(completed)
        hand = generate_hand_for_topic(topic['id']) if is_topic(topic['id']) else generate_hand_for_convention(topic['id'])
        hand['topic_id'] = topic['id']
        hands.append(hand)

    random.shuffle(hands)

    return jsonify({
        'review_session': True,
        'topics_included': [t['name'] for t in completed],
        'hands': hands
    })


def get_level_assessment():
    """
    GET /api/learning/level-assessment?user_id=X&level=Y

    Returns mixed assessment for level completion.
    """
    user_id = request.args.get('user_id', type=int)
    level = request.args.get('level', type=int)

    # Verify all topics in level are individually completed
    all_topics = get_topics_in_level(level)
    completed = get_completed_topics_in_level(user_id, level)

    if len(completed) < len(all_topics):
        return jsonify({
            'ready': False,
            'completed': len(completed),
            'required': len(all_topics),
            'remaining': [t for t in all_topics if t not in completed]
        })

    # Generate assessment (20 mixed hands)
    hands = []
    for topic in all_topics:
        count = 20 // len(all_topics)  # Distribute evenly
        for _ in range(count):
            hand = generate_hand_for_topic(topic['id']) if is_topic(topic['id']) else generate_hand_for_convention(topic['id'])
            hand['topic_id'] = topic['id']
            hands.append(hand)

    random.shuffle(hands)

    return jsonify({
        'ready': True,
        'assessment': True,
        'level': level,
        'hands': hands,
        'passing_accuracy': 0.80 if level < 8 else 0.85
    })
```

#### 3.2 Register New Endpoints

**File:** `backend/engine/learning/learning_path_api.py` (add to existing `register_learning_endpoints()`)

```python
def register_learning_endpoints(app):
    # ... existing registrations ...

    # NEW: Learning Mode endpoints
    app.route('/api/learning/start-session', methods=['POST'])(start_learning_session)
    app.route('/api/learning/submit-answer', methods=['POST'])(submit_learning_answer)
    app.route('/api/learning/review', methods=['GET'])(get_interleaved_review)
    app.route('/api/learning/level-assessment', methods=['GET'])(get_level_assessment)

    print("✓ Learning mode endpoints registered")
```

**Testing:**
- Integration tests for each new endpoint
- Test session flow: start → submit → submit → complete
- Test review generation with mixed topics
- Test level assessment prerequisites

---

### Phase 4: Frontend Learning Mode (3 days)
**Goal:** Guided learning UI that uses existing services

#### 4.1 Learning Mode Component

**File:** `frontend/src/components/learning/LearningMode.js` (NEW)

**Pattern:** Follow existing `LearningDashboard.js` structure

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
// REUSE existing services
import { analyticsService } from '../../services/analyticsService';
import './LearningMode.css';

const LearningMode = ({ onClose }) => {
  const { userId } = useAuth();
  const [currentLevel, setCurrentLevel] = useState(null);
  const [currentTopic, setCurrentTopic] = useState(null);
  const [currentHand, setCurrentHand] = useState(null);
  const [sessionProgress, setSessionProgress] = useState({ correct: 0, total: 0 });
  const [view, setView] = useState('level-select'); // level-select, practice, review, assessment, complete

  // Load skill tree progress on mount
  useEffect(() => {
    loadProgress();
  }, [userId]);

  const loadProgress = async () => {
    // REUSE existing endpoint
    const response = await fetch(`/api/skill-tree/progress?user_id=${userId}`);
    const data = await response.json();
    // Find current level (first incomplete)
    const currentLvl = data.levels.find(l => !l.completed);
    setCurrentLevel(currentLvl);
  };

  const startTopic = async (topicId) => {
    const response = await fetch('/api/learning/start-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, topic_id: topicId })
    });
    const data = await response.json();
    setCurrentTopic(topicId);
    setCurrentHand(data.hand);
    setSessionProgress({ correct: 0, total: 0, required: data.hands_required });
    setView('practice');
  };

  const submitAnswer = async (answer) => {
    const response = await fetch('/api/learning/submit-answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        topic_id: currentTopic,
        answer: answer,
        hand_data: currentHand
      })
    });
    const data = await response.json();

    // Update progress
    setSessionProgress(prev => ({
      ...prev,
      correct: prev.correct + (data.result.is_correct ? 1 : 0),
      total: prev.total + 1
    }));

    if (data.completed) {
      setView('complete');
    } else {
      setCurrentHand(data.next_hand);
    }
  };

  // Render based on current view
  // ... (level selection, practice, review, assessment, completion views)
};

export default LearningMode;
```

#### 4.2 Scorecard Component

**File:** `frontend/src/components/learning/Scorecard.js` (NEW)

**Pattern:** Reuse data from existing `/api/analytics/dashboard` and `/api/user/convention-progress`

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './Scorecard.css';

const Scorecard = () => {
  const { userId } = useAuth();
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    loadScorecard();
  }, [userId]);

  const loadScorecard = async () => {
    // REUSE existing endpoints
    const [skillTree, conventions] = await Promise.all([
      fetch(`/api/skill-tree/progress?user_id=${userId}`).then(r => r.json()),
      fetch(`/api/user/convention-progress?user_id=${userId}`).then(r => r.json())
    ]);

    setProgress({ skillTree, conventions });
  };

  // Render level-by-level progress with accuracy bars
  // ...
};
```

#### 4.3 Integration with Main App

**File:** `frontend/src/App.js` (modify existing)

```jsx
// Add Learning Mode entry point
import LearningMode from './components/learning/LearningMode';
import Scorecard from './components/learning/Scorecard';

// Add state
const [showLearningMode, setShowLearningMode] = useState(false);
const [showScorecard, setShowScorecard] = useState(false);

// Add buttons to UI (near existing "Practice Convention" button)
<button onClick={() => setShowLearningMode(true)}>
  📚 Learning Mode
</button>
<button onClick={() => setShowScorecard(true)}>
  📊 My Progress
</button>

// Add modals
{showLearningMode && <LearningMode onClose={() => setShowLearningMode(false)} />}
{showScorecard && <Scorecard onClose={() => setShowScorecard(false)} />}
```

**Testing:**
- E2E test: User can enter Learning Mode
- E2E test: User can complete a topic
- E2E test: Scorecard shows accurate progress
- E2E test: Level unlock works correctly

---

### Phase 5: Testing & Quality Assurance (2 days)

#### 5.1 Leverage Existing Testing Infrastructure

**Existing Assets to Reuse:**

| Test Type | Existing Infrastructure | How to Extend |
|-----------|------------------------|---------------|
| Bidding Quality | `test_bidding_quality_score.py` | Run against Learning Mode hands |
| Unit Tests | `backend/tests/unit/` structure | Add tests for new endpoints |
| Integration Tests | `backend/tests/integration/` | Add learning flow tests |
| E2E Tests | `frontend/e2e/tests/` | Add learning mode scenarios |
| Quick Test | `./test_quick.sh` | Include learning tests |

#### 5.2 New Test Files

**File:** `backend/tests/integration/test_learning_mode.py`

```python
"""
Integration tests for Learning Mode.
Reuses existing test patterns and fixtures.
"""

import pytest
from tests.fixtures import test_client, test_user  # Reuse existing fixtures

class TestLearningModeAPI:

    def test_start_session_topic(self, test_client, test_user):
        """Test starting a learning session for a fundamental topic"""
        response = test_client.post('/api/learning/start-session', json={
            'user_id': test_user['id'],
            'topic_id': 'hcp_counting'
        })
        assert response.status_code == 200
        data = response.json
        assert 'hand' in data
        assert 'hands_required' in data

    def test_start_session_convention(self, test_client, test_user):
        """Test starting a learning session for a convention (existing flow)"""
        response = test_client.post('/api/learning/start-session', json={
            'user_id': test_user['id'],
            'topic_id': 'stayman'
        })
        assert response.status_code == 200
        data = response.json
        assert 'hand' in data

    def test_submit_answer_correct(self, test_client, test_user):
        """Test submitting a correct answer"""
        # Start session
        start = test_client.post('/api/learning/start-session', json={
            'user_id': test_user['id'],
            'topic_id': 'when_to_open'
        }).json

        # Submit answer
        response = test_client.post('/api/learning/submit-answer', json={
            'user_id': test_user['id'],
            'topic_id': 'when_to_open',
            'answer': 'yes',  # Assuming hand should open
            'hand_data': start['hand']
        })
        assert response.status_code == 200
        data = response.json
        assert 'result' in data
        assert 'completed' in data

    def test_interleaved_review_requires_completed_topics(self, test_client, test_user):
        """Test that review requires 2+ completed topics"""
        response = test_client.get(f'/api/learning/review?user_id={test_user["id"]}&level=0')
        # Should fail if user hasn't completed topics
        assert response.status_code == 400 or 'error' in response.json

    def test_level_assessment_prerequisites(self, test_client, test_user):
        """Test that level assessment checks all topics completed"""
        response = test_client.get(f'/api/learning/level-assessment?user_id={test_user["id"]}&level=0')
        data = response.json
        # Should indicate not ready if topics incomplete
        if not data.get('ready'):
            assert 'remaining' in data
```

**File:** `frontend/e2e/tests/learning-mode.spec.js`

```javascript
// E2E tests for Learning Mode
// Follows existing Playwright patterns in e2e/tests/

import { test, expect } from '@playwright/test';

test.describe('Learning Mode', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Login if needed (reuse existing auth pattern)
  });

  test('can enter Learning Mode', async ({ page }) => {
    await page.click('text=Learning Mode');
    await expect(page.locator('.learning-mode-container')).toBeVisible();
  });

  test('shows current level and recommended topic', async ({ page }) => {
    await page.click('text=Learning Mode');
    await expect(page.locator('.current-level')).toBeVisible();
    await expect(page.locator('.recommended-topic')).toBeVisible();
  });

  test('can start and complete a topic practice session', async ({ page }) => {
    await page.click('text=Learning Mode');
    await page.click('text=Start'); // Start recommended topic

    // Complete required hands (mock or actual)
    for (let i = 0; i < 5; i++) {
      await expect(page.locator('.practice-hand')).toBeVisible();
      // Submit answer...
      await page.click('[data-testid="submit-answer"]');
    }

    await expect(page.locator('.topic-complete')).toBeVisible();
  });

  test('scorecard shows accurate progress', async ({ page }) => {
    await page.click('text=My Progress');
    await expect(page.locator('.scorecard')).toBeVisible();
    await expect(page.locator('.level-progress')).toHaveCount(9); // 9 levels
  });
});
```

#### 5.3 Quality Score Validation

**File:** `backend/test_learning_hand_quality.py` (NEW - follows existing pattern)

```python
"""
Validates that Learning Mode generates appropriate hands for each topic.
Follows pattern of test_bidding_quality_score.py
"""

from engine.hand_constructor import generate_hand_for_topic
from engine.learning.skill_tree import get_skill_tree_manager

def test_topic_hand_quality():
    """Test that generated hands match topic requirements"""
    tree = get_skill_tree_manager()

    results = []

    for level in tree.get_all_levels():
        for skill in level['skills']:
            topic_id = skill['id']

            # Generate 10 hands for each topic
            for _ in range(10):
                hand = generate_hand_for_topic(topic_id)

                # Validate hand meets topic requirements
                is_valid = validate_hand_for_topic(hand, topic_id)
                results.append({
                    'topic': topic_id,
                    'valid': is_valid
                })

    # Report
    valid_count = sum(1 for r in results if r['valid'])
    total = len(results)
    print(f"Topic Hand Quality: {valid_count}/{total} ({100*valid_count/total:.1f}%)")

    assert valid_count / total >= 0.95, "Hand quality below 95%"
```

---

## Testing Protocol Summary

### Before Each Phase

```bash
# Run existing tests to ensure no regression
./test_quick.sh
```

### After Each Phase

```bash
# Phase 0: Validation
./test_learning_infrastructure.sh  # New script

# Phase 1: Curriculum Extension
pytest backend/tests/unit/test_skill_tree.py -v

# Phase 2: Hand Generation
pytest backend/tests/unit/test_hand_constructor.py -v
python3 backend/test_learning_hand_quality.py

# Phase 3: API
pytest backend/tests/integration/test_learning_mode.py -v

# Phase 4: Frontend
npm run test:e2e -- --grep "Learning Mode"

# Phase 5: Full Suite
./test_all.sh
```

### Before Merge

```bash
# Full test suite
./test_all.sh

# Bidding quality (ensure no regression)
python3 backend/test_bidding_quality_score.py --hands 100

# Learning hand quality
python3 backend/test_learning_hand_quality.py
```

---

## Timeline Summary

| Phase | Duration | Focus | Key Deliverable |
|-------|----------|-------|-----------------|
| 0 | 1 day | Validation | Confirm existing infrastructure works |
| 1 | 2 days | Curriculum | Levels 0-4 in skill tree |
| 2 | 3 days | Hand Generation | Topics generate valid hands |
| 3 | 2 days | API | Learning session endpoints |
| 4 | 3 days | Frontend | Learning Mode UI |
| 5 | 2 days | Testing | Full test coverage |

**Total: ~13 days**

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Existing APIs don't work as expected | Phase 0 validates before building |
| Hand generation for fundamentals is complex | Start with simple topics (HCP counting) |
| UI complexity | Reuse existing component patterns |
| Integration breaks existing features | Run full test suite after each phase |
| Scope creep | MVP has NO gamification (XP, badges, streaks) - add later |

---

## What's NOT in MVP

Explicitly excluded to keep scope manageable:

- XP system
- Badges/achievements
- Streak tracking
- Leaderboards
- Spaced repetition scheduling
- Adaptive difficulty (beyond what exists)
- Social features
- Video tutorials
- Hint system (beyond existing explanations)

These can be added in future phases using the existing infrastructure (user_manager.py, celebration_manager.py, etc.)

---

## Dependencies

| Dependency | Status | Action |
|------------|--------|--------|
| Bidding engine reliability | 97.5% appropriateness | Good to proceed |
| Existing API endpoints | Need validation | Phase 0 |
| Database tables | Exist | Verify in Phase 0 |
| Frontend service | Exists | Reuse directly |

---

## Success Criteria

**MVP Complete When:**
1. User can enter Learning Mode and see current level
2. User can practice topics in sequence (blocked)
3. User can complete a topic and see it marked complete
4. User can do interleaved review after 2+ topics
5. User can pass level assessment to unlock next level
6. Scorecard shows accurate per-topic and per-level progress
7. All tests pass
8. No regression in existing bidding quality
