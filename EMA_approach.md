# 📊 EMA (Exponential Moving Average) Approach for Emotional State Analysis

**Technical Design Document**  
**Version:** 1.0  
**Last Updated:** 2026-02-17

---

## 📑 Table of Contents

1. [What EMA Is — The Core Idea](#1-what-ema-is--the-core-idea)
2. [Problems with the Current System](#2-problems-with-the-current-system)
3. [Current System Analysis](#3-current-system-analysis)
4. [EMA Applied to All 14 Parameter Groups](#4-ema-applied-to-all-14-parameter-groups)
   - [Parameters 1-4: Adaptive Weights](#parameters-1-4-adaptive-weights-user_profilepy)
   - [Parameters 5-6: Typing Speed Baseline](#parameters-5-6-typing-speed-baseline-orchestratorpy)
   - [Parameter 7: Entropy Penalty Coefficient](#parameter-7-entropy-penalty-coefficient-orchestratorpy)
   - [Parameter 8: Recurrence Boost Step](#parameter-8-recurrence-boost-step-orchestratorpy)
   - [Parameter 9: State Impact Multipliers](#parameter-9-state-impact-multipliers--15-values-orchestratorpy)
   - [Parameter 10: Behavior Multiplier Influence Cap](#parameter-10-behavior-multiplier-influence-cap-orchestratorpy)
   - [Parameter 11: Short-Term State](#parameter-11-short-term-state--27-emotions-user_profilepy)
   - [Parameter 12: Mid-Term Rolling Window](#parameter-12-mid-term-rolling-window--27-emotions-user_profilepy)
   - [Parameter 13: Long-Term Frequency State](#parameter-13-long-term-frequency-state--27-emotions-user_profilepy)
   - [Parameter 14: Similarity Threshold](#parameter-14-similarity-threshold-for-incident-detection-orchestratorpy)
5. [Adaptive α — Making EMA Itself Evolve Over Time](#5-adaptive-α--making-ema-itself-evolve-over-time)
6. [Full Inventory Table](#6-full-inventory-table)
7. [Suggested Implementation Order](#7-suggested-implementation-order)

---

## 1. What EMA Is — The Core Idea

**Exponential Moving Average (EMA)** is a time-series smoothing technique that blends new observations with accumulated history using a **learning rate** (α). Unlike simple averaging, EMA gives exponentially decreasing weight to older data points, making it perfect for adaptive systems.

### Core EMA Formula

```
V^(t) = α × V^(new) + (1 - α) × V^(t-1)
```

**Where:**
- **V^(t)** = the smoothed value after this update
- **V^(new)** = the raw observed value right now (from current message)
- **V^(t-1)** = the previously stored smoothed value
- **α** = learning rate — how much "new evidence" matters vs "accumulated history"

### 🎯 Learning Rate (α) Behavior

| α | Effective Memory Window | Behavior |
|---|---|---|
| **0.02** | ~50 updates | Very slow, deep baseline |
| **0.05** | ~20 updates | Slow, stable tracking |
| **0.10** | ~10 updates | Moderate responsiveness |
| **0.15** | ~7 updates | Responsive |
| **0.25** | ~4 updates | Fast adaptation |
| **0.30** | ~3 updates | Very reactive |

**💡 Interpretation:**
- **α close to 1.0** → Trusts new data heavily (fast adaptation, volatile, forgets history quickly)
- **α close to 0.0** → Trusts history heavily (slow adaptation, stable, deep baseline)

The "effective memory window" is approximately **1/α** — the number of recent updates that significantly influence the current value. For example, with α=0.10, the last ~10 updates carry most of the weight.

---

## 2. Problems with the Current System

The current system in `user_profile.py` uses a **rule-based step-adjustment approach** with hard thresholds and clamps in `_calculate_adaptive_weights()`. This creates **8 major problems**:

### ❌ Problem 1: Memoryless / No Momentum

**What's wrong:**  
Every 10 messages, the system **restarts from `INITIAL_WEIGHTS`**, not from the current adaptive weights.

```python
# From user_profile.py line 453
new_weights = INITIAL_WEIGHTS.copy()  # ❌ Starts fresh every time!
```

**Impact:**  
The system can **never gradually evolve** — it either jumps by ±0.05 or stays at initial. After 100 messages of a very emotional user, if the pattern continues, the weights just stay frozen at their last jump. If the pattern changes, they jump back to initial, then re-adjust. There's no smooth trajectory.

---

### ❌ Problem 2: Fixed Step Size

**What's wrong:**  
The ±0.05 / ±0.03 adjustments are **constant** regardless of how extreme the pattern is.

```python
# From user_profile.py lines 458-463
if emotion_intensity > 0.7:
    new_weights['emotion_intensity'] = min(0.55, INITIAL_WEIGHTS['emotion_intensity'] + 0.05)
elif emotion_intensity < 0.3:
    new_weights['emotion_intensity'] = max(0.35, INITIAL_WEIGHTS['emotion_intensity'] - 0.05)
```

**Impact:**  
A user with `emotion_intensity_avg = 0.95` (extremely emotional) gets the **same +0.05 adjustment** as one with `0.71` (barely over threshold). The system can't express "this user is **way** more emotional than average."

---

### ❌ Problem 3: No Time Decay on Patterns

**What's wrong:**  
`_analyze_chat_patterns()` treats **all message history equally**.

```python
# From user_profile.py lines 375-382
for msg_entry in self.message_history:  # ❌ All messages treated equally!
    emotions = msg_entry.get('emotions_detected', {})
    for emotion, score in emotions.items():
        emotion_frequency[emotion] += 1
        emotion_intensity_sum += score
```

**Impact:**  
A user who was **very emotional 200 messages ago** but **calm recently** will still see inflated `emotion_intensity_avg`. The system can't distinguish recent behavioral changes from historical patterns.

---

### ❌ Problem 4: Hard Threshold Buckets

**What's wrong:**  
Binary decisions (e.g., `> 0.7` vs `< 0.3`) with a **dead zone in `[0.3, 0.7]`** where no adjustment happens at all.

```python
# From user_profile.py lines 458-463
if emotion_intensity > 0.7:      # Only fires if > 0.7
    ...
elif emotion_intensity < 0.3:    # Only fires if < 0.3
    # Else: NO CHANGE for 0.3-0.7 range
```

**Impact:**  
- User at 0.69 → no adjustment
- User at 0.71 → +0.05 jump
- User at 0.50 → stuck at initial forever

**40% of the value range** triggers no learning at all.

---

### ❌ Problem 5: Tight Clamp Ranges

**What's wrong:**  
The min/max clamps (e.g., emotion can only drift `0.35–0.55`) **limit the system's ability to truly personalize**.

```python
# From user_profile.py
new_weights['emotion_intensity'] = min(0.55, ...)  # ❌ Can never exceed 0.55
new_weights['emotion_intensity'] = max(0.35, ...)  # ❌ Can never go below 0.35
```

**Impact:**  
A user who is **consistently extremely emotional** (e.g., grief counseling, trauma recovery) can't push `w_emotion_intensity` above 0.55. The system **artificially caps** personalization, preventing it from truly adapting to outlier users.

---

### ❌ Problem 6: No Per-User Learning on Constants

**What's wrong:**  
Parameters like `entropy_penalty = 0.3`, `recurrence_step = 0.3`, `behavior_alpha = 0.2`, and `similarity_threshold = 0.2` are **hardcoded for all users**.

```python
# From orchestrator.py line 100
entropy_penalty = normalized_entropy * 0.3  # ❌ Same for everyone

# From orchestrator.py line 125
boost = 1 + (max(0, incident_count - 1) * 0.3)  # ❌ Same for everyone

# From orchestrator.py line 209
alpha = 0.2  # ❌ Same for everyone

# From orchestrator.py line 416
similarity_threshold=0.2  # ❌ Same for everyone
```

**Impact:**  
- Some users express **mixed emotions** frequently (e.g., complex grief = sadness + gratitude + relief). They get penalized heavily by entropy. Others are emotionally "pure" (e.g., clinical depression = just sadness). One-size-fits-all doesn't work.
- Some users **escalate** with repetition (trauma triggers), others **desensitize** (venting reduces emotion). Current system assumes escalation for everyone.

---

### ❌ Problem 7: O(N) Recomputation

**What's wrong:**  
Mid-term recomputes from **last 15 messages** every update. Long-term scans **entire history** every update.

```python
# From user_profile.py (mid-term update logic)
# Recomputes entire window every time

# From user_profile.py (long-term update logic)
# Scans all messages in history
```

**Impact:**  
- **Linear time complexity** — cost grows with user engagement
- At 1,000 messages, long-term updates scan all 1,000 messages **every single time**
- Inefficient and doesn't scale

---

### ❌ Problem 8: Cliff Effects

**What's wrong:**  
The rolling window has a **hard boundary**: message 16 suddenly drops off completely from mid-term state instead of fading gradually.

**Impact:**  
A strong emotional event exactly 15 messages ago has **full weight**. The same event at 16 messages ago has **zero weight**. This creates discontinuities in the emotional profile — sudden drops as messages age out of the window.

---

### 📋 Current System's Rule Table

The current `_calculate_adaptive_weights()` applies these rules:

| Pattern Detected | Adjustment | Clamp Range |
|---|---|---|
| `emotion_intensity_avg > 0.7` | `w_ei += 0.05` | max `0.55` |
| `emotion_intensity_avg < 0.3` | `w_ei -= 0.05` | min `0.35` |
| `recency_pattern == 'recent_focused'` | `w_rw += 0.05` | max `0.40` |
| `recency_pattern == 'past_focused'` | `w_rw -= 0.05` | min `0.20` |
| `repetition_count > 3` | `w_rb += 0.05` | max `0.25` |
| `repetition_count == 0` | `w_rb -= 0.05` | min `0.05` |
| `temporal_ref_ratio < 0.3` | `w_tc -= 0.03` | min `0.05` |
| `temporal_specificity > 0.8` | `w_tc += 0.03` | max `0.15` |

These rules are **memoryless, discrete, and inflexible** — the opposite of what adaptive learning should be.

---

## 3. Current System Analysis

### 🏗️ Current Architecture

The system is split across two main files:

#### **`user_profile.py`** — Adaptive Weights

Defines the **initial weight hierarchy**:

```python
INITIAL_WEIGHTS = {
    'emotion_intensity': 0.45,      # Highest - emotion is primary
    'recency_weight': 0.30,         # High - recent events matter
    'recurrence_boost': 0.15,       # Medium - patterns matter
    'temporal_confidence': 0.10     # Lowest - exact timing less critical
}
```

These weights control how much each factor contributes to the **compound impact score**.

#### **`orchestrator.py`** — Compound Impact Formula

Calculates the final impact score using a **weighted sum approach**:

```python
# From orchestrator.py lines 280-292
base_impact = (adaptive_weights['emotion_intensity'] * emotion_intensity) +
              (adaptive_weights['recency_weight'] * recency_weight) +
              (adaptive_weights['temporal_confidence'] * temporal_confidence) +
              (adaptive_weights['recurrence_boost'] * normalized_recurrence)

final_impact = base_impact * behavior_multiplier
```

**Where:**
- `w_ei` = weight for emotion intensity
- `w_rw` = weight for recency (how recent the event is)
- `w_tc` = weight for temporal confidence (how certain we are about timing)
- `w_rb` = weight for recurrence (repeated incidents boost impact)
- `behavior_multiplier` = typing speed deviation (0.8–1.2)

### 📊 Workflow

1. **Message arrives** → Extract emotions, temporal references
2. **Calculate factors**:
   - `emotion_intensity` = max emotion probability × (1 - entropy penalty)
   - `recency_weight` = exponential decay based on days ago
   - `temporal_confidence` = confidence in temporal extraction
   - `recurrence_boost` = 1.0 + (incident_count - 1) × 0.3
3. **Compute compound impact** using weighted sum
4. **Update emotional states** (short/mid/long term)
5. **Every 10 messages**: Recalculate adaptive weights

---

## 4. EMA Applied to All 14 Parameter Groups

Below, we detail **how EMA replaces the current approach for each of the 14 parameter groups** in the system. Each section includes:
- Current implementation
- Problems
- EMA replacement formula
- Comparison table
- Concrete benefits

---

### Parameters 1-4: Adaptive Weights (`user_profile.py`)

#### 🎯 The 4 Adaptive Weights

| Parameter | Current Method | Proposed α |
|---|---|---|
| `emotion_intensity` | If/else ±0.05 | **0.12** |
| `recency_weight` | If/else ±0.05 | **0.15** |
| `recurrence_boost` | If/else ±0.05 | **0.25** |
| `temporal_confidence` | If/else ±0.03 | **0.20** |

#### 📝 Current Code

```python
# From user_profile.py lines 453-496
new_weights = INITIAL_WEIGHTS.copy()  # ❌ Restart from initial

if emotion_intensity > 0.7:
    new_weights['emotion_intensity'] = min(0.55, INITIAL_WEIGHTS['emotion_intensity'] + 0.05)
# ... similar for other weights
```

#### ❌ What's Wrong

- **Memoryless**: Starts from `INITIAL_WEIGHTS` every time (see Problem 1)
- **Fixed steps**: ±0.05 regardless of magnitude (see Problem 2)
- **Dead zones**: No adjustment for values in `[0.3, 0.7]` (see Problem 4)
- **Tight clamps**: Artificially limits personalization (see Problem 5)

#### ✅ EMA Replacement Formula

For each weight `w_i`, calculate the **observed signal** from current message patterns:

```
observed_signal_i = contribution_i / (Σ all_contributions)
```

**Example for `w_emotion_intensity`:**

```
observed_emotion_signal = Ī_emotion / (Ī_emotion + S̄_recency + R̄_repetition + C̄_temporal)
```

Where:
- `Ī_emotion` = average emotion intensity from message
- `S̄_recency` = average recency weight from message
- `R̄_repetition` = normalized recurrence boost
- `C̄_temporal` = temporal confidence

Then apply **EMA**:

```
w_i^(t) = α_i × w_i^(observed) + (1 - α_i) × w_i^(t-1)
```

**Normalize** weights to sum to 1.0:

```
w_i^(normalized) = w_i^(t) / Σ(all weights)
```

#### 📊 Comparison Table

| Aspect | Current System | With EMA |
|---|---|---|
| **After 10 msgs: user very emotional** | Jumps +0.05 from 0.45→0.50, stuck there | Smoothly rises 0.45→0.456→0.463→... proportional to how emotional |
| **After 10 msgs: user moderately emotional (0.5 avg)** | No change (dead zone 0.3–0.7) | Still adjusts slightly toward observed proportion |
| **User was emotional for 100 msgs, then becomes calm** | Still stuck at +0.05 because if/else re-fires from INITIAL | Gradually decays back: 0.50→0.49→0.48→... |
| **Weight trajectory** | Saw-tooth (jump → static → jump) | Smooth exponential curve |
| **Handles outliers** | Capped at ±0.05, max 0.55 | Can reach any value based on consistent patterns |
| **Reflects recent changes** | Only if threshold crossed | Continuous adjustment every message |

#### 🎁 Concrete Benefits

1. **Smooth, proportional learning**: Weight changes reflect the **magnitude** of the pattern, not just binary "yes/no"
2. **No dead zones**: Even moderate patterns (0.4–0.6) contribute to learning
3. **Momentum preservation**: Weights evolve from their current state, not from initial
4. **Natural decay**: If a user's behavior changes, weights gradually adapt back
5. **No artificial caps**: The system can truly personalize to extreme users

---

### Parameters 5-6: Typing Speed Baseline (`orchestrator.py`)

#### 🎯 The 2 Typing Speed Parameters

| Parameter | Current Method | Status |
|---|---|---|
| `typing_speed_mean` | ✅ Already uses EMA (β=0.05) | Keep as-is |
| `typing_speed_std` | ❌ Never updated, stays at 0.5 | Needs EMA |

#### 📝 Current Code

```python
# From orchestrator.py lines 31-32
typing_speed_mean = 1.0  # Default typing speed
typing_speed_std = 0.5   # ❌ NEVER UPDATED!

# From orchestrator.py lines 228-232 (mean is updated)
@staticmethod
def update_typing_baseline(speed: float) -> None:
    beta = 0.05
    mu = ImpactCalculator.typing_speed_mean
    ImpactCalculator.typing_speed_mean = beta * speed + (1 - beta) * mu
    # ❌ BUT std is never touched!
```

#### ❌ What's Wrong

**Typing speed mean** is already using EMA ✅ — that's good!

**BUT typing speed std** (standard deviation) is **hardcoded at 0.5 forever** ❌. This is used in the behavior multiplier:

```python
# From orchestrator.py lines 205-207
z = (speed - mu) / sigma  # ❌ sigma is always 0.5!
```

**Impact:**  
The z-score (and therefore `behavior_multiplier`) uses a **fake standard deviation**. A user who types at very consistent speeds (low σ) is treated the same as a user with erratic typing (high σ). The multiplier loses its meaning.

#### ✅ EMA Replacement for `std`

Use **Mean Absolute Deviation (MAD)** as a running estimate of spread:

```
σ^(t) = β_σ × |speed - μ^(t)| + (1 - β_σ) × σ^(t-1)
```

**Where:**
- `β_σ = 0.05` (same as mean for consistency)
- `|speed - μ^(t)|` = absolute deviation from current mean
- `σ^(t-1)` = previous standard deviation estimate

**Implementation:**

```python
@staticmethod
def update_typing_baseline(speed: float) -> None:
    beta = 0.05
    
    # Update mean (already done)
    mu = ImpactCalculator.typing_speed_mean
    ImpactCalculator.typing_speed_mean = beta * speed + (1 - beta) * mu
    
    # ✅ NEW: Update std using EMA on MAD
    sigma = ImpactCalculator.typing_speed_std
    deviation = abs(speed - mu)
    ImpactCalculator.typing_speed_std = beta * deviation + (1 - beta) * sigma
```

#### 🎁 Concrete Benefits

1. **True z-scores**: The behavior multiplier reflects **actual deviation** from the user's typing pattern
2. **Per-user calibration**: Users with consistent typing get small σ → larger z-scores for deviations → stronger behavior multiplier
3. **Users with erratic typing** get large σ → smaller z-scores → weaker behavior multiplier (because typing speed isn't a reliable signal for them)
4. **Adaptive sensitivity**: The system learns whether typing speed is a meaningful emotional signal for each user

---

### Parameter 7: Entropy Penalty Coefficient (`orchestrator.py`)

#### 🎯 Entropy Penalty

| Parameter | Current Method | Proposed α |
|---|---|---|
| `entropy_penalty_coeff` | Static `0.3` | **0.10** |

#### 📝 Current Code

```python
# From orchestrator.py lines 86-103
entropy = 0.0
for p in emotions_dict.values():
    if p > 0:
        entropy -= p * math.log(p)

n_emotions = len(emotions_dict)
if n_emotions > 1:
    normalized_entropy = entropy / math.log(n_emotions)
else:
    normalized_entropy = 0.0

# ❌ HARDCODED COEFFICIENT
entropy_penalty = normalized_entropy * 0.3

intensity = max_prob * (1 - entropy_penalty)
```

#### ❌ What's Wrong

The **penalty coefficient `0.3`** is the same for **all users** (see Problem 6).

**Impact:**
- **User A** (clinical depression) → always expresses pure sadness (low entropy) → no penalty ✅
- **User B** (complex grief) → mixes sadness + gratitude + relief (high entropy) → **30% penalty** ❌
- User B's mixed emotions are **natural and valid**, not "uncertain" — but the system treats them as less confident

#### ✅ EMA Replacement

Learn the **typical entropy level** for each user:

```
penalty_coeff^(t) = α_e × H_norm^(current) + (1 - α_e) × penalty_coeff^(t-1)
```

**Where:**
- `α_e = 0.10` (slow learning — entropy style is personality)
- `H_norm^(current)` = normalized entropy of current message
- `penalty_coeff^(t-1)` = previous coefficient (starts at 0.3)

**Then apply penalty relative to user's baseline**:

```
adjusted_penalty = max(0, H_norm^(current) - penalty_coeff^(t))
intensity = max_prob * (1 - adjusted_penalty)
```

#### 🎁 Concrete Benefits

1. **Personalized penalty**: Users who **normally** express mixed emotions aren't penalized for their natural style
2. **Anomaly detection**: If a usually-pure-emotion user suddenly shows high entropy, that gets flagged
3. **Conversely**: If a usually-mixed user shows unusually pure emotion, that's also notable
4. **Fair comparison**: The system compares each user to **their own baseline**, not a global standard

---

### Parameter 8: Recurrence Boost Step (`orchestrator.py`)

#### 🎯 Recurrence Boost Step

| Parameter | Current Method | Proposed α |
|---|---|---|
| `recurrence_step` | Static `0.3` | **0.15** |

#### 📝 Current Code

```python
# From orchestrator.py lines 107-126
@staticmethod
def calculate_recurrence_boost(incident_count: int) -> float:
    # ❌ HARDCODED STEP
    boost = 1 + (max(0, incident_count - 1) * 0.3)
    return min(2.5, boost)
```

**Example:**
- 1st mention: boost = 1.0
- 2nd mention: boost = 1.3 (+30%)
- 3rd mention: boost = 1.6 (+60%)
- Cap at 2.5

#### ❌ What's Wrong

The **`0.3` step is the same for all users** (see Problem 6).

**Impact:**
- **User C** (trauma survivor): Mentions traumatic event repeatedly → emotion **escalates** → step should be **higher** (e.g., 0.5)
- **User D** (venting): Repeats complaints → emotion **desensitizes** (catharsis effect) → step should be **lower** (e.g., 0.1 or even negative)

The current system **assumes everyone escalates** at the same rate.

#### ✅ EMA Replacement

Learn the **actual recurrence impact** from observed data:

```
observed_recurrence_impact = Δ_intensity / Δ_count
```

**Where:**
- `Δ_intensity` = change in emotion intensity when incident repeats
- `Δ_count` = change in recurrence count (usually +1)

**Then apply EMA:**

```
step^(t) = α_r × observed_impact + (1 - α_r) × step^(t-1)
```

**Where:**
- `α_r = 0.15` (moderate learning)
- `observed_impact` = calculated from current vs previous intensity
- `step^(t-1)` = previous step (starts at 0.3)

**Keep the cap at 2.5** as a static safety guardrail.

#### 🎁 Concrete Benefits

1. **Escalation vs desensitization**: System learns whether repetition **increases** or **decreases** emotional impact for each user
2. **Personalized intensity**: Trauma survivors get higher boost, venters get lower/neutral boost
3. **Adaptive over time**: If a user's pattern changes (e.g., therapy helps them process triggers), the step adapts
4. **Safety preserved**: The 2.5 cap prevents runaway escalation

---

### Parameter 9: State Impact Multipliers — 15 values (`orchestrator.py`)

#### 🎯 Impact Map Multipliers

| Age Category | States | Current Method | Proposed α |
|---|---|---|---|
| `recent` | short/mid/long | Static lookup table | **0.08** per cell |
| `medium` | short/mid/long | Static lookup table | **0.08** per cell |
| `distant` | short/mid/long | Static lookup table | **0.08** per cell |
| `future` | short/mid/long | Static lookup table | **0.08** per cell |
| `unknown` | short/mid/long | Static lookup table | **0.08** per cell |

**Total:** 5 categories × 3 states = **15 multipliers**

#### 📝 Current Code

```python
# From orchestrator.py lines 132-176
impact_map = {
    "recent": {
        "short_term": 1.0,    # ❌ STATIC
        "mid_term": 0.6,      # ❌ STATIC
        "long_term": 0.2      # ❌ STATIC
    },
    "medium": {
        "short_term": 0.3,
        "mid_term": 0.9,
        "long_term": 0.5
    },
    "distant": {
        "short_term": 0.05,
        "mid_term": 0.3,
        "long_term": 0.8
    },
    "unknown": {
        "short_term": 0.5,
        "mid_term": 0.5,
        "long_term": 0.3
    },
    "future": {
        "short_term": 0.7,
        "mid_term": 0.4,
        "long_term": 0.0
    }
}
```

#### ❌ What's Wrong

These multipliers are **hardcoded for all users** (see Problem 6).

**Impact:**
- **User E** (PTSD): Distant memories hit **short-term state hard** (intrusive thoughts) → but current system gives only 0.05
- **User F** (reflective): Past events stay in **long-term**, don't affect current mood → 0.8 is too high
- **One-size-fits-all** doesn't capture how temporal distance affects emotional spillover

#### ✅ EMA Replacement

Learn the **actual state changes** from observed impacts:

```
m_(category,state)^(t) = α_m × actual_state_change + (1 - α_m) × m_(category,state)^(t-1)
```

**Where:**
- `α_m = 0.08` (very slow learning — these are structural patterns)
- `actual_state_change` = measured Δ in state value after applying multiplier
- `m_(category,state)^(t-1)` = previous multiplier (starts at current static values)

**Implementation:**

```python
# After updating state with multiplier
actual_short_term_change = new_short_term - old_short_term
expected_change = score * impact_score  # Without multiplier

# Learn multiplier
observed_multiplier = actual_short_term_change / expected_change if expected_change > 0 else 1.0
alpha_m = 0.08
impact_map["recent"]["short_term"] = alpha_m * observed_multiplier + (1 - alpha_m) * impact_map["recent"]["short_term"]
```

#### 🎁 Concrete Benefits

1. **Temporal-emotional spillover**: System learns how **past/future events affect current emotions** for each user
2. **PTSD detection**: Users whose distant memories hit short-term hard will naturally increase the `distant→short` multiplier
3. **Reflective users**: Those who keep past in perspective will decrease spillover multipliers
4. **Personalized architecture**: The **structure** of emotional states adapts to match each user's cognitive patterns

---

### Parameter 10: Behavior Multiplier Influence Cap (`orchestrator.py`)

#### 🎯 Behavior Alpha

| Parameter | Current Method | Proposed α |
|---|---|---|
| `behavior_alpha` | Static `0.2` | **0.10** |

#### 📝 Current Code

```python
# From orchestrator.py lines 205-213
z = (speed - mu) / sigma

# ❌ HARDCODED CAP
alpha = 0.2

behavior_mult = 1 + alpha * math.tanh(abs(z))
return max(0.8, min(1.2, behavior_mult))
```

The `alpha = 0.2` means typing speed can **influence impact by ±20%**.

#### ❌ What's Wrong

The **`0.2` cap is the same for all users** (see Problem 6).

**Impact:**
- **User G**: Typing speed **highly correlated** with emotion (types fast when anxious) → `0.2` is too low, misses signal
- **User H**: Typing speed **uncorrelated** with emotion (just a fast typer) → `0.2` is too high, adds noise

#### ✅ EMA Replacement

Learn the **correlation between typing speed deviation and emotion intensity**:

```
α_behav^(t) = α_b × corr(speed_deviation, emotion_intensity) + (1 - α_b) × α_behav^(t-1)
```

**Where:**
- `α_b = 0.10` (slow learning — this is a personality trait)
- `corr(...)` = running correlation estimate (e.g., using covariance / variance)
- `α_behav^(t-1)` = previous alpha (starts at 0.2)

**Simpler approach** (incremental):

Track: `Σ(z_i × intensity_i)` and `Σ(z_i²)` across messages, then:

```
correlation ≈ Σ(z × intensity) / sqrt(Σ(z²) × Σ(intensity²))
α_behav = 0.5 × |correlation|  # Scale correlation to influence
```

#### 🎁 Concrete Benefits

1. **Signal relevance**: System learns whether typing speed is a **meaningful emotional signal** for each user
2. **High-correlation users**: Get stronger behavior multiplier (up to ±50% if correlation is strong)
3. **Low-correlation users**: Get weaker multiplier (near ±0% if uncorrelated) — ignores typing noise
4. **Automatic feature selection**: The model learns which behavioral signals matter per user

---

### Parameter 11: Short-Term State — 27 emotions (`user_profile.py`)

#### 🎯 Short-Term Emotional State

| Parameter | Current Method | Proposed α |
|---|---|---|
| `short_term_state` (27 emotions) | Additive accumulation | **0.30** per emotion |

#### 📝 Current Code

```python
# From user_profile.py (short-term update logic)
# Current: pure additive
for emotion, weighted_impact in state_updates.items():
    self.short_term_state[emotion] += weighted_impact['short_term']
```

#### ❌ What's Wrong

**Pure additive accumulation** means:
- Values **grow unbounded** unless manually reset
- **No natural decay**: If user was sad 5 messages ago but now happy, sadness stays inflated
- **Requires periodic normalization** or reset logic (added complexity)

#### ✅ EMA Replacement

Replace additive with **EMA** for natural decay:

```
S_emotion^(t) = α_st × impact_emotion^(new) + (1 - α_st) × S_emotion^(t-1)
```

**Where:**
- `α_st = 0.30` (fast learning for short-term state)
- `impact_emotion^(new)` = current message's weighted impact
- `S_emotion^(t-1)` = previous short-term state

**Decay behavior:**

If an emotion is mentioned, it gets boosted. If **not** mentioned (impact = 0):

```
S_emotion^(t) = 0.30 × 0 + 0.70 × S_emotion^(t-1) = 0.70 × S_emotion^(t-1)
```

So the value decays by **30% per message** if not mentioned.

**After 5 messages:**

```
S^(t+5) = (0.70)^5 × S^(t) = 0.168 × S^(t)
```

Emotion reduces to **17%** of original — natural fade.

#### 🎁 Concrete Benefits

1. **Natural decay**: Recent emotions fade if not reinforced
2. **No unbounded growth**: Values stay in reasonable range
3. **No manual reset**: System self-regulates
4. **Smooth transitions**: If user's emotion shifts (sad → happy), old emotion fades while new one rises
5. **Simpler code**: No normalization logic needed

---

### Parameter 12: Mid-Term Rolling Window — 27 emotions (`user_profile.py`)

#### 🎯 Mid-Term Emotional State

| Parameter | Current Method | Proposed α |
|---|---|---|
| `mid_term_state` (27 emotions) | Full recompute from last 15 messages | **0.125** per emotion |

#### 📝 Current Code

```python
# From user_profile.py (mid-term update logic - simplified conceptual)
# Every update: recompute from last 15 messages
recent_messages = self.message_history[-15:]
mid_term_state = {emotion: 0.0 for emotion in ALL_EMOTIONS}

for msg in recent_messages:
    for emotion, score in msg['emotions_detected'].items():
        mid_term_state[emotion] += score * impact
```

**Time complexity:** **O(window_size)** = O(15) per update.

#### ❌ What's Wrong

1. **O(N) recomputation** every update (see Problem 7)
2. **Cliff edge**: Message 16 drops to zero weight instantly (see Problem 8)
3. **Equal weighting**: All 15 messages weighted the same (message 1 = message 15)

#### ✅ EMA Replacement

Use **EMA with α ≈ 2/(window_size + 1)**:

For `window_size = 15`:

```
α_mt = 2 / (15 + 1) = 0.125
```

**Formula:**

```
M_emotion^(t) = α_mt × (score_emotion × impact) + (1 - α_mt) × M_emotion^(t-1)
```

**Where:**
- `α_mt = 0.125` (approximates 15-message rolling average)
- `score_emotion × impact` = current contribution
- `M_emotion^(t-1)` = previous mid-term state

#### 📊 Comparison

| Aspect | Current (Rolling Window) | EMA |
|---|---|---|
| **Time complexity** | O(15) per update | **O(1)** per update |
| **Message at boundary** | Full weight at msg 15, zero at msg 16 | Smooth exponential decay |
| **Recency weighting** | All 15 msgs equal | Recent msgs weighted more |
| **Memory required** | Store 15 messages | Store 1 value (current state) |

#### 🎁 Concrete Benefits

1. **O(1) per update** instead of O(15) — **15× faster**
2. **No cliff edge**: Smooth exponential decay as messages age
3. **Weighted toward recent**: EMA naturally gives more weight to newer messages within the "window"
4. **Memory efficient**: Don't need to store message ring buffer
5. **Mathematically equivalent**: EMA with α=0.125 approximates a 15-message moving average

---

### Parameter 13: Long-Term Frequency State — 27 emotions (`user_profile.py`)

#### 🎯 Long-Term Emotional Baseline

| Parameter | Current Method | Proposed α |
|---|---|---|
| `long_term_state` (27 emotions) | Full history recompute, top-3 only | **0.02** per emotion |

#### 📝 Current Code

```python
# From user_profile.py (long-term update logic - conceptual)
# Every update: scan ENTIRE history
emotion_frequency = Counter()

for msg in self.message_history:  # ❌ ALL messages!
    for emotion in msg['emotions_detected']:
        emotion_frequency[emotion] += 1

# Take top 3 only
top_3 = emotion_frequency.most_common(3)

# Reset state and rebuild
long_term_state = {e: 0.0 for e in ALL_EMOTIONS}
for emotion, count in top_3:
    long_term_state[emotion] = count / total_messages
```

**Time complexity:** **O(N × M)** where N = total messages, M = avg emotions per message.

#### ❌ What's Wrong

1. **O(N) full history scan** every update (see Problem 7) — at 1,000 messages, scans 1,000 messages
2. **Only top 3**: Ignores 24 other emotions completely
3. **Jarring resets**: If emotion drops from #3 to #4, it goes from non-zero to **zero instantly**
4. **Frequency-only**: Doesn't account for **intensity** (strong emotion = weak emotion if both appear once)

#### ✅ EMA Replacement

Use **very slow EMA** (α = 0.02) for deep baseline:

```
L_emotion^(t) = α_lt × (score_emotion × impact) + (1 - α_lt) × L_emotion^(t-1)
```

**Where:**
- `α_lt = 0.02` (very slow — long-term baseline)
- Effective memory window ≈ 1/0.02 = **50 messages**
- All 27 emotions contribute

#### 📊 Comparison

| Aspect | Current (Full Recompute) | EMA |
|---|---|---|
| **Time complexity** | **O(N)** where N = all messages | **O(1)** |
| **At 1,000 messages** | Scans 1,000 messages | Updates 1 value |
| **Emotions tracked** | Top 3 only | All 27 |
| **Transition behavior** | Cliff edge (#3→#4 drops to zero) | Smooth decay |
| **Intensity-aware** | No (counts frequency) | Yes (uses score × impact) |
| **Baseline stability** | Recalculated each time (can jump) | Smooth exponential trend |

#### 🎁 Concrete Benefits

1. **O(1) instead of O(N)** — at 1,000 messages, **1000× faster**
2. **No recomputation**: Just update one value per emotion
3. **All emotions contribute**: No artificial top-3 cutoff
4. **Smooth transitions**: Emotions naturally rise/fall in baseline
5. **True stable baseline**: With α=0.02, takes ~50 messages to significantly shift — perfect for long-term personality
6. **Intensity-weighted**: Strong emotions build baseline faster than weak ones

---

### Parameter 14: Similarity Threshold for Incident Detection (`orchestrator.py`)

#### 🎯 Similarity Threshold

| Parameter | Current Method | Proposed α |
|---|---|---|
| `similarity_threshold` | Static `0.2` | **0.10** |

#### 📝 Current Code

```python
# From orchestrator.py lines 412-417
repetition_info = self.incident_detector.find_repeated_incidents(
    current_message=message,
    message_history=profile.message_history,
    similarity_threshold=0.2  # ❌ HARDCODED
)
```

The threshold determines when two messages are considered "about the same incident."

**Jaccard similarity:**

```
similarity = |intersection| / |union|
```

If `similarity >= 0.2`, incidents are considered repeated.

#### ❌ What's Wrong

The **`0.2` threshold is the same for all users** (see Problem 6).

**Impact:**
- **User I** (diverse topics): Talks about work, family, hobbies, health → rarely hits 0.2 → under-detects repetition
- **User J** (focused topics): Only talks about one traumatic event → almost all messages hit 0.2 → over-detects repetition

#### ✅ EMA Replacement

Learn the **average similarity** of recent messages:

```
θ^(t) = α_θ × S̄_recent + (1 - α_θ) × θ^(t-1)
```

**Where:**
- `α_θ = 0.10` (moderate learning)
- `S̄_recent` = average similarity between current message and last N messages
- `θ^(t-1)` = previous threshold (starts at 0.2)

**Adaptive threshold:**

Set `threshold = max(0.1, min(0.4, θ^(t)))` (bounded to prevent extremes).

#### 🎁 Concrete Benefits

1. **Calibrates to user's topic diversity**:
   - **Diverse users** → lower average similarity → lower threshold → easier to detect repetition
   - **Focused users** → higher average similarity → higher threshold → harder to spuriously detect
2. **Self-adjusting**: If a user changes their communication pattern (e.g., starts focusing on one issue), threshold adapts
3. **Fair comparison**: Each user is compared to **their own baseline topic diversity**, not a global standard

---

## 5. Adaptive α — Making EMA Itself Evolve Over Time

The EMA formulas above use **fixed α values**. But we can make the system even smarter: **adjust α based on profile maturity**.

### 🎯 The Concept

**New profiles** should learn **fast** (high α) because we have little data.  
**Mature profiles** should learn **slow** (low α) to maintain a stable baseline.

### 🧮 Formula

```
α_effective = α_base / (1 + message_count / K)
```

**Where:**
- `α_base` = the base learning rate (e.g., 0.15)
- `message_count` = total messages in user's profile
- `K` = half-life constant (recommended **K = 200**)

### 📊 Behavior Table

| Profile Age | α_effective (for α_base = 0.15) | Meaning |
|---|---|---|
| **Message 1** | 0.149 | Nearly full learning rate |
| **Message 50** | 0.120 | Still adapting quickly |
| **Message 200** | 0.075 | Half the original rate (K=200 kicks in) |
| **Message 500** | 0.043 | Mostly stable, fine-tuning |
| **Message 1000** | 0.025 | Near-frozen, deep baseline |

### 📉 Decay Curve

```
α_effective decays from α_base → α_base/2 at K messages → α_base/N as N → ∞
```

### 🎁 Benefits

1. **Replaces `weights_learning_enabled` boolean**: No more hard "enable after 10 messages" cutoff
2. **Replaces fixed 10-message cycle**: Learning happens **every message**, but slows naturally
3. **Smooth learning curve**: Fast early adaptation → gradual stabilization
4. **Prevents over-fitting**: Mature profiles don't wildly swing on single messages
5. **Preserves responsiveness**: Even mature profiles still adapt (just slower)

### 🛠️ Implementation

```python
def get_effective_alpha(base_alpha: float, message_count: int, K: int = 200) -> float:
    """Calculate adaptive learning rate based on profile maturity"""
    return base_alpha / (1 + message_count / K)

# Example usage in weight update
effective_alpha = get_effective_alpha(alpha_base=0.12, message_count=self.message_count)
w_emotion^(t) = effective_alpha × w_observed + (1 - effective_alpha) × w_emotion^(t-1)
```

---

## 6. Full Inventory Table

Here's the **complete summary** of all 14 parameter groups with their EMA conversion:

| # | Parameter | File | Current Method | EMA α | Key Benefit |
|---|---|---|---|---|---|
| **1** | `w_emotion_intensity` | user_profile.py | If/else ±0.05 | **0.12** | Smooth, proportional learning |
| **2** | `w_recency_weight` | user_profile.py | If/else ±0.05 | **0.15** | No dead zones |
| **3** | `w_recurrence_boost` | user_profile.py | If/else ±0.05 | **0.25** | Fast pattern response |
| **4** | `w_temporal_confidence` | user_profile.py | If/else ±0.03 | **0.20** | Continuous sensitivity |
| **5** | `typing_speed_mean` | orchestrator.py | ✅ Already EMA | **0.05** | Keep as-is |
| **6** | `typing_speed_std` | orchestrator.py | ❌ Never updated | **0.05** | Real z-scores, personalized behavior multiplier |
| **7** | `entropy_penalty_coeff` | orchestrator.py | Static `0.3` | **0.10** | Per-user emotion style (mixed vs pure) |
| **8** | `recurrence_step` | orchestrator.py | Static `0.3` | **0.15** | Escalation vs desensitization learning |
| **9** | `impact_map` multipliers (×15) | orchestrator.py | Static lookup table | **0.08** | Learns temporal-emotional spillover patterns |
| **10** | `behavior_alpha` | orchestrator.py | Static `0.2` | **0.10** | Typing speed relevance per user |
| **11** | `short_term_state` (×27) | user_profile.py | Additive accumulation | **0.30** | Natural decay between messages |
| **12** | `mid_term_state` (×27) | user_profile.py | Full window recompute O(15) | **0.125** | O(1), no cliff edge, recency-weighted |
| **13** | `long_term_state` (×27) | user_profile.py | Full history recompute O(N) | **0.02** | O(1), stable baseline, all emotions |
| **14** | `similarity_threshold` | orchestrator.py | Static `0.2` | **0.10** | Adaptive to user's topic diversity |

**Total:** 14 parameter groups = **1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 15 + 1 + 27 + 27 + 27 + 1 = 105 individual parameters** being learned per user 🎯

---

## 7. Suggested Implementation Order

Implementing all 14 parameter groups at once is risky. Here's a **phased rollout** strategy:

### 🚀 Phase 1 — Highest Impact (Adaptive Weights #1–4)

**Goal:** Fix the core personalization system.

**What to do:**
- Replace `_calculate_adaptive_weights()` in `user_profile.py`
- Implement EMA-based weight updates with observed signals
- Remove `INITIAL_WEIGHTS.copy()` restart
- Remove hard thresholds and clamps
- Add adaptive α decay

**Expected impact:**
- **Immediate UX improvement**: Weights actually personalize over time
- **Fixes Problems 1, 2, 4, 5**: Momentum, proportional learning, no dead zones, no tight clamps
- **Moderate code change**: ~50 lines in `_calculate_adaptive_weights()`

**Test:** Run with synthetic user (100 very emotional messages) and verify weights smoothly increase toward emotion dominance.

---

### 🚀 Phase 2 — Emotional States (#11–13)

**Goal:** Fix performance and quality of state tracking.

**What to do:**
- Convert `short_term_state` update from `+=` to EMA (α=0.30)
- Convert `mid_term_state` from rolling window to EMA (α=0.125)
- Convert `long_term_state` from full recompute to EMA (α=0.02)

**Expected impact:**
- **Massive performance gain**: O(N) → O(1) for mid/long-term updates
- **Better quality**: Natural decay, smooth transitions, all emotions tracked
- **Fixes Problems 3, 7, 8**: Time decay, no recomputation, no cliff edges
- **Moderate code change**: ~100 lines across state update logic

**Test:** Profile with 1,000 messages — measure update time before/after (should be ~100× faster).

---

### 🚀 Phase 3 — Per-User Constants (#6–10, #14)

**Goal:** Personalize the hardcoded parameters.

**What to do:**
- Add EMA tracking for:
  - `typing_speed_std` (α=0.05)
  - `entropy_penalty_coeff` (α=0.10)
  - `recurrence_step` (α=0.15)
  - `behavior_alpha` (α=0.10)
  - `impact_map` multipliers (α=0.08)
  - `similarity_threshold` (α=0.10)

**Expected impact:**
- **Deep personalization**: System adapts to user-specific patterns
- **Fixes Problem 6**: No more one-size-fits-all constants
- **Larger code change**: ~200 lines across `orchestrator.py` and `user_profile.py`

**Test:** Two synthetic users with opposite patterns (e.g., one escalates, one desensitizes) — verify parameters diverge.

---

### 🚀 Phase 4 — Meta-Learning (Adaptive α)

**Goal:** Make the entire system stabilize naturally with profile maturity.

**What to do:**
- Implement `get_effective_alpha()` function
- Apply to all EMA updates
- Remove `weights_learning_enabled` flag
- Remove 10-message checkpoint logic

**Expected impact:**
- **Elegant lifecycle**: Fast early learning → slow mature refinement
- **Simpler code**: Remove boolean flags and checkpoint counters
- **Small code change**: ~30 lines to add α decay wrapper

**Test:** Track α over 1,000 messages — verify it decays from base to base/N.

---

### ✅ Rollback Strategy

Each phase is **independent** — if Phase N fails, rollback and keep Phases 1..N-1.

### 📊 Success Metrics

| Metric | Before EMA | After EMA (Target) |
|---|---|---|
| **Weight personalization** | Stuck at ±0.05 jumps | Smooth curve, 0.20–0.60 range |
| **State update time** (1K msgs) | ~10ms (O(N)) | ~0.01ms (O(1)) |
| **Memory usage** | 15-msg buffer + all history | Just current state |
| **Parameters learned per user** | 4 (weights only) | 105 (all groups) |
| **Learning stability** | Oscillates | Converges smoothly |

---

## 🎓 Conclusion

The **EMA approach** transforms this emotional state analysis system from a **rigid, rule-based architecture** into a **truly adaptive, personalized learning system**. By replacing:
- **Hard thresholds** → Continuous gradients
- **Fixed steps** → Proportional learning
- **Memoryless resets** → Smooth momentum
- **Global constants** → Per-user baselines
- **O(N) recomputation** → O(1) incremental updates

...we gain a system that:
- ✅ **Learns smoothly** from every message
- ✅ **Personalizes deeply** to each user
- ✅ **Scales efficiently** to long histories
- ✅ **Stabilizes naturally** over time

**All with simple, elegant mathematics.** 🚀

---

**Questions?** See the implementation details in each parameter section above, or refer to the codebase in `user_profile.py` and `orchestrator.py`.
