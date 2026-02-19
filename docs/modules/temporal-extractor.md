# Temporal Extractor Module

> **Module**: `temporal_extractor.py`  
> **Purpose**: Extract and parse temporal references from multilingual text

---

## Overview

The Temporal Extractor module identifies and parses time references from text, supporting English, Hindi, and Hinglish expressions. It uses a multi-strategy approach combining regex patterns, dateparser, and tense analysis.

### Responsibilities

- Detect temporal phrases in text
- Parse dates and calculate time gaps
- Categorize temporal references (recent, medium, distant, future)
- Calculate confidence scores
- Analyze verb tenses for ambiguity resolution

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 TEMPORAL EXTRACTOR                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │  Regex Patterns  │    │   Dateparser    │            │
│  │  (40+ patterns)  │    │  (absolute)     │            │
│  └────────┬────────┘    └────────┬────────┘            │
│           │                      │                      │
│           └──────────┬───────────┘                      │
│                      │                                  │
│  ┌───────────────────▼───────────────────┐             │
│  │          TimePhrase Detection          │             │
│  └───────────────────┬───────────────────┘             │
│                      │                                  │
│  ┌───────────────────▼───────────────────┐             │
│  │          TenseAnalyzer                 │             │
│  │    (ambiguity resolution)              │             │
│  └───────────────────┬───────────────────┘             │
│                      │                                  │
│  ┌───────────────────▼───────────────────┐             │
│  │          ParsedTemporal Output         │             │
│  └───────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## Data Classes

### `AgeCategory` (Enum)

Temporal age categories for event classification:

| Value | Description | Days Range |
|-------|-------------|------------|
| `RECENT` | Recent events | 0-30 days |
| `MEDIUM` | Medium-past events | 31-365 days |
| `DISTANT` | Distant events | 365+ days |
| `FUTURE` | Future events | Negative days |
| `UNKNOWN` | Could not determine | — |

---

### `TimePhrase`

Represents a detected temporal phrase in text.

```python
@dataclass
class TimePhrase:
    text: str           # "3 years ago"
    start_pos: int      # Starting position in text
    end_pos: int        # Ending position in text
    pattern_type: str   # "relative_past"
    language: str       # "english"
    context_window: str # Surrounding text for context
```

---

### `ParsedTemporal`

Represents a fully parsed temporal reference with metadata.

```python
@dataclass
class ParsedTemporal:
    phrase: str                    # "3 years ago"
    parsed_date: Optional[datetime] # 2023-02-19
    time_gap_days: Optional[int]   # 1095
    age_category: str              # "distant"
    confidence: float              # 0.95
    parse_method: str              # "regex"
    days_ago: int                  # 1095
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
```

---

## Class: `TenseAnalyzer`

Analyzes verb tenses to resolve ambiguous temporal references.

### Tense Indicators

**Past Indicators:**
| Language | Examples |
|----------|----------|
| English | was, were, did, had, went, happened |
| Hindi | tha, thi, the, gaya, gai, hui |
| Hinglish | tha, was, gaya, happened |

**Future Indicators:**
| Language | Examples |
|----------|----------|
| English | will, going to, shall, would, planning |
| Hindi | hoga, hogi, honge, karenge, jayenge |
| Hinglish | will, hoga, going to, karenge |

**Immediate Past:**
| Language | Examples |
|----------|----------|
| English | just, recently, just now, moments ago |
| Hindi | abhi, abhi hi, thodi der pehle |
| Hinglish | just, abhi, just now, recently |

### Method: `analyze_tense(full_message, language='mixed')`

```python
result = TenseAnalyzer.analyze_tense("I was feeling sad yesterday")
# {
#     'past_score': 0.8,
#     'future_score': 0.0,
#     'present_score': 0.2,
#     'dominant_tense': 'past'
# }
```

---

## Class: `TemporalExtractor`

Main extraction orchestrator.

### Regex Patterns (40+)

The extractor includes patterns for:

**English:**
- Relative: "X years/months/weeks/days ago"
- Absolute: "May 2020", "last Tuesday"
- Vague: "recently", "a while ago"

**Hindi:**
- Relative: "X saal/mahine/hafte/din pehle"
- Time units: "kal", "parso", "pichhle hafte"
- Vague: "bahut pehle", "kuch samay pehle"

**Hinglish (Mixed):**
- "2 years pehle"
- "last month mein"
- "kuch days ago"

### Method: `extract_all(text) → List[ParsedTemporal]`

Main extraction method.

```python
extractor = TemporalExtractor()
results = extractor.extract_all("3 saal pehle dadi chali gayi")

for ref in results:
    print(f"Phrase: {ref.phrase}")      # "3 saal pehle"
    print(f"Days ago: {ref.days_ago}")   # 1095
    print(f"Category: {ref.age_category}") # "distant"
    print(f"Confidence: {ref.confidence}")  # 0.95
```

### Method: `categorize_time_gap(days_ago) → str`

Categorize a time gap into predefined categories.

```python
category = extractor.categorize_time_gap(15)   # "recent"
category = extractor.categorize_time_gap(100)  # "medium"
category = extractor.categorize_time_gap(500)  # "distant"
category = extractor.categorize_time_gap(-7)   # "future"
```

---

## Confidence Scoring

Confidence is calculated based on:

1. **Pattern Match Quality**: How well the phrase matches known patterns
2. **Parse Success**: Whether dateparser could parse the date
3. **Tense Agreement**: Whether verb tense matches temporal direction
4. **Context Clarity**: Presence of supporting context

**Confidence Ranges:**

| Score | Interpretation |
|-------|----------------|
| 0.9-1.0 | High confidence, clear temporal reference |
| 0.7-0.9 | Good confidence, reliable interpretation |
| 0.5-0.7 | Moderate confidence, some ambiguity |
| < 0.5 | Low confidence, may need clarification |

---

## Language Support

### Supported Expressions

| Language | Expression | Days Ago |
|----------|------------|----------|
| English | "3 years ago" | 1095 |
| English | "last week" | ~7 |
| English | "yesterday" | 1 |
| Hindi | "3 saal pehle" | 1095 |
| Hindi | "pichhle hafte" | ~7 |
| Hindi | "kal" | 1 |
| Hinglish | "2 years pehle" | 730 |
| Hinglish | "last month mein" | ~30 |

### Future References

| Expression | Days Ahead |
|------------|------------|
| "next week" | -7 |
| "tomorrow" | -1 |
| "agle mahine" | ~-30 |
| "kal" (context-dependent) | -1 or 1 |

---

## Usage Examples

### Basic Extraction

```python
from temporal_extractor import TemporalExtractor

extractor = TemporalExtractor()

# English
results = extractor.extract_all("I lost my job 6 months ago")
# [ParsedTemporal(phrase='6 months ago', days_ago=180, category='medium')]

# Hindi
results = extractor.extract_all("2 saal pehle shaadi hui thi")
# [ParsedTemporal(phrase='2 saal pehle', days_ago=730, category='distant')]

# Hinglish
results = extractor.extract_all("Last year mein bahut kuch hua")
# [ParsedTemporal(phrase='Last year', days_ago=365, category='distant')]
```

### Multiple References

```python
text = "3 years ago I graduated, and last month I got promoted"
results = extractor.extract_all(text)

for ref in results:
    print(f"{ref.phrase}: {ref.age_category}")
# Output:
# 3 years ago: distant
# last month: recent
```

### Integration with Orchestrator

```python
from temporal_extractor import TemporalExtractor
from orchestrator import ImpactCalculator

extractor = TemporalExtractor()

# Extract temporal references
temporal_refs = extractor.extract_all(message)

if temporal_refs:
    primary_ref = temporal_refs[0]
    
    # Calculate recency weight
    recency = ImpactCalculator.calculate_recency_weight(primary_ref.days_ago)
    
    # Get state multipliers
    multipliers = ImpactCalculator.get_state_impact_multipliers(primary_ref.age_category)
```

---

## Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `dateparser` | Absolute date parsing | Optional (graceful degradation) |
| `re` | Regex pattern matching | Built-in |
| `datetime` | Date/time operations | Built-in |

Install optional dependency:
```bash
pip install dateparser
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `dateparser not installed` warning | Install with `pip install dateparser` |
| Wrong language detection | Check for language mixing in text |
| Ambiguous "kal" (yesterday/tomorrow) | Uses TenseAnalyzer for resolution |
| Low confidence scores | Provide more context in message |

---

## Related Documentation

- [API Reference](../api-reference.md) — Complete function signatures
- [Orchestrator Module](./orchestrator.md) — Impact calculation
- [Data Flow](../data-flow.md) — How temporal data flows through system
