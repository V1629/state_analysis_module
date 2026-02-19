# User Profile Module

> **Module**: `user_profile.py`  
> **Purpose**: User emotional profile management with adaptive weight learning

---

## Overview

The User Profile module manages per-user emotional profiles across three temporal dimensions. It implements EMA-based state updates and adaptive weight learning.

### Responsibilities

- Track emotional states across short, mid, and long-term horizons
- Implement EMA (Exponential Moving Average) for state updates
- Manage adaptive weights for impact calculation
- Persist profiles to JSON for session continuity
- Track message history for pattern analysis

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER PROFILE                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              TEMPORAL STATES                      │   │
│  ├──────────┬──────────────┬────────────────────────┤   │
│  │ ST (⚡)   │ MT (📈)      │ LT (🏛️)               │   │
│  │ α=0.15   │ window=15    │ α=0.02                │   │
│  │ 0-30d    │ 31-365d      │ 365d+                 │   │
│  └──────────┴──────────────┴────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           ADAPTIVE WEIGHTS                        │   │
│  │  emotion_intensity: 0.45                         │   │
│  │  recency_weight: 0.30                            │   │
│  │  recurrence_boost: 0.15                          │   │
│  │  temporal_confidence: 0.10                       │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           MESSAGE HISTORY                         │   │
│  │  [msg1, msg2, msg3, ...]                         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Constants

### `ALL_EMOTIONS`

List of all 27 supported emotions:

```python
ALL_EMOTIONS = [
    'admiration', 'amusement', 'anger', 'annoyance', 'approval',
    'caring', 'confusion', 'curiosity', 'desire', 'disappointment',
    'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear',
    'gratitude', 'grief', 'joy', 'love', 'nervousness',
    'neutral', 'optimism', 'pride', 'realization', 'relief',
    'remorse', 'sadness', 'surprise'
]
```

### `INITIAL_WEIGHTS`

Default adaptive weight hierarchy:

```python
INITIAL_WEIGHTS = {
    'emotion_intensity': 0.45,      # Highest - emotion is primary
    'recency_weight': 0.30,         # High - recent events matter
    'recurrence_boost': 0.15,       # Medium - patterns matter
    'temporal_confidence': 0.10     # Lowest - exact timing less critical
}
```

### `STATE_ACTIVATION_CONFIG`

Configuration for state activation thresholds:

```python
STATE_ACTIVATION_CONFIG = {
    'short_term': {
        'name': '⚡ Short-term (0-30 days)',
        'min_days': 0,
        'min_messages': 1,
        'description': 'Recent emotions, always tracking'
    },
    'mid_term': {
        'name': '📈 Mid-term (31-365 days)',
        'min_days': 14,
        'min_messages': 30,
        'window_size': 15,
        'description': 'Patterns over 2 weeks'
    },
    'long_term': {
        'name': '🏛️ Long-term (365+ days)',
        'min_days': 90,
        'min_messages': 50,
        'description': 'Baseline personality over 3 months'
    }
}
```

---

## Class: `UserProfile`

Main profile management class.

### Constructor

```python
def __init__(self, user_id: str)
```

**Parameters:**
- `user_id` (str): Unique user identifier

**Raises:** `ValueError` if `user_id` is empty or not a string

**Initialized Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `user_id` | `str` | Unique identifier |
| `created_at` | `datetime` | Profile creation timestamp |
| `last_updated` | `datetime` | Last update timestamp |
| `short_term_state` | `Dict[str, float]` | Current mood (27 emotions) |
| `mid_term_state` | `Dict[str, float]` | Emotional trends (27 emotions) |
| `long_term_state` | `Dict[str, float]` | Personality baseline (27 emotions) |
| `message_history` | `List[Dict]` | All messages with metadata |
| `message_count` | `int` | Total messages processed |
| `adaptive_weights` | `Dict[str, float]` | Learned weights |

---

### State Update Methods

#### `update_short_term(emotions, impact_score)`

Update short-term state using EMA.

```python
# EMA formula
for emotion, new_value in emotions.items():
    old_value = self.short_term_state[emotion]
    self.short_term_state[emotion] = α * new_value + (1 - α) * old_value
```

**Learning Rate:** α = 0.15 (fast, reactive)

---

#### `update_mid_term(emotions, impact_score)`

Update mid-term state using rolling window.

**Process:**
1. Maintain a window of the last 15 messages
2. Calculate average emotion scores across window
3. Update mid-term state with windowed average

**Activation:** After 14 days OR 30 messages

---

#### `update_long_term(emotions, impact_score)`

Update long-term baseline using EMA.

```python
# EMA with slow learning rate
effective_α = get_effective_alpha(0.02, self.message_count)
for emotion, new_value in emotions.items():
    old_value = self.long_term_state[emotion]
    self.long_term_state[emotion] = effective_α * new_value + (1 - effective_α) * old_value
```

**Learning Rate:** α = 0.02 (slow, stable)

**Activation:** After 90 days OR 50 messages

---

### Activation Methods

#### `is_state_activated(state_type) → bool`

Check if a state should be updated based on thresholds.

```python
profile = UserProfile("user123")

# Process messages
for i in range(35):
    profile.message_count = i
    print(f"Mid-term active: {profile.is_state_activated('mid_term')}")
    # False until i >= 30 (or 14 days pass)
```

**Uses OR Logic:** Activates if EITHER time OR message threshold is met.

---

#### `get_state_activation_info() → Dict`

Get detailed activation status for all states.

```python
info = profile.get_state_activation_info()
# {
#     'short_term': {
#         'activated': True,
#         'activated_by': 'both',
#         'days_progress': 100,
#         'messages_progress': 100
#     },
#     'mid_term': {
#         'activated': False,
#         'activated_by': None,
#         'days_progress': 35.7,  # 5/14 days
#         'messages_progress': 66.7  # 20/30 messages
#     },
#     ...
# }
```

---

### Persistence Methods

#### `save_profile() → bool`

Save profile to JSON file.

```python
profile = UserProfile("user123")
# ... process messages ...
success = profile.save_profile()
# Saves to user_profiles/user123.json
```

---

#### `load_profile(user_id)` (static)

Load profile from JSON file or create new.

```python
profile = UserProfile.load_profile("user123")
# Loads from user_profiles/user123.json
# Returns new profile if file doesn't exist
```

---

### History Methods

#### `add_message_to_history(message, emotions, temporal_info, impact_score)`

Add a message to the user's history.

```python
profile.add_message_to_history(
    message="I'm feeling sad today",
    emotions={"sadness": 0.72, "disappointment": 0.15},
    temporal_info={"days_ago": 0, "category": "recent"},
    impact_score=0.65
)
```

**Stored Entry Structure:**
```python
{
    "timestamp": "2026-02-19T10:30:00",
    "message": "I'm feeling sad today",
    "emotions_detected": {"sadness": 0.72, ...},
    "temporal_info": {...},
    "impact_score": 0.65
}
```

---

## Function: `get_effective_alpha()`

Calculate adaptive learning rate based on profile maturity.

```python
def get_effective_alpha(
    base_learning_rate: float,
    message_count: int,
    decay_constant: int = 200
) -> float:
    return base_learning_rate / (1 + message_count / decay_constant)
```

**Purpose:** As more messages are processed, the learning rate decreases, stabilizing the profile over time.

**Example:**
| Messages | Base α | Effective α |
|----------|--------|-------------|
| 0 | 0.15 | 0.150 |
| 50 | 0.15 | 0.120 |
| 100 | 0.15 | 0.100 |
| 200 | 0.15 | 0.075 |
| 500 | 0.15 | 0.043 |

---

## Per-User EMA Parameters

The profile stores per-user parameters that can evolve via EMA:

```python
# Default values
self.entropy_penalty_coeff = 0.3
self.recurrence_step = 0.3
self.behavior_alpha = 0.2
self.similarity_threshold = 0.2
self.impact_multipliers = {
    "recent": {"short_term": 1.0, "mid_term": 0.6, "long_term": 0.2},
    "medium": {"short_term": 0.3, "mid_term": 0.9, "long_term": 0.5},
    "distant": {"short_term": 0.05, "mid_term": 0.3, "long_term": 0.8},
    "unknown": {"short_term": 0.5, "mid_term": 0.5, "long_term": 0.3},
    "future": {"short_term": 0.7, "mid_term": 0.4, "long_term": 0.0}
}
```

---

## Usage Example

```python
from user_profile import UserProfile, ALL_EMOTIONS, get_effective_alpha

# Create or load profile
profile = UserProfile.load_profile("user123")

# Process a message
emotions = {"sadness": 0.72, "grief": 0.15, "love": 0.08}
impact_score = 0.85

# Update states
profile.update_short_term(emotions, impact_score)

if profile.is_state_activated('mid_term'):
    profile.update_mid_term(emotions, impact_score)

if profile.is_state_activated('long_term'):
    profile.update_long_term(emotions, impact_score)

# Add to history
profile.add_message_to_history(
    message="Miss my grandmother",
    emotions=emotions,
    temporal_info={"days_ago": 1095, "category": "distant"},
    impact_score=impact_score
)

# Save profile
profile.save_profile()

# Check activation
activation = profile.get_state_activation_info()
print(f"MT Active: {activation['mid_term']['activated']}")
print(f"LT Active: {activation['long_term']['activated']}")
```

---

## File Storage

Profiles are stored in `user_profiles/` directory:

```
user_profiles/
├── user123.json
├── alice.json
└── bob.json
```

**JSON Structure:**
```json
{
    "user_id": "user123",
    "created_at": "2026-02-01T10:00:00",
    "last_updated": "2026-02-19T14:30:00",
    "short_term_state": {
        "sadness": 0.45,
        "joy": 0.12,
        ...
    },
    "mid_term_state": {...},
    "long_term_state": {...},
    "adaptive_weights": {...},
    "message_count": 150,
    "message_history": [...]
}
```

---

## Related Documentation

- [API Reference](../api-reference.md) — Complete function signatures
- [EMA Approach](../ema-approach.md) — Detailed EMA explanation
- [Data Flow](../data-flow.md) — Profile update pipeline
