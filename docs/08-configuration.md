# 08 — Configuration

> **Reading time:** 10 minutes  
> **Prerequisites:** [07-api-reference.md](./07-api-reference.md)  
> **Next:** [09-diagrams.md](./09-diagrams.md)

---

## Overview

This document covers all configuration options for the Emotional State Analysis Module.

---

# Environment Setup

## Required Environment Variables

Create a `.env` file in the project root:

```bash
# .env
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx
```

### Getting a HuggingFace API Key

1. Go to [huggingface.co](https://huggingface.co/)
2. Create an account or sign in
3. Go to **Settings** → **Access Tokens**
4. Click **New token**
5. Name it (e.g., "emotion-analysis")
6. Select **Read** access
7. Copy the token

---

## Python Dependencies

### requirements.txt

```txt
requests>=2.28.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
```

### Installation

```bash
pip install -r requirements.txt
```

---

# Module Configuration

## orchestrator.py

### Impact Calculator Settings

```python
# Default values
ENTROPY_PENALTY = 0.3       # Reduces confidence for ambiguous emotions
RECURRENCE_STEP = 0.3       # Boost per recent recurrence
BEHAVIOR_ALPHA = 0.2        # Behavioral pattern learning rate

# Temporal mapping thresholds
RECENT_DAYS = 30            # Days considered "recent"
MEDIUM_DAYS = 365           # Days considered "medium"
DISTANT_DAYS = 1825         # Days considered "distant" (5 years)
```

### Customizing Impact Calculator

```python
from orchestrator import ImpactCalculator

# Create custom calculator
calculator = ImpactCalculator(
    entropy_penalty=0.4,    # Higher penalty for ambiguity
    recurrence_step=0.2,    # Lower recurrence boost
    behavior_alpha=0.3      # Faster behavioral learning
)
```

---

## emotional_detector.py

### API Configuration

```python
# Model selection
MODEL_ID = "AnasAlokla/multilingual_go_emotions"

# API endpoint
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

# Request timeout (seconds)
REQUEST_TIMEOUT = 30
```

### Customizing API Settings

```python
# In emotional_detector.py or your wrapper

import os

# Custom timeout
REQUEST_TIMEOUT = int(os.getenv('HF_TIMEOUT', 30))

# Custom model (if you want to use a different one)
MODEL_ID = os.getenv('HF_MODEL', 'AnasAlokla/multilingual_go_emotions')
```

---

## temporal_extractor.py

### Temporal Category Thresholds

```python
# Default category boundaries (in days)
TEMPORAL_THRESHOLDS = {
    'recent': (0, 30),       # 0-30 days ago
    'medium': (31, 365),     # 1-12 months ago
    'distant': (366, float('inf'))  # 1+ years ago
}

# Future is automatically: days_ago < 0
```

### Confidence Thresholds

```python
# Minimum confidence for time phrase detection
MIN_CONFIDENCE = 0.5

# High confidence threshold
HIGH_CONFIDENCE = 0.8
```

---

## user_profile.py

### State Activation Thresholds

```python
STATE_ACTIVATION_CONFIG = {
    'mid_term': {
        'min_days': 14,          # Minimum days for MT activation
        'min_messages': 30       # OR minimum messages
    },
    'long_term': {
        'min_days': 90,          # Minimum days for LT activation
        'min_messages': 50       # OR minimum messages
    }
}
```

### Learning Rates (Alpha Values)

```python
INITIAL_WEIGHTS = {
    'short_term': 0.15,   # Fast adaptation (~7 message window)
    'mid_term': 0.10,     # Moderate adaptation
    'long_term': 0.02     # Slow, stable (~50 message window)
}
```

### Adaptive Learning Configuration

```python
# Decay constant for adaptive alpha
ALPHA_DECAY_CONSTANT = 200  # Higher = slower decay

# Formula: effective_alpha = base_alpha / (1 + message_count / decay_constant)
```

### Profile Storage

```python
# Directory for user profiles
PROFILE_DIR = "user_profiles"

# Profile file format
PROFILE_FORMAT = "{user_id}.json"

# Chat log format
CHATLOG_FORMAT = "{user_id}_chat_log.xlsx"
```

---

## chat_logger.py

### Excel Styling

```python
# Header colors
HEADER_FONT_COLOR = "FFFFFF"
HEADER_BG_COLOR = "4472C4"

# High emotion highlighting
HIGH_EMOTION_THRESHOLD = 0.7
HIGH_EMOTION_COLOR = "FFFF00"  # Yellow

# Column widths
TIMESTAMP_WIDTH = 20
MESSAGE_WIDTH = 50
EMOTION_WIDTH = 12
```

---

# Full Configuration Example

## config.py (Optional)

You can create a central configuration file:

```python
"""
config.py - Central configuration for Emotional State Analysis Module
"""

import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# ENVIRONMENT
# =============================================================================
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

# =============================================================================
# EMOTIONAL DETECTOR
# =============================================================================
HF_MODEL = "AnasAlokla/multilingual_go_emotions"
HF_TIMEOUT = 30  # seconds

# =============================================================================
# TEMPORAL EXTRACTION
# =============================================================================
TEMPORAL_THRESHOLDS = {
    'recent': 30,
    'medium': 365,
    'distant': 1825
}

# =============================================================================
# IMPACT CALCULATION
# =============================================================================
ENTROPY_PENALTY = 0.3
RECURRENCE_STEP = 0.3
BEHAVIOR_ALPHA = 0.2

# =============================================================================
# STATE MANAGEMENT
# =============================================================================
STATE_ACTIVATION = {
    'mid_term': {'min_days': 14, 'min_messages': 30},
    'long_term': {'min_days': 90, 'min_messages': 50}
}

LEARNING_RATES = {
    'short_term': 0.15,
    'mid_term': 0.10,
    'long_term': 0.02
}

ALPHA_DECAY_CONSTANT = 200

# =============================================================================
# STORAGE
# =============================================================================
PROFILE_DIR = "user_profiles"

# =============================================================================
# LOGGING
# =============================================================================
EXCEL_HIGH_EMOTION_THRESHOLD = 0.7
```

---

# Tuning Guide

## When to Adjust Learning Rates

| Scenario | Adjustment |
|----------|------------|
| Users have volatile moods | Increase ST alpha (0.20-0.25) |
| Need faster adaptation | Increase all alphas |
| Need more stability | Decrease all alphas |
| New users adapt too slowly | Increase decay constant |
| Mature profiles too stable | Decrease decay constant |

---

## When to Adjust State Activation

| Scenario | Adjustment |
|----------|------------|
| Users interact frequently | Decrease min_messages |
| Users interact rarely | Increase min_days |
| Want MT earlier | Decrease both MT thresholds |
| Want more reliable LT | Increase LT thresholds |

---

## Impact Multiplier Tuning

### Default Mappings

```python
IMPACT_MAPPINGS = {
    'recent': {'ST': 0.70, 'MT': 0.20, 'LT': 0.10},
    'medium': {'ST': 0.30, 'MT': 0.50, 'LT': 0.20},
    'distant': {'ST': 0.05, 'MT': 0.30, 'LT': 0.80},
    'future': {'ST': 0.70, 'MT': 0.40, 'LT': 0.00}
}
```

### When to Adjust

| Scenario | Adjustment |
|----------|------------|
| Distant events affect current mood too much | Decrease distant ST |
| Recent events don't impact LT enough | Increase recent LT |
| Future anxiety too high | Decrease future ST |

---

# Directory Structure

```
project/
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── config.py               # (Optional) Central config
├── orchestrator.py
├── emotional_detector.py
├── temporal_extractor.py
├── user_profile.py
├── chat_logger.py
├── user_profiles/          # Auto-created
│   ├── user123.json
│   └── user123_chat_log.xlsx
└── docs/                   # Documentation
```

---

## What's Next?

View all system diagrams in one place:

👉 **Continue to [09-diagrams.md](./09-diagrams.md)** for the complete diagram collection.

---

**Navigation:**
| Previous | Current | Next |
|----------|---------|------|
| [07-api-reference.md](./07-api-reference.md) | 08-configuration.md | [09-diagrams.md](./09-diagrams.md) |
