# 07 — API Reference

> **Prerequisites:** [06-module-reference.md](./06-module-reference.md)  
> **Next:** [08-configuration.md](./08-configuration.md)

---

## Overview

This document provides complete API reference for all public functions and classes.

---

# orchestrator.py

## `process_message()`

Main entry point for processing user messages.

```python
def process_message(
    user_id: str,
    message: str,
    timestamp: datetime = None
) -> Dict[str, Any]
```

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | `str` | ✅ | Unique user identifier |
| `message` | `str` | ✅ | User message text |
| `timestamp` | `datetime` | ❌ | Message timestamp (default: `datetime.now()`) |

### Returns

```python
{
    'detected_emotions': Dict[str, float],  # All 27 emotions
    'temporal_refs': List[TimePhrase],      # Extracted time references
    'temporal_category': str,               # recent/medium/distant/future
    'state_updates': {
        'short_term': Dict[str, float],
        'mid_term': Dict[str, float],
        'long_term': Dict[str, float]
    },
    'dominant_emotion': str,
    'dominant_score': float
}
```

### Example

```python
from orchestrator import process_message

result = process_message(
    user_id="user123",
    message="I've been stressed about work for the past month"
)

print(result['dominant_emotion'])  # 'nervousness'
print(result['temporal_category']) # 'recent'
```

---

## Class: `ImpactCalculator`

Calculates emotional impact weights.

### Constructor

```python
ImpactCalculator(
    entropy_penalty: float = 0.3,
    recurrence_step: float = 0.3,
    behavior_alpha: float = 0.2
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entropy_penalty` | `float` | 0.3 | Penalty for ambiguous emotions |
| `recurrence_step` | `float` | 0.3 | Boost per recurrence |
| `behavior_alpha` | `float` | 0.2 | Behavioral learning rate |

---

### `calculate_recency_weight()`

```python
def calculate_recency_weight(self, days_ago: int) -> float
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `days_ago` | `int` | Days from current date (negative = future) |

**Returns:** `float` between 0.0 and 1.0

---

### `calculate_emotion_intensity()`

```python
def calculate_emotion_intensity(
    self, 
    emotions: Dict[str, float]
) -> Tuple[float, str]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `emotions` | `Dict[str, float]` | Emotion name → score mapping |

**Returns:** `Tuple[intensity: float, dominant_emotion: str]`

---

### `calculate_recurrence_boost()`

```python
def calculate_recurrence_boost(
    self,
    emotion: str,
    history: List[Dict[str, Any]]
) -> float
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `emotion` | `str` | Emotion to check |
| `history` | `List[Dict]` | Past emotion detections |

**Returns:** `float` multiplier (1.0 = no boost)

---

### `get_state_impact_multipliers()`

```python
def get_state_impact_multipliers(
    self,
    temporal_category: str
) -> Dict[str, float]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `temporal_category` | `str` | `'recent'`, `'medium'`, `'distant'`, `'future'` |

**Returns:** `Dict` with `'ST'`, `'MT'`, `'LT'` keys

---

# emotional_detector.py

## `classify_emotions()`

Classifies emotions in text using HuggingFace API.

```python
def classify_emotions(text: str) -> Dict[str, float]
```

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `text` | `str` | ✅ | Input text (EN/HI/Hinglish) |

### Returns

```python
{
    'admiration': 0.12,
    'amusement': 0.05,
    'anger': 0.02,
    # ... all 27 emotions
    'surprise': 0.08
}
```

### Example

```python
from emotional_detector import classify_emotions

emotions = classify_emotions("I'm so happy and excited!")
print(emotions['joy'])        # 0.85
print(emotions['excitement']) # 0.72
```

---

## Constants

### `ALL_EMOTIONS`

```python
ALL_EMOTIONS: List[str]  # 27 emotion names
```

### `API_URL`

```python
API_URL: str  # HuggingFace endpoint
```

### `HEADERS`

```python
HEADERS: Dict[str, str]  # Authorization headers
```

---

# temporal_extractor.py

## `extract()`

Extracts temporal information from text.

```python
def extract(text: str) -> ParsedTemporal
```

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `text` | `str` | ✅ | Input text (EN/HI/Hinglish) |

### Returns

```python
ParsedTemporal(
    phrases: List[TimePhrase],
    days_ago: int,
    category: str,  # 'recent', 'medium', 'distant', 'future'
    tense: str      # 'past', 'present', 'future'
)
```

### Example

```python
from temporal_extractor import extract

result = extract("3 years ago I moved to a new city")
print(result.days_ago)   # 1095
print(result.category)   # 'distant'
print(result.tense)      # 'past'
```

---

## Class: `TimePhrase`

Data class for extracted time phrases.

```python
@dataclass
class TimePhrase:
    original_text: str   # Original text as found
    normalized: str      # Normalized English form
    start_pos: int       # Start character position
    end_pos: int         # End character position
    confidence: float    # Detection confidence (0-1)
```

---

## Class: `ParsedTemporal`

Data class for complete temporal analysis.

```python
@dataclass
class ParsedTemporal:
    phrases: List[TimePhrase]
    days_ago: int
    category: str
    tense: str
```

---

## Class: `TenseAnalyzer`

Grammatical tense detection.

### `analyze()`

```python
def analyze(self, text: str) -> str
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | Input text |

**Returns:** `'past'`, `'present'`, or `'future'`

---

## `categorize_temporal()`

Maps days to temporal category.

```python
def categorize_temporal(days_ago: int) -> str
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `days_ago` | `int` | Days from current date |

**Returns:** `'recent'`, `'medium'`, `'distant'`, or `'future'`

| Input Range | Output |
|-------------|--------|
| `< 0` | `'future'` |
| `0-30` | `'recent'` |
| `31-365` | `'medium'` |
| `> 365` | `'distant'` |

---

# user_profile.py

## Class: `UserProfile`

User emotional profile manager.

### Constructor

```python
UserProfile(user_id: str)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | `str` | ✅ | Unique user identifier |

### Attributes

| Name | Type | Description |
|------|------|-------------|
| `user_id` | `str` | User identifier |
| `created_at` | `datetime` | Profile creation time |
| `message_count` | `int` | Total messages processed |
| `short_term_state` | `Dict[str, float]` | ST emotional state |
| `mid_term_state` | `Dict[str, float]` | MT emotional state |
| `long_term_state` | `Dict[str, float]` | LT emotional state |
| `mt_activated` | `bool` | Mid-term state active |
| `lt_activated` | `bool` | Long-term state active |

---

### `update_states()`

Updates emotional states with new data.

```python
def update_states(
    self,
    emotions: Dict[str, float],
    impact_multipliers: Dict[str, float]
) -> Dict[str, Dict[str, float]]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `emotions` | `Dict[str, float]` | Detected emotions |
| `impact_multipliers` | `Dict[str, float]` | ST/MT/LT multipliers |

**Returns:** Updated states for all three temporal horizons

---

### `check_activation()`

Checks and updates state activation flags.

```python
def check_activation(self) -> None
```

**Side effects:** Updates `mt_activated` and `lt_activated`

---

### `get_dominant_emotions()`

Gets top emotions for each state.

```python
def get_dominant_emotions(self, top_n: int = 5) -> Dict[str, List[Tuple[str, float]]]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_n` | `int` | 5 | Number of top emotions |

**Returns:**
```python
{
    'short_term': [('joy', 0.8), ('excitement', 0.6), ...],
    'mid_term': [...],
    'long_term': [...]
}
```

---

### `_adapt_weights_based_on_pattern()`

Adapts SS weights based on user's emotional patterns.

```python
def _adapt_weights_based_on_pattern(self, state_type: str) -> Dict[str, float]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `state_type` | `str` | `'short_term'`, `'mid_term'`, or `'long_term'` |

**Returns:** Adapted weights dict (normalized to sum=1.0)

```python
# Example return value
{
    "intensity": 0.24,
    "persistence": 0.16,
    "recency": 0.22,
    "impact": 0.15,
    "volatility": 0.23
}
```

**Adaptation Rules:**

| Pattern | Condition | Adjustment |
|---------|-----------|------------|
| High volatility | `volatility > 0.3` | ↑ volatility +0.05, ↓ persistence -0.05 |
| Low volatility | `volatility < 0.1` | ↑ persistence +0.03, ↓ volatility -0.03 |
| Not enough data | `history < 3` | Return base weights (no adaptation) |

**Constraints:**
- `MIN_WEIGHT = 0.10`
- `MAX_WEIGHT = 0.30`
- All weights normalized to sum = 1.0

---

### `save()`

Persists profile to disk.

```python
def save(self) -> str
```

**Returns:** Path to saved JSON file

---

### `load()` (class method)

Loads profile from disk.

```python
@classmethod
def load(cls, user_id: str) -> 'UserProfile'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | `str` | User identifier |

**Returns:** `UserProfile` instance

**Raises:** `FileNotFoundError` if profile doesn't exist

---

## Constants

### `ALL_EMOTIONS`

```python
ALL_EMOTIONS: List[str]  # 27 emotion names
```

### `STATE_ACTIVATION_CONFIG`

```python
STATE_ACTIVATION_CONFIG = {
    'mid_term': {'min_days': 14, 'min_messages': 30},
    'long_term': {'min_days': 90, 'min_messages': 50}
}
```

### `INITIAL_WEIGHTS`

```python
INITIAL_WEIGHTS = {
    'short_term': 0.15,
    'mid_term': 0.10,
    'long_term': 0.02
}
```

---

# chat_logger.py

## `log_interaction()`

Logs interaction to Excel file.

```python
def log_interaction(
    user_id: str,
    message: str,
    detected_emotions: Dict[str, float],
    temporal_category: str,
    state_updates: Dict[str, Dict[str, float]],
    timestamp: datetime = None
) -> str
```

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | `str` | ✅ | User identifier |
| `message` | `str` | ✅ | Message text |
| `detected_emotions` | `Dict[str, float]` | ✅ | All 27 emotions |
| `temporal_category` | `str` | ✅ | Temporal category |
| `state_updates` | `Dict[str, Dict]` | ✅ | Updated states |
| `timestamp` | `datetime` | ❌ | Log timestamp |

**Returns:** Path to Excel file

---

## `export_profile_history()`

Exports full profile history to Excel.

```python
def export_profile_history(user_id: str) -> str
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | `str` | User identifier |

**Returns:** Path to exported Excel file

---

## Type Summary

### Common Types

```python
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Emotion dict type (used everywhere)
EmotionDict = Dict[str, float]  # emotion_name → score (0-1)

# State update type
StateUpdates = Dict[str, Dict[str, float]]  # {
    # 'short_term': EmotionDict,
    # 'mid_term': EmotionDict,
    # 'long_term': EmotionDict
# }

# Impact multipliers
ImpactMultipliers = Dict[str, float]  # {'ST': 0.7, 'MT': 0.2, 'LT': 0.1}
```

---

## Error Handling

### Common Exceptions

| Exception | Raised By | When |
|-----------|-----------|------|
| `FileNotFoundError` | `UserProfile.load()` | Profile doesn't exist |
| `requests.RequestException` | `classify_emotions()` | API failure |
| `ValueError` | `categorize_temporal()` | Invalid input |

### Graceful Degradation

```python
# emotional_detector.py handles API failures gracefully
try:
    emotions = classify_emotions(text)
except Exception:
    emotions = {e: 0.0 for e in ALL_EMOTIONS}  # Neutral fallback
```

---

## What's Next?

Learn about configuration and environment setup:

👉 **Continue to [08-configuration.md](./08-configuration.md)** for environment and settings documentation.

---

**Navigation:**
| Previous | Current | Next |
|----------|---------|------|
| [06-module-reference.md](./06-module-reference.md) | 07-api-reference.md | [08-configuration.md](./08-configuration.md) |
