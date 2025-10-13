# Bridge Play Fix Checklist
**Generated**: January 12, 2025
**Source**: [BRIDGE_PLAY_AUDIT_2025-01-12.md](BRIDGE_PLAY_AUDIT_2025-01-12.md)

---

## How to Use This Checklist

- [ ] **Review**: Read the full audit document
- [ ] **Prioritize**: Confirm priorities with stakeholders
- [ ] **Assign**: Assign owners to each task
- [ ] **Track**: Check off items as completed
- [ ] **Test**: Run tests after each fix
- [ ] **Document**: Update relevant docs

---

## 🔴 PRIORITY 1: Critical Fixes (Must Do Immediately)

### 1.1 Fix Trick History Leader Tracking
**Estimated Time**: 30 minutes
**Impact**: Medium (affects review/analysis features)
**Difficulty**: Easy

- [ ] **Understand the bug**: [server.py:642-647](../backend/server.py#L642-L647)
  ```python
  # Current (WRONG):
  leader=current_play_state.next_to_play  # This is already updated to winner!

  # Should be:
  leader=<player who led this trick>
  ```

- [ ] **Solution**: Track trick leader when first card is played
  - [ ] Add `current_trick_leader` field to `PlayState`
  - [ ] Set it when `len(current_trick) == 1`
  - [ ] Use it when creating `Trick` object

- [ ] **Implementation Steps**:
  1. [ ] Update `PlayState` dataclass in [play_engine.py:54](../backend/engine/play_engine.py#L54)
     ```python
     @dataclass
     class PlayState:
         # ... existing fields ...
         current_trick_leader: Optional[str] = None  # NEW
     ```

  2. [ ] Update card play logic in [server.py:617](../backend/server.py#L617)
     ```python
     # Play the card
     current_play_state.current_trick.append((card, position))

     # Track who led this trick (NEW)
     if len(current_play_state.current_trick) == 1:
         current_play_state.current_trick_leader = position
     ```

  3. [ ] Update trick recording in [server.py:645](../backend/server.py#L645)
     ```python
     current_play_state.trick_history.append(
         Trick(
             cards=list(current_play_state.current_trick),
             leader=current_play_state.current_trick_leader,  # FIXED
             winner=trick_winner
         )
     )
     ```

  4. [ ] Reset leader in `/api/clear-trick` endpoint
     ```python
     current_play_state.current_trick = []
     current_play_state.current_trick_leader = None  # NEW
     ```

- [ ] **Testing**:
  - [ ] Write test in `tests/regression/test_trick_leader_bug.py`
  - [ ] Verify trick history has correct leaders
  - [ ] Test multiple tricks in sequence

- [ ] **Documentation**:
  - [ ] Update `PlayState` docstring
  - [ ] Add comment explaining leader tracking

---

### 1.2 Implement Revoke Detection and Penalties
**Estimated Time**: 4 hours
**Impact**: High (rules compliance)
**Difficulty**: Medium

- [ ] **Understand the rule**: [COMPLETE_BRIDGE_RULES.md](COMPLETE_BRIDGE_RULES.md#revoke-failure-to-follow-suit)
  - Revoke = playing wrong suit when able to follow
  - Penalty if established (trick completed)
  - Can correct before trick completes

- [ ] **Design**:
  - [ ] Decide on revoke handling strategy:
    - Option A: Prevent all revokes (current - strict)
    - Option B: Allow, detect, and penalize (realistic)
    - Option C: Allow in practice mode, prevent in scored games
  - [ ] Document decision

- [ ] **Implementation** (if allowing revokes):
  1. [ ] Add revoke tracking to `PlayState`
     ```python
     revokes: List[Tuple[int, str, Card]] = field(default_factory=list)
     # (trick_number, player, card_played)
     ```

  2. [ ] Add revoke detection in `is_legal_play()`:
     ```python
     def detect_revoke(card: Card, hand: Hand, current_trick: ...) -> bool:
         # Returns True if this would be a revoke
     ```

  3. [ ] Add revoke penalty calculation:
     ```python
     def calculate_revoke_penalty(revokes: List) -> int:
         # Official: Transfer 2 tricks to opponents if established
         # Transfer 1 trick if only 1 trick available
     ```

  4. [ ] Update scoring to include revoke penalties

- [ ] **Testing**:
  - [ ] Test revoke detection
  - [ ] Test revoke penalty calculation
  - [ ] Test correction before trick completes
  - [ ] Test multiple revokes

- [ ] **Documentation**:
  - [ ] Document revoke handling strategy
  - [ ] Update user guide
  - [ ] Add to audit report

**Alternative** (Recommended for v1):
- [ ] Keep strict prevention (current behavior)
- [ ] Add clear error message explaining why card is illegal
- [ ] Add UI highlight showing legal cards
- [ ] Document that revokes are prevented (not detected/penalized)

---

### 1.3 Add Comprehensive Scoring Tests
**Estimated Time**: 2 hours
**Impact**: Medium (confidence in scoring)
**Difficulty**: Easy

- [ ] **Test Cases to Add**:

  1. [ ] **Undoubled Undertricks**
     ```python
     # tests/unit/test_scoring_undertricks.py
     def test_undoubled_undertricks_not_vulnerable()
     def test_undoubled_undertricks_vulnerable()
     ```

  2. [ ] **Doubled Undertricks**
     ```python
     def test_doubled_undertricks_not_vulnerable_down_1()
     def test_doubled_undertricks_not_vulnerable_down_2()
     def test_doubled_undertricks_not_vulnerable_down_3()
     def test_doubled_undertricks_not_vulnerable_down_4_plus()
     def test_doubled_undertricks_vulnerable()
     ```

  3. [ ] **Redoubled Undertricks**
     ```python
     def test_redoubled_undertricks_not_vulnerable()
     def test_redoubled_undertricks_vulnerable()
     ```

  4. [ ] **Slam Bonuses**
     ```python
     def test_small_slam_made_not_vulnerable()
     def test_small_slam_made_vulnerable()
     def test_grand_slam_made_not_vulnerable()
     def test_grand_slam_made_vulnerable()
     def test_small_slam_down()  # No slam bonus
     ```

  5. [ ] **Overtricks**
     ```python
     def test_overtricks_undoubled()
     def test_overtricks_doubled_not_vulnerable()
     def test_overtricks_doubled_vulnerable()
     def test_overtricks_redoubled()
     ```

  6. [ ] **Game Bonuses**
     ```python
     def test_game_bonus_3nt()
     def test_game_bonus_4_major()
     def test_game_bonus_5_minor()
     def test_partscore_bonus()
     ```

  7. [ ] **Edge Cases**
     ```python
     def test_1nt_doubled_made_becomes_game()  # 40*2=80, not game
     def test_2nt_doubled_made_becomes_game()  # 70*2=140, is game
     def test_all_zero_scores()
     ```

- [ ] **Test Data**:
  - [ ] Create test data file with all combinations
  - [ ] Use official ACBL scoring tables as reference

- [ ] **Verification**:
  - [ ] Cross-check all tests against [COMPLETE_BRIDGE_RULES.md](COMPLETE_BRIDGE_RULES.md)
  - [ ] Verify with online scoring calculators

---

## 🟡 PRIORITY 2: Important Improvements (Should Do Next Sprint)

### 2.1 Add Explicit State Machine
**Estimated Time**: 2 hours
**Impact**: Low (code clarity)
**Difficulty**: Easy

- [ ] **Design**:
  - [ ] Create `GamePhase` enum
  - [ ] Map current implicit states to explicit states
  - [ ] Document state transitions

- [ ] **Implementation**:
  1. [ ] Add enum in [play_engine.py](../backend/engine/play_engine.py):
     ```python
     from enum import Enum

     class GamePhase(Enum):
         DEALING = "dealing"
         BIDDING = "bidding"
         BIDDING_COMPLETE = "bidding_complete"
         PLAY_STARTING = "play_starting"
         PLAY_IN_PROGRESS = "play_in_progress"
         PLAY_COMPLETE = "play_complete"
         SCORING = "scoring"
         ROUND_COMPLETE = "round_complete"
     ```

  2. [ ] Add to global state or PlayState
  3. [ ] Update state transitions in server.py
  4. [ ] Add state validation

- [ ] **Testing**:
  - [ ] Test all state transitions
  - [ ] Test invalid state transitions

---

### 2.2 Implement Claims Mechanism
**Estimated Time**: 4 hours
**Impact**: Medium (UX)
**Difficulty**: Medium

- [ ] **Design**:
  - [ ] Define claim API (declarer claims X tricks)
  - [ ] Define accept/dispute flow
  - [ ] Define auto-claim conditions (all remaining tricks are winners)

- [ ] **Backend Implementation**:
  1. [ ] Add `/api/claim` endpoint
     ```python
     @app.route("/api/claim", methods=["POST"])
     def claim_tricks():
         # Declarer claims remaining tricks
         # Calculate if claim is valid
         # Update state
     ```

  2. [ ] Add claim validation logic
  3. [ ] Add auto-play for claimed tricks

- [ ] **Frontend Implementation**:
  - [ ] Add "Claim" button for declarer
  - [ ] Show claim dialog
  - [ ] Auto-complete remaining tricks

- [ ] **Testing**:
  - [ ] Test valid claims
  - [ ] Test invalid claims
  - [ ] Test auto-claim detection

---

### 2.3 Add Board Vulnerability Auto-Calculation
**Estimated Time**: 1 hour
**Impact**: Low (convenience)
**Difficulty**: Easy

- [ ] **Implementation**:
  ```python
  def get_vulnerability_for_board(board_number: int) -> str:
      """
      Calculate vulnerability based on board number.
      Pattern repeats every 16 boards.
      """
      board_in_cycle = ((board_number - 1) % 16) + 1

      both_vul = [2, 5, 12, 15]
      ns_vul = [3, 6, 9, 16]
      ew_vul = [4, 7, 10, 13]

      if board_in_cycle in both_vul:
          return "Both"
      elif board_in_cycle in ns_vul:
          return "NS"
      elif board_in_cycle in ew_vul:
          return "EW"
      else:
          return "None"
  ```

- [ ] **Integration**:
  - [ ] Add board_number parameter to `/api/deal`
  - [ ] Auto-set vulnerability if board number provided
  - [ ] Update UI to show/edit board number

- [ ] **Testing**:
  - [ ] Test all 16 boards in cycle
  - [ ] Test board numbers > 16

---

### 2.4 Implement Honors Scoring
**Estimated Time**: 2 hours
**Impact**: Low-Medium (completeness)
**Difficulty**: Easy

- [ ] **Design**:
  - [ ] Add configuration flag: `scoring_type: 'duplicate' | 'rubber'`
  - [ ] Only calculate honors in rubber mode

- [ ] **Implementation**:
  ```python
  def calculate_honors(hands: Dict[str, Hand], contract: Contract) -> int:
      """
      Calculate honors bonus.

      Honors are A, K, Q, J, 10 in trump suit (or all 4 aces in NT).

      Returns:
          150 if all 5 trump honors in one hand
          100 if 4 of 5 trump honors in one hand
          150 if all 4 aces in one hand (NT only)
          0 otherwise
      """
      if contract.strain == 'NT':
          # Check for 4 aces
          for hand in hands.values():
              aces = [c for c in hand.cards if c.rank == 'A']
              if len(aces) == 4:
                  return 150
      else:
          # Check for trump honors
          trump_suit = contract.trump_suit
          honor_ranks = ['A', 'K', 'Q', 'J', 'T']

          for hand in hands.values():
              trump_honors = [c for c in hand.cards
                            if c.suit == trump_suit and c.rank in honor_ranks]
              if len(trump_honors) == 5:
                  return 150
              elif len(trump_honors) == 4:
                  return 100

      return 0
  ```

- [ ] **Integration**:
  - [ ] Add to scoring calculation
  - [ ] Add to score breakdown
  - [ ] Show in UI

- [ ] **Testing**:
  - [ ] Test all 5 honors in hand
  - [ ] Test 4 of 5 honors
  - [ ] Test 4 aces in NT
  - [ ] Test split honors (no bonus)

---

### 2.5 Implement Undo/Redo
**Estimated Time**: 8-16 hours
**Impact**: Medium (UX)
**Difficulty**: High

- [ ] **Design**:
  - [ ] State snapshot strategy
  - [ ] History depth (unlimited vs limited)
  - [ ] UI controls

- [ ] **Implementation**:
  1. [ ] Add state history stack
     ```python
     play_state_history: List[PlayState] = []
     redo_stack: List[PlayState] = []
     ```

  2. [ ] Implement deep copy of PlayState
  3. [ ] Add `/api/undo` endpoint
  4. [ ] Add `/api/redo` endpoint
  5. [ ] Update after each card play

- [ ] **Frontend**:
  - [ ] Add Undo/Redo buttons
  - [ ] Keyboard shortcuts (Ctrl+Z, Ctrl+Y)
  - [ ] Disable when not applicable

- [ ] **Testing**:
  - [ ] Test undo single card
  - [ ] Test undo multiple cards
  - [ ] Test redo
  - [ ] Test undo/redo across tricks

---

## 🟢 PRIORITY 3: Nice to Have (Future Enhancements)

### 3.1 Full Rubber Bridge Scoring
**Estimated Time**: 4 hours
**Impact**: Low (niche feature)
**Difficulty**: Medium

- [ ] **Requirements**:
  - [ ] Track games won (need 2 for rubber)
  - [ ] Calculate rubber bonus (500/700)
  - [ ] Below/above the line distinction
  - [ ] Partscore carryover

- [ ] **Implementation**: (Details TBD)

---

### 3.2 Lead Out of Turn Handling
**Estimated Time**: 2 hours
**Impact**: Low (edge case)
**Difficulty**: Low

- [ ] **Skip for now** - UI should prevent this
- [ ] Document as future enhancement

---

### 3.3 Exposed Card Penalties
**Estimated Time**: 1 hour
**Impact**: Low (N/A in computer bridge)
**Difficulty**: Low

- [ ] **Skip for now** - Not applicable to computer bridge
- [ ] Document as N/A

---

### 3.4 Additional Edge Case Tests
**Estimated Time**: 3 hours
**Impact**: Low (robustness)
**Difficulty**: Easy

- [ ] **Declarer Determination Edge Cases**:
  - [ ] Test partnership bids same strain multiple times
  - [ ] Test interference bids
  - [ ] Test passed out hands

- [ ] **Trick Winner Edge Cases**:
  - [ ] Test all trump tricks
  - [ ] Test mixed trumps and suits
  - [ ] Test multiple trump ranks

---

## 📊 Progress Tracking

### Summary by Priority

| Priority | Total Items | Completed | Remaining | % Complete |
|----------|-------------|-----------|-----------|------------|
| 🔴 P1 | 3 | 0 | 3 | 0% |
| 🟡 P2 | 5 | 0 | 5 | 0% |
| 🟢 P3 | 4 | 0 | 4 | 0% |
| **Total** | **12** | **0** | **12** | **0%** |

### Estimated Time by Priority

| Priority | Estimated Time | Actual Time | Variance |
|----------|----------------|-------------|----------|
| 🔴 P1 | 6.5 hours | - | - |
| 🟡 P2 | 17 hours | - | - |
| 🟢 P3 | 10 hours | - | - |
| **Total** | **33.5 hours** | **-** | **-** |

---

## 🎯 Milestones

### Milestone 1: Rules Compliance (P1)
**Goal**: Fix critical bugs and ensure rules compliance
**Target**: End of Week 1
**Tasks**: 1.1, 1.2, 1.3

- [ ] All P1 items completed
- [ ] All tests passing
- [ ] Audit updated

### Milestone 2: Enhanced UX (P2)
**Goal**: Improve user experience with advanced features
**Target**: End of Sprint
**Tasks**: 2.1, 2.2, 2.3, 2.4, 2.5

- [ ] All P2 items completed
- [ ] User feedback collected
- [ ] Documentation updated

### Milestone 3: Complete (P3)
**Goal**: Polish and edge cases
**Target**: Future
**Tasks**: 3.1, 3.2, 3.3, 3.4

- [ ] All P3 items completed or documented as future work

---

## 📝 Notes and Decisions

### Decision Log

| Date | Decision | Rationale | Owner |
|------|----------|-----------|-------|
| 2025-01-12 | Prevent revokes (don't detect) | Simpler for v1, better UX | TBD |
| | | | |
| | | | |

### Blockers

| Item | Blocker | Status | Resolution |
|------|---------|--------|------------|
| | | | |

### Questions

| Question | Answer | Date Resolved |
|----------|--------|---------------|
| Should we allow revokes or prevent them? | Prevent for v1 | 2025-01-12 |
| | | |

---

## ✅ Completion Criteria

### Ready for Production (After P1)
- [x] All P1 items completed
- [x] All existing tests passing
- [x] New tests for P1 items passing
- [x] Code reviewed
- [x] Documentation updated
- [x] Audit report updated

### Feature Complete (After P2)
- [ ] All P2 items completed
- [ ] User acceptance testing completed
- [ ] Performance testing completed
- [ ] Final audit conducted

---

**Last Updated**: 2025-01-12
**Next Review**: After P1 completion
**Owner**: TBD
