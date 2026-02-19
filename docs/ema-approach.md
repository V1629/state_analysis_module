# EMA Approach — Technical Design Document

> **Emotional State Analysis Module** — Exponential Moving Average Implementation

---

## Table of Contents

1. [What is EMA](#what-is-ema)
2. [Why EMA for Emotional State Tracking](#why-ema-for-emotional-state-tracking)
3. [Core Formula](#core-formula)
4. [Learning Rate Behavior](#learning-rate-behavior)
5. [Application to Emotional States](#application-to-emotional-states)
6. [Adaptive Learning Rate](#adaptive-learning-rate)
7. [Per-User Parameter Evolution](#per-user-parameter-evolution)
8. [Comparison with Previous Approach](#comparison-with-previous-approach)

---

## What is EMA

**Exponential Moving Average (EMA)** is a time-series smoothing technique that blends new observations with accumulated history using a **learning rate** (α). Unlike simple averaging, EMA gives exponentially decreasing weight to older data points, making it perfect for adaptive systems.

### Core Concept

```
EMA = α × NewValue + (1 - α) × PreviousEMA
```

- **α close to 1.0**: Trusts new data heavily (fast adaptation, volatile)
- **α close to 0.0**: Trusts history heavily (slow adaptation, stable)

### Visual Representation

```
Time →  t₁    t₂    t₃    t₄    t₅
Data:   0.8   0.2   0.6   0.3   0.7

EMA (α=0.3):
t₁: 0.8 (initial)
t₂: 0.3×0.2 + 0.7×0.8 = 0.62
t₃: 0.3×0.6 + 0.7×0.62 = 0.61
t₄: 0.3×0.3 + 0.7×0.61 = 0.52
t₅: 0.3×0.7 + 0.7×0.52 = 0.57

Notice: Smooth transitions, no abrupt changes
```

---

## Why EMA for Emotional State Tracking

### Benefits for Emotional Analysis

1. **Smooth Transitions**: Emotional states don't jump abruptly
2. **Memory**: Recent emotions matter more, but history isn't forgotten
3. **Noise Filtering**: Occasional outliers don't dominate
4. **Personalization**: Can adapt learning rate per user
5. **Efficiency**: O(1) computation per update

### Comparison with Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Simple Average** | Easy to compute | All history weighted equally |
| **Rolling Window** | Recent focus | Hard cutoff, no smooth decay |
| **EMA** | Smooth decay, efficient | Requires tuning α |
| **Weighted Average** | Flexible | Complex weight management |

---

## Core Formula

### EMA Update

```python
def ema_update(old_value: float, new_value: float, alpha: float) -> float:
    """
    Exponential Moving Average update
    
    Args:
        old_value: Previous EMA value
        new_value: New observed value
        alpha: Learning rate (0 < α ≤ 1)
    
    Returns:
        Updated EMA value
    """
    return alpha * new_value + (1 - alpha) * old_value
```

### Mathematical Properties

**Effective Memory Window:**
```
Window ≈ 1/α
```

**Weight of observation n steps ago:**
```
Weight(n) = α × (1 - α)^n
```

**Example (α = 0.15):**
| Steps Ago | Weight | Interpretation |
|-----------|--------|----------------|
| 0 (current) | 15% | Primary influence |
| 1 | 12.75% | Recent |
| 2 | 10.84% | Recent |
| 5 | 6.65% | Moderate |
| 10 | 2.95% | Low |
| 20 | 0.52% | Minimal |

---

## Learning Rate Behavior

### Learning Rate (α) Reference Table

| α | Effective Window | Behavior | Use Case |
|---|------------------|----------|----------|
| **0.02** | ~50 updates | Very slow, deep baseline | Long-term personality |
| **0.05** | ~20 updates | Slow, stable tracking | Behavioral trends |
| **0.10** | ~10 updates | Moderate responsiveness | General tracking |
| **0.15** | ~7 updates | Responsive | Short-term mood |
| **0.25** | ~4 updates | Fast adaptation | Reactive systems |
| **0.30** | ~3 updates | Very reactive | Quick changes |

### In This Module

| State | α | Window | Purpose |
|-------|---|--------|---------|
| Short-Term | 0.15 | ~7 msgs | Current mood |
| Long-Term | 0.02 | ~50 msgs | Personality baseline |

---

## Application to Emotional States

### Short-Term State (α = 0.15)

Captures current mood with fast adaptation:

```python
def update_short_term(self, emotions: Dict[str, float], impact_score: float):
    alpha = 0.15
    
    for emotion in ALL_EMOTIONS:
        old_value = self.short_term_state[emotion]
        new_value = emotions.get(emotion, 0.0)
        
        # EMA update
        self.short_term_state[emotion] = alpha * new_value + (1 - alpha) * old_value
```

**Example Evolution:**
```
Messages: "I'm happy" → "Feel great" → "A bit tired" → "Still okay"
joy:      0.15       → 0.28        → 0.24         → 0.22
```

### Mid-Term State (Rolling Window)

Uses a rolling window of the last N messages:

```python
def update_mid_term(self, emotions: Dict[str, float]):
    window_size = 15
    recent_history = self.message_history[-window_size:]
    
    for emotion in ALL_EMOTIONS:
        total = sum(msg['emotions'].get(emotion, 0) for msg in recent_history)
        self.mid_term_state[emotion] = total / len(recent_history)
```

### Long-Term State (α = 0.02)

Captures stable personality baseline:

```python
def update_long_term(self, emotions: Dict[str, float]):
    alpha = 0.02
    
    for emotion in ALL_EMOTIONS:
        old_value = self.long_term_state[emotion]
        new_value = emotions.get(emotion, 0.0)
        
        # Very slow adaptation
        self.long_term_state[emotion] = alpha * new_value + (1 - alpha) * old_value
```

**Example Evolution (100 messages):**
```
Initial: neutral = 0.5
After 100 msgs of mixed emotions:
  neutral = 0.42 (gradual shift)
```

---

## Adaptive Learning Rate

### Concept

As profiles mature, the learning rate should decrease to stabilize:

```python
def get_effective_alpha(base_alpha: float, message_count: int, decay_constant: int = 200) -> float:
    """
    Calculate adaptive learning rate based on profile maturity
    
    Formula: effective_α = base_α / (1 + message_count / decay_constant)
    """
    return base_alpha / (1 + message_count / decay_constant)
```

### Evolution Over Time

| Messages | Base α | Effective α | Interpretation |
|----------|--------|-------------|----------------|
| 0 | 0.15 | 0.150 | Full responsiveness |
| 50 | 0.15 | 0.120 | Learning phase |
| 100 | 0.15 | 0.100 | Moderate stability |
| 200 | 0.15 | 0.075 | Stabilizing |
| 500 | 0.15 | 0.043 | Highly stable |

### Visualization

```
Effective α
    ▲
0.15│●
    │ ●
0.10│   ●●
    │      ●●●
0.05│          ●●●●●●
    │                  ●●●●●●●●●●
    └─────────────────────────────→ Messages
    0   100   200   300   400   500
```

---

## Per-User Parameter Evolution

### Evolving Parameters

The following parameters can evolve via EMA to personalize the system:

| Parameter | Initial | α | Purpose |
|-----------|---------|---|---------|
| `entropy_penalty_coeff` | 0.3 | 0.10 | Personalize mixed-emotion handling |
| `recurrence_step` | 0.3 | 0.15 | Learn escalation vs desensitization |
| `behavior_alpha` | 0.2 | 0.10 | Typing speed sensitivity |
| `similarity_threshold` | 0.2 | 0.10 | Incident matching sensitivity |

### Example: Entropy Penalty Evolution

```python
# For a user who consistently expresses mixed emotions
# The entropy penalty coefficient should decrease

observed_entropy = calculate_entropy(emotions)
alpha = 0.10

self.entropy_penalty_coeff = (
    alpha * observed_entropy + 
    (1 - alpha) * self.entropy_penalty_coeff
)
```

**Result:**
- User with pure emotions: penalty_coeff stays ~0.3
- User with mixed emotions: penalty_coeff increases to ~0.5
- Penalty is then calculated relative to user's baseline

---

## Comparison with Previous Approach

### Previous: Rule-Based Adjustments

```python
# Old approach (problematic)
if emotion_intensity > 0.7:
    weight += 0.05
elif emotion_intensity < 0.3:
    weight -= 0.05
```

**Problems:**
1. Memoryless — restarts from initial
2. Fixed step size — doesn't reflect magnitude
3. Dead zones — no adjustment for 0.3-0.7
4. Binary decisions — no gradual change

### Current: EMA-Based

```python
# New approach
weight = alpha * observed_weight + (1 - alpha) * weight
```

**Benefits:**
1. Continuous memory — builds on previous state
2. Proportional response — reflects actual values
3. No dead zones — always adjusts
4. Smooth evolution — gradual changes

### Side-by-Side Comparison

| Aspect | Rule-Based | EMA |
|--------|------------|-----|
| Memory | None | Exponential decay |
| Step size | Fixed (±0.05) | Proportional |
| Thresholds | 0.3, 0.7 | None |
| Dead zones | 40% of range | None |
| Trajectory | Sawtooth | Smooth curve |
| Personalization | Limited | Full range |

### Trajectory Comparison

```
Rule-Based:          EMA:
Value                Value
  ▲                    ▲
  │  ┌──┐              │     ╭──────
  │──┘  └──┐           │   ╭╯
  │        └──┐        │ ╭╯
  └───────────────→    └───────────────→
      Time                 Time
```

---

## Implementation Guidelines

### Choosing α Values

1. **Fast response needed**: α = 0.15-0.25
2. **Stable baseline**: α = 0.02-0.05
3. **General tracking**: α = 0.10

### Initialization

```python
# Initialize states with neutral values
for emotion in ALL_EMOTIONS:
    self.short_term_state[emotion] = 0.0
    self.mid_term_state[emotion] = 0.0
    self.long_term_state[emotion] = 0.0
```

### Edge Cases

```python
# Handle missing emotions
new_value = emotions.get(emotion, 0.0)  # Default to 0

# Clamp extreme values
result = max(0.0, min(1.0, ema_result))

# Handle first message (no history)
if self.message_count == 0:
    self.short_term_state = emotions.copy()
```

---

## Summary

EMA provides a mathematically sound approach to emotional state tracking that:

- ✅ Preserves memory of past emotional patterns
- ✅ Smoothly adapts to new information
- ✅ Allows per-state and per-user customization
- ✅ Scales efficiently with O(1) updates
- ✅ Avoids abrupt changes and dead zones

The key insight is matching the learning rate (α) to the desired temporal behavior: fast for current mood, slow for personality baseline.

---

## Related Documentation

- [Data Flow](./data-flow.md) — How EMA fits in the pipeline
- [User Profile Module](./modules/user-profile.md) — EMA implementation
- [Configuration](./configuration.md) — Tuning parameters
