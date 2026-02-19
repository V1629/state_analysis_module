# Orchestrator Module

> **Module**: `orchestrator.py`  
> **Purpose**: Central coordination layer for emotional state analysis

---

## Overview

The Orchestrator is the **brain** of the Emotional State Analysis Module. It connects emotion detection, temporal extraction, and profile updates into a cohesive pipeline.

### Responsibilities

- Coordinate emotion detection and temporal extraction
- Calculate compound impact scores using weighted sum approach
- Manage adaptive weight learning
- Update user profiles across all temporal states
- Handle behavioral analysis (typing speed)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │ ImpactCalculator │    │ BehaviorAnalysis │            │
│  ├─────────────────┤    ├─────────────────┤            │
│  │ • recency_weight│    │ • typing_speed   │            │
│  │ • intensity     │    │ • z-score        │            │
│  │ • recurrence    │    │ • multiplier     │            │
│  │ • state_impact  │    │                  │            │
│  └─────────────────┘    └─────────────────┘            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Impact Calculation                  │   │
│  │  impact = Σ(weight_i × factor_i) × behavior_mult│   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Class: `ImpactCalculator`

The core calculation engine for emotional impact assessment.

### Class Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `typing_speed_mean` | `float` | `1.0` | Baseline typing speed |
| `typing_speed_std` | `float` | `0.5` | Typing speed standard deviation |

### Methods

#### `calculate_recency_weight(days_ago, max_days=730) → float`

Calculates exponential decay weight for past events.

**Implementation:**
```python
@staticmethod
def calculate_recency_weight(days_ago: int, max_days: int = 730) -> float:
    if days_ago < 0:  # Future events
        return 0.7  # Anticipatory emotions
    
    lambda_factor = math.log(0.05) / max_days  # ≈ -0.0041
    weight = math.exp(lambda_factor * days_ago)
    
    return max(0.0, min(1.0, weight))
```

**Decay Curve:**

| Days Ago | Weight | Interpretation |
|----------|--------|----------------|
| 0 | 1.0 | Maximum impact |
| 30 | ~0.89 | Recent, high impact |
| 180 | ~0.56 | Medium, moderate impact |
| 365 | ~0.22 | Old, reduced impact |
| 730 | ~0.05 | Very old, minimal impact |

---

#### `calculate_emotion_intensity(emotions_dict, entropy_penalty_coefficient=0.3) → float`

Calculates normalized intensity with entropy penalty for uncertain emotions.

**Key Concepts:**

1. **Maximum Probability**: The highest emotion probability indicates strength
2. **Shannon Entropy**: Measures emotion distribution uncertainty
3. **Entropy Penalty**: Reduces intensity for mixed/uncertain emotions

**Formula:**
```
intensity = max_prob × (1 - entropy_penalty)
where entropy_penalty = max(0, normalized_entropy - coefficient)
```

**Why Entropy Matters:**
- Low entropy (e.g., sadness=0.9) → confident emotion → no penalty
- High entropy (e.g., sadness=0.3, joy=0.3, neutral=0.3) → uncertain → penalty applied

---

#### `calculate_recurrence_boost(incident_count, recurrence_step=0.3) → float`

Amplifies impact for repeated emotional incidents.

**Formula:**
```
boost = 1 + (incident_count - 1) × recurrence_step
```

**Example Progression:**
| Occurrence | Boost | Impact |
|------------|-------|--------|
| 1st | 1.0× | Base impact |
| 2nd | 1.3× | 30% increase |
| 3rd | 1.6× | 60% increase |
| 4th | 1.9× | 90% increase |
| 5th+ | 2.5× | Capped maximum |

---

#### `get_state_impact_multipliers(age_category, user_multipliers=None) → Dict`

Determines how temporal categories affect each emotional state.

**Default Multiplier Table:**

| Category | Short-Term | Mid-Term | Long-Term |
|----------|------------|----------|-----------|
| `recent` | 1.0 | 0.6 | 0.2 |
| `medium` | 0.3 | 0.9 | 0.5 |
| `distant` | 0.05 | 0.3 | 0.8 |
| `future` | 0.7 | 0.4 | 0.0 |
| `unknown` | 0.5 | 0.5 | 0.3 |

**Interpretation:**
- **Recent events** primarily affect short-term state
- **Medium events** primarily affect mid-term state
- **Distant events** primarily affect long-term baseline
- **Future events** create anticipatory short-term impact

---

## Impact Calculation Pipeline

### Step 1: Extract Signals

```python
# From user message
emotions = classify_emotions(message)        # {emotion: probability}
temporal = extractor.extract_all(message)    # [ParsedTemporal, ...]
```

### Step 2: Calculate Factors

```python
# Core factors
emotion_intensity = calculate_emotion_intensity(emotions)
recency_weight = calculate_recency_weight(days_ago)
temporal_confidence = temporal_result.confidence
recurrence_boost = calculate_recurrence_boost(incident_count)
```

### Step 3: Compute Weighted Sum

```python
# Using adaptive weights
base_impact = (
    adaptive_weights['emotion_intensity'] * emotion_intensity +
    adaptive_weights['recency_weight'] * recency_weight +
    adaptive_weights['temporal_confidence'] * temporal_confidence +
    adaptive_weights['recurrence_boost'] * normalized_recurrence
)
```

### Step 4: Apply Behavior Multiplier

```python
# Z-score based multiplier
z_score = (typing_speed - mean) / std
behavior_multiplier = 1.0 + (alpha * tanh(z_score))

final_impact = base_impact * behavior_multiplier
```

---

## Behavioral Analysis

### Typing Speed Analysis

The orchestrator tracks typing speed deviations as behavioral signals:

- **Faster than usual** → May indicate excitement, urgency
- **Slower than usual** → May indicate hesitation, deep thought
- **Normal speed** → Baseline behavior

**EMA Update for Mean:**
```python
typing_speed_mean = β × speed + (1 - β) × typing_speed_mean
# where β = 0.05 (slow learning)
```

**Behavior Multiplier Range:** [0.8, 1.2]

---

## Configuration Parameters

### Hardcoded (Current)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `entropy_penalty_coefficient` | 0.3 | Entropy penalty threshold |
| `recurrence_step` | 0.3 | Boost per recurrence |
| `max_recurrence_boost` | 2.5 | Maximum boost cap |
| `behavior_alpha` | 0.2 | Behavior multiplier strength |

### Per-User (Adaptive)

These can be stored in `UserProfile` and evolved via EMA:
- `entropy_penalty_coeff`
- `recurrence_step`
- `behavior_alpha`
- `similarity_threshold`
- `impact_multipliers`

---

## Usage Example

```python
from orchestrator import ImpactCalculator
from emotional_detector import classify_emotions
from temporal_extractor import TemporalExtractor
from user_profile import UserProfile

# Initialize
profile = UserProfile("user123")
extractor = TemporalExtractor()

# Process message
message = "3 saal pehle dadi chali gayi, aaj bhi yaad aati hai"

# Step 1: Detect emotions
emotions = classify_emotions(message)
# {"sadness": 0.72, "grief": 0.15, "love": 0.08, ...}

# Step 2: Extract temporal
temporal_refs = extractor.extract_all(message)
days_ago = temporal_refs[0].days_ago  # 1095

# Step 3: Calculate factors
intensity = ImpactCalculator.calculate_emotion_intensity(emotions)
recency = ImpactCalculator.calculate_recency_weight(days_ago)
boost = ImpactCalculator.calculate_recurrence_boost(1)

# Step 4: Compute impact
weights = profile.adaptive_weights
impact = (
    weights['emotion_intensity'] * intensity +
    weights['recency_weight'] * recency +
    weights['recurrence_boost'] * boost * 0.5 +  # normalized
    weights['temporal_confidence'] * temporal_refs[0].confidence
)

print(f"Impact Score: {impact:.4f}")
```

---

## Related Documentation

- [API Reference](../api-reference.md) — Complete function signatures
- [User Profile Module](./user-profile.md) — Profile management
- [EMA Approach](../ema-approach.md) — Adaptive learning details
