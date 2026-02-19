# Configuration Guide

> **Emotional State Analysis Module** — Environment Setup and Configuration

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Required Dependencies](#required-dependencies)
3. [API Configuration](#api-configuration)
4. [Module Parameters](#module-parameters)
5. [State Activation Thresholds](#state-activation-thresholds)
6. [Adaptive Weights](#adaptive-weights)
7. [Impact Calculation Parameters](#impact-calculation-parameters)
8. [File Paths](#file-paths)

---

## Environment Setup

### System Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Operating System | Linux, macOS, Windows |
| Memory | 512MB+ |
| Network | Required for HuggingFace API |

### Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# .env file
hf_token=hf_YOUR_HUGGINGFACE_TOKEN_HERE
```

**Getting a HuggingFace Token:**
1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token (read access is sufficient)
3. Copy and paste into `.env`

---

## Required Dependencies

### `requirements.txt`

```txt
huggingface_hub>=0.20.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
pytest>=7.0.0
dateparser>=1.2.0
```

### Installation

```bash
pip install -r requirements.txt
```

### Optional Dependencies

| Package | Purpose | Install Command |
|---------|---------|-----------------|
| `dateparser` | Advanced date parsing | `pip install dateparser` |
| `pytest` | Unit testing | `pip install pytest` |

---

## API Configuration

### HuggingFace Inference API

| Setting | Value |
|---------|-------|
| **Provider** | `hf-inference` |
| **Model** | `AnasAlokla/multilingual_go_emotions` |
| **Task** | Text Classification |
| **Rate Limit** | Free tier: ~300 requests/hour |

### Configuration in Code

```python
# emotional_detector.py
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv('hf_token')

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN,
)

MODEL_NAME = "AnasAlokla/multilingual_go_emotions"
```

---

## Module Parameters

### Orchestrator Parameters

| Parameter | Default | Description | Location |
|-----------|---------|-------------|----------|
| `typing_speed_mean` | `1.0` | Baseline typing speed | `orchestrator.py:31` |
| `typing_speed_std` | `0.5` | Typing speed std dev | `orchestrator.py:32` |
| `max_days` | `730` | Max days for recency (2 years) | `orchestrator.py:54` |
| `entropy_penalty_coefficient` | `0.3` | Entropy penalty threshold | `orchestrator.py:70` |
| `recurrence_step` | `0.3` | Boost per recurrence | `orchestrator.py:118` |
| `max_recurrence_boost` | `2.5` | Maximum boost cap | `orchestrator.py:120` |
| `behavior_alpha` | `0.2` | Behavior multiplier strength | `orchestrator.py:209` |

### Temporal Extractor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Recent threshold | 30 days | 0-30 days = "recent" |
| Medium threshold | 365 days | 31-365 days = "medium" |
| Distant threshold | 365+ days | 365+ days = "distant" |

### User Profile Parameters

| Parameter | Default | Description | Location |
|-----------|---------|-------------|----------|
| `short_term_alpha` | `0.15` | ST learning rate | `user_profile.py` |
| `long_term_alpha` | `0.02` | LT learning rate | `user_profile.py` |
| `mid_term_window` | `15` | Rolling window size | `user_profile.py:45` |
| `decay_constant` | `200` | Alpha decay constant | `user_profile.py:76` |

---

## State Activation Thresholds

### Configuration

```python
# user_profile.py
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
        'description': 'Patterns over 2 weeks',
        'window_size': 15
    },
    'long_term': {
        'name': '🏛️ Long-term (365+ days)',
        'min_days': 90,
        'min_messages': 50,
        'description': 'Baseline personality over 3 months'
    }
}
```

### Activation Logic

Uses **OR logic**: State activates if EITHER time OR message threshold is met.

| State | Time Threshold | Message Threshold |
|-------|----------------|-------------------|
| Short-Term | 0 days | 1 message |
| Mid-Term | 14 days | 30 messages |
| Long-Term | 90 days | 50 messages |

### Customization

To change thresholds, modify `STATE_ACTIVATION_CONFIG` in `user_profile.py`:

```python
# Example: Activate mid-term earlier
STATE_ACTIVATION_CONFIG['mid_term']['min_days'] = 7
STATE_ACTIVATION_CONFIG['mid_term']['min_messages'] = 15
```

---

## Adaptive Weights

### Initial Weight Hierarchy

```python
# user_profile.py
INITIAL_WEIGHTS = {
    'emotion_intensity': 0.45,      # Highest - emotion is primary
    'recency_weight': 0.30,         # High - recent events matter
    'recurrence_boost': 0.15,       # Medium - patterns matter
    'temporal_confidence': 0.10     # Lowest - exact timing less critical
}
```

### Weight Constraints

| Weight | Min | Max | Description |
|--------|-----|-----|-------------|
| `emotion_intensity` | 0.35 | 0.55 | Primary emotion weight |
| `recency_weight` | 0.20 | 0.40 | Time recency weight |
| `recurrence_boost` | 0.05 | 0.25 | Pattern repetition weight |
| `temporal_confidence` | 0.05 | 0.15 | Parsing confidence weight |

### Per-User EMA Parameters

These parameters can evolve via EMA for personalization:

```python
# user_profile.py - UserProfile.__init__
self.entropy_penalty_coeff = 0.3
self.recurrence_step = 0.3
self.behavior_alpha = 0.2
self.similarity_threshold = 0.2
```

---

## Impact Calculation Parameters

### State Impact Multipliers

```python
# user_profile.py - UserProfile.__init__
self.impact_multipliers = {
    "recent": {"short_term": 1.0, "mid_term": 0.6, "long_term": 0.2},
    "medium": {"short_term": 0.3, "mid_term": 0.9, "long_term": 0.5},
    "distant": {"short_term": 0.05, "mid_term": 0.3, "long_term": 0.8},
    "unknown": {"short_term": 0.5, "mid_term": 0.5, "long_term": 0.3},
    "future": {"short_term": 0.7, "mid_term": 0.4, "long_term": 0.0}
}
```

### Interpretation

| Category | Primarily Affects |
|----------|-------------------|
| `recent` | Short-term (current mood) |
| `medium` | Mid-term (ongoing patterns) |
| `distant` | Long-term (personality baseline) |
| `future` | Short-term (anticipation) |

---

## File Paths

### Default Paths

| File | Default Path | Purpose |
|------|--------------|---------|
| User Profiles | `user_profiles/` | JSON profile storage |
| Chat Logs | `chat_logs.xlsx` | Excel chat history |
| Environment | `.env` | API tokens |

### Customization

**Custom Profile Directory:**
```python
# user_profile.py
PROFILE_DIR = "/custom/path/to/profiles"
```

**Custom Log File:**
```python
# In your script
from chat_logger import ChatLogger
logger = ChatLogger("/custom/path/to/logs.xlsx")
```

---

## Configuration Examples

### Development Configuration

```python
# Lower thresholds for faster testing
STATE_ACTIVATION_CONFIG['mid_term']['min_messages'] = 5
STATE_ACTIVATION_CONFIG['long_term']['min_messages'] = 10

# Higher learning rates for faster adaptation
short_term_alpha = 0.25
long_term_alpha = 0.05
```

### Production Configuration

```python
# Standard thresholds
STATE_ACTIVATION_CONFIG['mid_term']['min_messages'] = 30
STATE_ACTIVATION_CONFIG['long_term']['min_messages'] = 50

# Lower learning rates for stability
short_term_alpha = 0.15
long_term_alpha = 0.02
```

### High-Sensitivity Configuration

```python
# For emotional support applications
INITIAL_WEIGHTS = {
    'emotion_intensity': 0.55,      # Higher emotion weight
    'recency_weight': 0.25,
    'recurrence_boost': 0.15,
    'temporal_confidence': 0.05
}

# Lower entropy penalty for mixed emotions
entropy_penalty_coefficient = 0.2
```

---

## Troubleshooting Configuration Issues

| Issue | Solution |
|-------|----------|
| `HF_TOKEN not found` | Create `.env` file with `hf_token=your_token` |
| `dateparser not installed` | Run `pip install dateparser` |
| Profiles not saving | Check write permissions on `user_profiles/` |
| States not activating | Verify message count meets thresholds |
| Impact always 0 | Check adaptive weights sum to 1.0 |

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `hf_token` | Yes | — | HuggingFace API token |

---

## Related Documentation

- [API Reference](./api-reference.md) — Complete function signatures
- [Architecture Guide](./architecture-guide.md) — System design
- [Data Flow](./data-flow.md) — How data moves through the system
