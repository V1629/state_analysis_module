# API Reference

> **Emotional State Analysis Module** — Complete API Documentation

---

## Table of Contents

1. [Orchestrator](#orchestrator)
2. [Emotional Detector](#emotional-detector)
3. [Temporal Extractor](#temporal-extractor)
4. [User Profile](#user-profile)
5. [Chat Logger](#chat-logger)
6. [Data Classes](#data-classes)
7. [Constants](#constants)

---

## Orchestrator

**Module**: `orchestrator.py`

The central coordination layer for emotional state analysis.

### Class: `ImpactCalculator`

Calculates how much an incident impacts user's emotional state.

#### `calculate_recency_weight(days_ago, max_days=730)`

Calculate exponential decay weight for past events.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `days_ago` | `int` | — | Number of days in the past |
| `max_days` | `int` | `730` | Reference point for decay (2 years) |

**Returns:** `float` — Weight factor in range [0, 1]

**Formula:**
```python
weight = e^(λ × days_ago)
# where λ = ln(0.05) / max_days ≈ -0.0041
```

**Example:**
```python
from orchestrator import ImpactCalculator

# Recent event (yesterday) - high weight
weight = ImpactCalculator.calculate_recency_weight(1)
print(weight)  # ~0.996

# Old event (1 year ago) - low weight
weight = ImpactCalculator.calculate_recency_weight(365)
print(weight)  # ~0.223
```

---

#### `calculate_emotion_intensity(emotions_dict, entropy_penalty_coefficient=0.3)`

Calculate normalized intensity from emotion probabilities.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `emotions_dict` | `Dict[str, float]` | — | Emotion name to probability mapping |
| `entropy_penalty_coefficient` | `float` | `0.3` | Per-user entropy penalty |

**Returns:** `float` — Intensity score in range [0, 1]

**Formula:**
```python
intensity = max_probability × (1 - entropy_penalty)
# where entropy_penalty = max(0, normalized_entropy - coefficient)
```

**Example:**
```python
emotions = {"sadness": 0.72, "grief": 0.15, "love": 0.08}
intensity = ImpactCalculator.calculate_emotion_intensity(emotions)
print(intensity)  # ~0.65
```

---

#### `calculate_recurrence_boost(incident_count, recurrence_step=0.3)`

Increase emotional weight for repeated incidents.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `incident_count` | `int` | — | Number of times emotion detected |
| `recurrence_step` | `float` | `0.3` | Step size for boost calculation |

**Returns:** `float` — Boost multiplier in range [1.0, 2.5]

**Formula:**
```python
boost = 1 + (incident_count - 1) × recurrence_step
# capped at 2.5
```

**Example:**
```python
# First mention - no boost
boost = ImpactCalculator.calculate_recurrence_boost(1)
print(boost)  # 1.0

# Third mention - significant boost
boost = ImpactCalculator.calculate_recurrence_boost(3)
print(boost)  # 1.6
```

---

#### `get_state_impact_multipliers(age_category, user_multipliers=None)`

Determine which emotional states are affected by incident.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `age_category` | `str` | — | 'recent', 'medium', 'distant', 'future', 'unknown' |
| `user_multipliers` | `Dict` | `None` | Optional per-user multiplier overrides |

**Returns:** `Dict[str, float]` — Multipliers for each state

**Default Multipliers:**

| Category | Short-Term | Mid-Term | Long-Term |
|----------|------------|----------|-----------|
| recent | 1.0 | 0.6 | 0.2 |
| medium | 0.3 | 0.9 | 0.5 |
| distant | 0.05 | 0.3 | 0.8 |
| future | 0.7 | 0.4 | 0.0 |
| unknown | 0.5 | 0.5 | 0.3 |

---

## Emotional Detector

**Module**: `emotional_detector.py`

Emotion classification using HuggingFace multilingual model.

### `classify_emotions(text)`

Classify emotions in multilingual text.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | Input text (English, Hindi, or Hinglish) |

**Returns:** `Dict[str, float]` — Emotion name to probability mapping, sorted by probability

**Supported Emotions (27):**
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

**Example:**
```python
from emotional_detector import classify_emotions

emotions = classify_emotions("I'm really happy today!")
# Returns: {"joy": 0.82, "optimism": 0.12, "excitement": 0.04, ...}

emotions = classify_emotions("Bahut sad feel ho raha hai")
# Returns: {"sadness": 0.75, "grief": 0.10, "disappointment": 0.08, ...}
```

---

## Temporal Extractor

**Module**: `temporal_extractor.py`

Temporal reference extraction from multilingual text.

### Class: `TemporalExtractor`

Main extraction orchestrator.

#### `extract_all(text)`

Extract all temporal references from text.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | Input text to analyze |

**Returns:** `List[ParsedTemporal]` — List of parsed temporal references

**Example:**
```python
from temporal_extractor import TemporalExtractor

extractor = TemporalExtractor()
results = extractor.extract_all("3 years ago I lost my grandmother")

for ref in results:
    print(f"Phrase: {ref.phrase}")
    print(f"Days ago: {ref.days_ago}")
    print(f"Category: {ref.age_category}")
    print(f"Confidence: {ref.confidence}")
```

---

#### `categorize_time_gap(days_ago)`

Categorize a time gap into predefined categories.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `days_ago` | `int` | Number of days |

**Returns:** `str` — Category ('recent', 'medium', 'distant', 'future', 'unknown')

**Thresholds:**
| Days | Category |
|------|----------|
| 0-30 | recent |
| 31-365 | medium |
| 365+ | distant |
| negative | future |

---

### Class: `TenseAnalyzer`

Analyze verb tenses for ambiguity resolution.

#### `analyze_tense(full_message, language='mixed')`

Analyze message tense and return scoring.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `full_message` | `str` | — | Full text message |
| `language` | `str` | `'mixed'` | Language hint |

**Returns:** `Dict[str, Any]` — Tense scores and dominant tense

**Example:**
```python
from temporal_extractor import TenseAnalyzer

result = TenseAnalyzer.analyze_tense("I was feeling sad yesterday")
# Returns: {"past_score": 0.8, "future_score": 0.0, "present_score": 0.2, "dominant_tense": "past"}
```

---

## User Profile

**Module**: `user_profile.py`

User emotional profile management.

### Class: `UserProfile`

Manages user's emotional profile across three temporal dimensions.

#### `__init__(user_id)`

Initialize a new user profile.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `user_id` | `str` | Unique user identifier |

**Raises:** `ValueError` if `user_id` is empty or not a string

---

#### `update_short_term(emotions, impact_score)`

Update short-term emotional state using EMA.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `emotions` | `Dict[str, float]` | Detected emotions |
| `impact_score` | `float` | Calculated impact |

**Learning Rate:** α = 0.15 (fast adaptation)

---

#### `update_mid_term(emotions, impact_score)`

Update mid-term emotional state using rolling window.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `emotions` | `Dict[str, float]` | Detected emotions |
| `impact_score` | `float` | Calculated impact |

**Window Size:** 15 messages

**Activation:** After 14 days OR 30 messages

---

#### `update_long_term(emotions, impact_score)`

Update long-term emotional baseline using EMA.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `emotions` | `Dict[str, float]` | Detected emotions |
| `impact_score` | `float` | Calculated impact |

**Learning Rate:** α = 0.02 (slow, stable)

**Activation:** After 90 days OR 50 messages

---

#### `add_message_to_history(message, emotions, temporal_info, impact_score)`

Add a message to the user's history.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `message` | `str` | The user's message |
| `emotions` | `Dict[str, float]` | Detected emotions |
| `temporal_info` | `Dict` | Temporal extraction results |
| `impact_score` | `float` | Calculated impact |

---

#### `save_profile()`

Save profile to JSON file.

**Returns:** `bool` — Success status

---

#### `load_profile(user_id)` (static)

Load a profile from JSON file.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `user_id` | `str` | User identifier |

**Returns:** `UserProfile` — Loaded profile or new profile if not found

---

#### `get_state_activation_info()`

Get activation status for all states.

**Returns:** `Dict[str, Dict]` — Activation info for each state

---

### Function: `get_effective_alpha(base_learning_rate, message_count, decay_constant=200)`

Calculate adaptive learning rate based on profile maturity.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `base_learning_rate` | `float` | — | Starting learning rate |
| `message_count` | `int` | — | Messages processed |
| `decay_constant` | `int` | `200` | Decay speed control |

**Returns:** `float` — Effective learning rate

**Formula:**
```python
effective_α = base_α / (1 + message_count / decay_constant)
```

---

## Chat Logger

**Module**: `chat_logger.py`

Excel export for chat history and emotional states.

### Class: `ChatLogger`

#### `__init__(file_path="chat_logs.xlsx")`

Initialize logger with target file.

---

#### `log_chat(message, impact_score, current_state, profile_state, activation_status, profile_age_days, message_count)`

Log a chat message with emotional states.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `message` | `str` | User's message |
| `impact_score` | `float` | Calculated impact |
| `current_state` | `dict` | Current message emotions |
| `profile_state` | `dict` | Profile emotional states |
| `activation_status` | `dict` | State activation status |
| `profile_age_days` | `int` | Days since profile creation |
| `message_count` | `int` | Total messages processed |

---

## Data Classes

### `ParsedTemporal`

Represents a parsed temporal reference.

**Fields:**
| Name | Type | Description |
|------|------|-------------|
| `phrase` | `str` | Original phrase |
| `parsed_date` | `Optional[datetime]` | Parsed date if available |
| `time_gap_days` | `Optional[int]` | Days from now |
| `age_category` | `str` | Category (recent/medium/distant/future) |
| `confidence` | `float` | Parsing confidence |
| `parse_method` | `str` | Method used for parsing |
| `days_ago` | `int` | Days ago (convenience field) |

**Methods:**
- `to_dict()` — Convert to dictionary for serialization

---

### `TimePhrase`

Represents a detected temporal phrase.

**Fields:**
| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | The phrase text |
| `start_pos` | `int` | Start position in text |
| `end_pos` | `int` | End position in text |
| `pattern_type` | `str` | Type of pattern matched |
| `language` | `str` | Detected language |
| `context_window` | `str` | Surrounding context |

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
    'emotion_intensity': 0.45,      # Highest
    'recency_weight': 0.30,         # High
    'recurrence_boost': 0.15,       # Medium
    'temporal_confidence': 0.10     # Lowest
}
```

### `STATE_ACTIVATION_CONFIG`

State activation thresholds:

```python
STATE_ACTIVATION_CONFIG = {
    'short_term': {'min_days': 0, 'min_messages': 1},
    'mid_term': {'min_days': 14, 'min_messages': 30, 'window_size': 15},
    'long_term': {'min_days': 90, 'min_messages': 50}
}
```
