# DDS Testing Approaches - Performance & Resource Analysis

## Current Production Baseline

**Current Usage:**
- Database: 256KB (1 user, 1 session)
- Review logs: 320KB (~20 hand files)
- Very low production traffic (early stage)

**DDS Performance Characteristics:**
- Solve time: 10-200ms per decision (from dds_ai.py documentation)
- Memory: ~5-10MB per active solver instance
- CPU: High during solve (single-threaded, CPU-bound)

---

## Approach 1: Instrumented Gameplay Logging ⭐ RECOMMENDED

### Load Impact: **MINIMAL** (0-5% overhead)

#### Implementation
```python
# Add after line 1538 in server.py (after trick is processed)
def log_ai_play_lightweight(card, position, ai_level, solve_time_ms):
    """Minimal logging - just append to SQLite"""
    cursor.execute("""
        INSERT INTO ai_play_log
        (timestamp, position, card, ai_level, solve_time_ms, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now(), position, f"{card.rank}{card.suit}",
          ai_level, solve_time_ms, session_id))
```

#### Pros
✅ **Extremely low overhead** - Single INSERT per AI play (~1ms)
✅ **Real production data** - Captures actual user gameplay patterns
✅ **Always on** - No manual test running required
✅ **Scalable** - SQLite handles thousands of inserts/sec
✅ **Historical data** - Build dataset over time
✅ **No user impact** - Invisible to end users
✅ **Incremental** - Start with minimal fields, expand later

#### Cons
❌ **Passive collection** - Need time to accumulate data (days/weeks)
❌ **Limited early data** - Only logs plays that happen organically
❌ **Storage grows** - ~100 bytes per play × 52 plays/hand
❌ **Privacy consideration** - Storing complete hand data

#### Resource Metrics
- **CPU**: +0.5% per play (1ms database insert)
- **Memory**: +50 bytes per play (in-memory before commit)
- **Disk**: ~100 bytes/play × 52 plays × N hands
  - 100 hands = 520KB
  - 1,000 hands = 5.2MB
  - 10,000 hands = 52MB
- **Network**: 0 (local only)
- **API latency**: +1-2ms per play

#### Cost-Benefit Score: **9/10**
Best for: Continuous monitoring, gradual dataset building

---

## Approach 2: Double Dummy Analysis Benchmarking

### Load Impact: **LOW-MODERATE** (5-15% during runs)

#### Implementation
```python
# Run weekly via cron job
# backend/benchmarks/weekly_dds_quality.py

def analyze_last_week_plays():
    # 1. Query 100 hands from database (10ms)
    # 2. For each hand:
    #    - Replay with DDS (10-200ms × 52 cards = 0.5-10 sec/hand)
    #    - Compare outcomes (1ms)
    # Total: 50-1000 seconds = 1-17 minutes
```

#### Pros
✅ **Scheduled** - Runs off-peak (e.g., 3am Sunday)
✅ **Comprehensive analysis** - Full double-dummy comparison
✅ **No real-time impact** - Batch processing
✅ **High quality metrics** - Can compute optimal play %
✅ **Controllable** - Adjust batch size based on load

#### Cons
❌ **Periodic spikes** - High CPU during analysis window
❌ **Slow** - Takes 1-17 minutes for 100 hands
❌ **Requires data** - Needs Approach 1's logs first
❌ **Single-threaded** - DDS doesn't parallelize well
❌ **Can timeout** - May need to split into smaller batches

#### Resource Metrics
- **CPU**: 80-100% for 1-17 minutes/week
- **Memory**: 50-100MB (loading hands + DDS state)
- **Disk**: 1-2MB output per week (analysis results)
- **Network**: 0
- **API latency**: 0 (runs separately)

**Weekly Resource Budget:**
- 100 hands: ~10 minutes CPU time
- 500 hands: ~50 minutes CPU time
- 1000 hands: ~100 minutes CPU time

#### Cost-Benefit Score: **7/10**
Best for: Weekly quality reports, trend analysis

---

## Approach 3: A/B Testing Framework

### Load Impact: **MODERATE** (15-30% overhead)

#### Implementation
```python
# Run in parallel with production
def ab_test_hand(hand_data):
    # Play same hand 3 times with different AIs
    # - DDS (expert): 10-200ms × 52 = 0.5-10 sec
    # - Minimax depth 4: 50-500ms × 52 = 2.6-26 sec
    # - Minimax depth 3: 10-100ms × 52 = 0.5-5 sec
    # Total: 3.6-41 seconds per hand × 3 versions = ~100 sec/hand
```

#### Pros
✅ **Controlled comparison** - Same hands, different AIs
✅ **Statistical validity** - Can compute confidence intervals
✅ **Immediate insights** - No waiting for organic traffic
✅ **Targeted testing** - Can test specific scenarios

#### Cons
❌ **High overhead** - 3× compute cost (triple plays same hands)
❌ **Expensive** - Each test hand takes ~100 seconds
❌ **Can block production** - If run synchronously
❌ **Complex to implement** - Need parallel execution
❌ **Not real gameplay** - Simulated scenarios only

#### Resource Metrics
- **CPU**: 3× normal load during test runs
- **Memory**: 150-300MB (3 AI instances + state)
- **Disk**: Minimal (results only)
- **Network**: 0
- **API latency**: 0 if async, +10-30s if sync

**Test Budget:**
- 10 hands: ~17 minutes
- 100 hands: ~2.7 hours
- 1000 hands: ~27 hours

#### Cost-Benefit Score: **5/10**
Best for: One-time comparisons, pre-deployment validation

---

## Approach 4: Production Telemetry Dashboard

### Load Impact: **MINIMAL** (1-3% overhead)

#### Implementation
```python
# Add to server.py
@app.route("/api/dds-metrics", methods=["GET"])
def get_dds_metrics():
    # Query pre-computed aggregates (10ms)
    return {
        "plays_24h": cached_count,
        "avg_solve_time": cached_avg,
        "fallback_rate": cached_rate
    }

# Background aggregation every 5 minutes
def update_metrics_cache():
    # Aggregate last 24h of data (100-500ms)
    # Store in Redis or app memory
```

#### Pros
✅ **Real-time visibility** - See DDS health live
✅ **Ultra-fast** - Queries cached aggregates
✅ **Alerting ready** - Can trigger on anomalies
✅ **Low overhead** - Aggregation only every 5 min
✅ **Operational value** - Detect issues immediately
✅ **User-facing** - Can show "AI status" badge

#### Cons
❌ **Requires Approach 1** - Needs logging infrastructure
❌ **Cache complexity** - Need to manage cache invalidation
❌ **Limited depth** - Shows aggregates, not detailed analysis
❌ **Memory usage** - Need to store recent aggregates

#### Resource Metrics
- **CPU**: +0.5% (periodic aggregation every 5 min)
- **Memory**: 1-5MB (cached aggregates)
- **Disk**: 0 (uses Approach 1's data)
- **Network**: <1KB per dashboard view
- **API latency**: +5-10ms (cached query)

#### Cost-Benefit Score: **8/10**
Best for: Operations monitoring, uptime tracking

---

## Approach 5: Batch Simulation Testing

### Load Impact: **HIGH** (50-100% for hours)

#### Implementation
```python
# backend/simulation_enhanced.py - expanded
def run_dds_quality_simulation(hand_count=500):
    # Generate 500 random hands
    # Play each with DDS
    # Compare to optimal double-dummy
    # Time: 500 hands × 10 sec = ~83 minutes
```

#### Pros
✅ **Generates own data** - No need for production traffic
✅ **Reproducible** - Can rerun same hands
✅ **Comprehensive** - Tests all scenarios systematically
✅ **Off-production** - Can run on separate server

#### Cons
❌ **Very expensive** - Hours of CPU time
❌ **Not real gameplay** - Synthetic hands
❌ **Blocks server** - Consumes all resources
❌ **Slow feedback** - Takes hours to complete
❌ **Inference mismatch** - Random hands ≠ real distribution

#### Resource Metrics
- **CPU**: 90-100% for 1-3 hours
- **Memory**: 100-200MB
- **Disk**: 50-100MB (results JSON)
- **Network**: 0
- **API latency**: N/A (blocks production)

**Simulation Budget:**
- 100 hands: ~17 minutes
- 500 hands: ~83 minutes (1.4 hours)
- 1000 hands: ~166 minutes (2.8 hours)

#### Cost-Benefit Score: **4/10**
Best for: Pre-deployment testing, isolated quality checks

---

## Approach 6: Sparse Deep Sampling

### Load Impact: **LOW** (2-5% overhead) ⭐ EXCELLENT COMPROMISE

#### Implementation
```python
# Log only 10% of hands, but with complete detail
import random

if random.random() < 0.10:  # 10% sampling
    log_complete_hand_analysis(
        all_4_hands=state.deal,
        all_plays=trick_history,
        ai_decisions=ai_reasoning,
        outcome=final_result
    )
```

#### Pros
✅ **Low overhead** - Only 10% of hands logged
✅ **Rich data** - Complete game state when logged
✅ **Representative** - Random sampling is statistically valid
✅ **Adjustable** - Can tune sampling rate (5%, 10%, 20%)
✅ **Balanced** - Between minimal and comprehensive
✅ **Real gameplay** - Captures actual user patterns

#### Cons
❌ **Smaller dataset** - Takes 10× longer to accumulate N samples
❌ **Implementation** - Need complete hand serialization
❌ **Variable overhead** - Spikes when logging occurs

#### Resource Metrics
- **CPU**: +2% average (occasional 20ms spikes)
- **Memory**: +50KB per logged hand (transient)
- **Disk**: ~5KB per logged hand
  - 100 hands: 500KB
  - 1000 hands: 5MB
- **Network**: 0
- **API latency**: +0ms average, +20ms when sampling triggers

#### Cost-Benefit Score: **8.5/10**
Best for: Balancing detail with performance

---

## Recommended Strategy: Hybrid Approach

### Phase 1: Immediate (Week 1)
1. **Approach 1 (Minimal Logging)** + **Approach 4 (Dashboard)**
   - Total overhead: 1-3%
   - Captures: AI level, card played, solve time, fallback flag
   - Visibility: Real-time dashboard

### Phase 2: Short-term (Week 2-4)
2. **Approach 6 (Sparse Deep Sampling)** at 10%
   - Overhead: +2% more = 3-5% total
   - Captures: Complete game state for deep analysis
   - Dataset: 10-50 hands/week with full detail

### Phase 3: Monthly (Ongoing)
3. **Approach 2 (Batch Analysis)** weekly on Sundays 3am
   - Overhead: 10 minutes/week off-peak
   - Analysis: Quality metrics, trend detection
   - Reporting: Weekly email with insights

### Total Resource Impact
- **Real-time overhead**: 3-5% (Approaches 1 + 4 + 6)
- **Weekly batch**: 10 minutes off-peak (Approach 2)
- **Storage growth**: ~1-2MB/week
- **API latency**: +1-2ms average

---

## Alternative: If Production Has High Traffic

If you scale to 100+ hands/day:

### Change Strategy to:
1. **Approach 1 only** (minimal logging)
2. **Approach 4** (dashboard) with Redis caching
3. **Skip Approach 6** (too much overhead at scale)
4. **Use Approach 2** monthly instead of weekly

At high scale:
- Overhead drops to <1% (database inserts are cheap)
- More data collected passively
- Can afford longer analysis intervals

---

## Cost Comparison Table

| Approach | Real-time Overhead | Storage/Week | Setup Time | Data Quality | Scalability |
|----------|-------------------|--------------|------------|--------------|-------------|
| 1. Logging | 0.5% | 1-5MB | 1 hour | Medium | Excellent |
| 2. Batch Analysis | 0% (off-peak) | 2MB | 4 hours | High | Good |
| 3. A/B Testing | 15-30% | 10MB | 8 hours | Very High | Poor |
| 4. Dashboard | 1% | 0MB | 2 hours | Low | Excellent |
| 5. Simulation | 100% (blocking) | 50-100MB | 1 hour | Medium | N/A |
| 6. Sparse Sampling | 2-5% | 5-10MB | 3 hours | High | Good |

---

## Decision Matrix

**Choose Approach 1 + 4 if:**
- ✅ Low traffic (< 10 hands/day)
- ✅ Want minimal impact
- ✅ Need real-time monitoring
- ✅ Can wait for data accumulation

**Add Approach 6 if:**
- ✅ Want detailed analysis
- ✅ Can tolerate 2-5% overhead
- ✅ Need faster insights

**Use Approach 2 if:**
- ✅ Have accumulated logs (from Approach 1)
- ✅ Can schedule off-peak processing
- ✅ Want rigorous quality metrics

**Avoid Approach 3 + 5 unless:**
- ❌ One-time testing only
- ❌ Separate test environment available
- ❌ Not time-sensitive

---

## Render.com Specific Considerations

**Free Tier Limits:**
- CPU: Shared, burstable
- Memory: 512MB
- Disk: Ephemeral (resets on deploy)
- Sleep: After 15 min inactivity

**Implications:**
1. **Must use external storage** (Render Postgres or external DB)
2. **Batch jobs should complete quickly** (< 15 min to avoid sleep)
3. **Can't rely on in-memory caching** (use Redis or DB)
4. **Approach 2 limited** to 100 hands max (~10 min)

**Recommended for Render:**
- ✅ Approach 1 with Postgres storage
- ✅ Approach 4 with DB-backed cache
- ⚠️ Approach 2 limited to 100 hands
- ❌ Approaches 3 + 5 too resource-intensive

---

## Final Recommendation

### Start Here (Minimal Viable Monitoring):
```python
# 1. Add to server.py after line 1538
def log_ai_play(card, position, ai_level, solve_time, fallback):
    cursor.execute("""
        INSERT INTO ai_plays
        (timestamp, card, position, ai_level, solve_ms, used_fallback)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now(), f"{card.rank}{card.suit}",
          position, ai_level, solve_time, fallback))

# 2. Add dashboard endpoint
@app.route("/api/dds-health")
def dds_health():
    return {
        "plays_24h": query("SELECT COUNT(*) FROM ai_plays WHERE timestamp > ?"),
        "avg_solve_ms": query("SELECT AVG(solve_ms) FROM ai_plays"),
        "fallback_rate": query("SELECT AVG(used_fallback) FROM ai_plays"),
        "dds_available": DDS_AVAILABLE and PLATFORM_ALLOWS_DDS
    }
```

**Total implementation time:** 1-2 hours
**Total overhead:** <1%
**Immediate value:** Real-time DDS health monitoring
**Long-term value:** Dataset for quality analysis

Then add Approach 6 (sparse sampling) after 1-2 weeks once baseline is stable.
