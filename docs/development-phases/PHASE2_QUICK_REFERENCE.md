# Phase 2 Quick Reference Card

**One-page summary of Phase 2 Minimax AI implementation**

---

## 🎯 What is Phase 2?

Upgrade AI from **simple rules** → **look-ahead search (Minimax)**

**Result:** AI that thinks 2-4 tricks ahead, plays 20-30% better

---

## ⏱️ Timeline

**Total: 8-12 hours**
- Week 1: Foundation (3-4 hours)
- Week 2: Minimax core (3-4 hours)
- Week 3: Polish & integrate (2-3 hours)

---

## 📁 New Files

```
backend/engine/play/ai/
├── base_ai.py          # Abstract interface
├── simple_ai.py        # Phase 1 (moved)
├── minimax_ai.py       # Phase 2 (NEW)
└── evaluation.py       # Position scoring (NEW)

tests/play/
├── test_minimax_ai.py     # Unit tests
└── test_ai_comparison.py  # Benchmarks
```

---

## 🔧 Key Components

### 1. Base AI Interface
```python
class BasePlayAI(ABC):
    @abstractmethod
    def choose_card(state, position) -> Card

    @abstractmethod
    def get_name() -> str

    @abstractmethod
    def get_difficulty() -> str
```

### 2. Minimax Algorithm
```python
class MinimaxPlayAI(BasePlayAI):
    def __init__(max_depth=4):
        # Look ahead 4 tricks

    def choose_card(state, position):
        # Alpha-beta pruning
        # Returns best card
```

### 3. Evaluation Function
```python
class PositionEvaluator:
    def evaluate(state, perspective):
        score = 0.0
        score += tricks_won          # 1.0 weight
        score += sure_winners        # 0.5 weight
        score += trump_control       # 0.3 weight
        score += communication       # 0.2 weight
        return score
```

---

## 📊 Performance Targets

| Depth | Time/Move | Strength | Use Case |
|-------|-----------|----------|----------|
| 2 | < 2s | Intermediate | Fast games |
| 4 | < 5s | Advanced | Training |
| 6 | < 30s | Expert | Analysis |

---

## ✅ Acceptance Criteria

- [ ] Outperforms Simple AI by 1-2 tricks
- [ ] < 5 seconds per move (depth 4)
- [ ] All tests passing
- [ ] Zero breaking changes
- [ ] UI integration complete

---

## 🎮 User-Facing Changes

### Difficulty Selection
```
Settings → AI Difficulty:
• Beginner (Fast)      - SimplePlayAI
• Intermediate (2s)    - Minimax depth=2
• Advanced (5s)        - Minimax depth=4
```

---

## 🚀 Implementation Order

**Week 1:**
1. Create `base_ai.py` interface
2. Move SimplePlayAI to new structure
3. Create basic PositionEvaluator
4. Write evaluator tests

**Week 2:**
5. Implement MinimaxPlayAI class
6. Add alpha-beta pruning
7. Test with depth=2
8. Benchmark vs Simple AI

**Week 3:**
9. Enhance evaluation function
10. Add move ordering
11. Integrate in server.py
12. Add UI difficulty selector

---

## 🎓 Key Concepts

### Minimax Search
- **Maximizing player:** Declarer (wants more tricks)
- **Minimizing player:** Defenders (want fewer tricks)
- **Alpha-beta pruning:** Skip bad branches
- **Depth limit:** Stop after N tricks

### Evaluation Components
1. **Tricks won** - Already decided (weight 1.0)
2. **Sure winners** - High cards (weight 0.5)
3. **Trump control** - Trump length (weight 0.3)
4. **Communication** - Entries (weight 0.2)
5. **Defense** - Defender potential (weight 0.15)

---

## 🔬 Testing Strategy

```python
# Unit test
def test_minimax_finds_winning_line():
    ai = MinimaxPlayAI(max_depth=3)
    card = ai.choose_card(winning_position, 'S')
    assert leads_to_contract_making(card)

# Benchmark test
def benchmark_ai_comparison():
    for deal in standard_deals:
        simple_tricks = play_with(SimplePlayAI())
        minimax_tricks = play_with(MinimaxPlayAI())
        assert minimax_tricks >= simple_tricks
```

---

## 💡 Design Decisions

### Why Minimax?
- ✅ Industry standard for card games
- ✅ Proven effective for Bridge
- ✅ Understandable and debuggable
- ✅ Good foundation for Phase 3

### Why Not Immediately DDS?
- Phase 2 teaches core concepts
- Minimax is useful standalone
- DDS is Phase 3 enhancement
- Gradual complexity increase

### Why Abstract Base Class?
- Type safety
- Easy to swap implementations
- Consistent interface
- Enables testing

---

## 🎯 Success Metrics

**Before (Phase 1):**
- Simple rule-based AI
- Instant decisions
- Beginner level play

**After (Phase 2):**
- Look-ahead search
- 2-5 second thinking time
- Intermediate/Advanced play
- +20-30% trick-taking improvement

---

## 🚧 What's NOT in Phase 2

❌ Imperfect information handling
❌ Double dummy solver integration
❌ Opening lead strategy
❌ Machine learning
❌ Bidding integration

*These are Phase 3 or future enhancements*

---

## 🔗 Related Documents

- **[PHASE2_MINIMAX_PLAN.md](PHASE2_MINIMAX_PLAN.md)** - Full detailed plan (35 pages)
- **[PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)** - Phase 1 summary
- **[STANDALONE_PLAY_GUIDE.md](STANDALONE_PLAY_GUIDE.md)** - Architecture guide

---

## 🚀 Ready to Start?

1. Read full plan: [PHASE2_MINIMAX_PLAN.md](PHASE2_MINIMAX_PLAN.md)
2. Set up dev environment
3. Start with Week 1 tasks
4. Track progress with tests
5. Benchmark against Simple AI

---

## 📞 Questions?

**Architecture:** See Phase 2 plan section 3
**Testing:** See Phase 2 plan section 8
**Timeline:** See Phase 2 plan section 7
**Performance:** See Phase 2 plan section 9

---

**Phase 2 transforms your AI from reactive to strategic! 🎯**
