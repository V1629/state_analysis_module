# Emotional Detector Module

> **Module**: `emotional_detector.py`  
> **Purpose**: Emotion classification using HuggingFace multilingual model

---

## Overview

The Emotional Detector module handles emotion classification from text using the HuggingFace Inference API. It supports multilingual input (English, Hindi, Hinglish) and detects 27 distinct emotions.

### Responsibilities

- Connect to HuggingFace Inference API
- Classify emotions from input text
- Return probability scores for all emotions
- Handle API errors gracefully

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `hf_token` | Yes | HuggingFace API token |

Create a `.env` file in the project root:
```bash
hf_token=hf_YOUR_TOKEN_HERE
```

### Model

| Property | Value |
|----------|-------|
| **Model Name** | `AnasAlokla/multilingual_go_emotions` |
| **Provider** | HuggingFace Inference API |
| **Task** | Text Classification |
| **Languages** | English, Hindi, Hinglish, and more |

---

## Supported Emotions (27)

The model detects 27 emotion categories:

| Category | Emotions |
|----------|----------|
| **Positive** | admiration, amusement, approval, caring, excitement, gratitude, joy, love, optimism, pride, relief |
| **Negative** | anger, annoyance, disappointment, disapproval, disgust, embarrassment, fear, grief, nervousness, remorse, sadness |
| **Neutral** | confusion, curiosity, desire, neutral, realization, surprise |

---

## Function: `classify_emotions(text)`

Main function for emotion classification.

### Signature

```python
def classify_emotions(text: str) -> Dict[str, float]
```

### Parameters

| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | Input text (any supported language) |

### Returns

`Dict[str, float]` — Dictionary mapping emotion names to probability scores

### Example

```python
from emotional_detector import classify_emotions

# English
emotions = classify_emotions("I'm so happy today!")
# {"joy": 0.82, "optimism": 0.12, "excitement": 0.04, ...}

# Hindi
emotions = classify_emotions("मुझे बहुत खुशी है")
# {"joy": 0.78, "excitement": 0.10, "gratitude": 0.05, ...}

# Hinglish
emotions = classify_emotions("Yaar bahut sad feel ho raha hai")
# {"sadness": 0.75, "disappointment": 0.12, "grief": 0.08, ...}
```

### Error Handling

```python
# Empty input
emotions = classify_emotions("")
# Returns: {}

# API error
emotions = classify_emotions("some text")
# On error: prints error message, returns {}
```

---

## Implementation Details

### API Client Initialization

```python
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv('hf_token')

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN,
)
```

### Classification Process

```python
def classify_emotions(text: str) -> Dict[str, float]:
    if not text or len(text.strip()) == 0:
        return {}
    
    try:
        # Call HuggingFace API
        classification_result = client.text_classification(
            text,
            model=MODEL_NAME,
        )
        
        # Convert to dictionary
        emotions_with_scores = {}
        for emotion_item in classification_result:
            emotion_name = emotion_item['label']
            emotion_probability = emotion_item['score']
            emotions_with_scores[emotion_name] = emotion_probability
        
        return emotions_with_scores
    
    except Exception as error:
        print(f"❌ Error in emotion classification: {error}")
        return {}
```

---

## Output Format

The function returns all 27 emotions with their probability scores:

```python
{
    "sadness": 0.72,
    "grief": 0.15,
    "love": 0.08,
    "caring": 0.03,
    "neutral": 0.01,
    "disappointment": 0.01,
    # ... remaining emotions with scores
}
```

**Properties:**
- All probabilities sum to approximately 1.0
- Sorted by probability (descending) when displayed
- Emotions with probability < 0.01 are typically negligible

---

## Integration with Orchestrator

The orchestrator uses emotion detection as follows:

```python
from emotional_detector import classify_emotions
from orchestrator import ImpactCalculator

# Step 1: Detect emotions
emotions = classify_emotions(user_message)

# Step 2: Calculate intensity
intensity = ImpactCalculator.calculate_emotion_intensity(emotions)

# Step 3: Get top emotions for logging
top_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
```

---

## Testing

### Interactive Testing

Run the module directly for interactive testing:

```bash
python emotional_detector.py
```

This starts an interactive loop:
```
🌍 Multilingual Emotion Detector
📝 Enter text: I'm feeling stressed about exams

🔎 Emotion Predictions:
   nervousness          │ ████████████████     │ 0.6523
   fear                 │ ████████             │ 0.3210
   ...
```

### Unit Testing

```python
def test_emotion_detection():
    emotions = classify_emotions("I am very happy")
    assert "joy" in emotions
    assert emotions["joy"] > 0.5
    
def test_empty_input():
    emotions = classify_emotions("")
    assert emotions == {}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `HF_TOKEN environment variable not set` | Create `.env` file with `hf_token=your_token` |
| `Error initializing HuggingFace client` | Check token validity and network connection |
| Empty results | Verify text is not empty, check API rate limits |
| Unexpected emotions | Model may interpret context differently; verify input |

---

## Related Documentation

- [API Reference](../api-reference.md) — Complete function signatures
- [Orchestrator Module](./orchestrator.md) — Impact calculation
- [Data Flow](../data-flow.md) — How emotions are processed
