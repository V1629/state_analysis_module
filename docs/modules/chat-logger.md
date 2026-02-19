# Chat Logger Module

> **Module**: `chat_logger.py`  
> **Purpose**: Excel export for chat history and emotional state tracking

---

## Overview

The Chat Logger module provides Excel export functionality for comprehensive chat analysis. It creates formatted workbooks that track messages, emotional states, and profile evolution over time.

### Responsibilities

- Create and manage Excel workbooks
- Log messages with emotional analysis
- Track state activation status
- Format output for readability
- Support analysis and debugging

---

## Excel Structure

### Columns

| Column | Description |
|--------|-------------|
| **Timestamp** | When the message was sent |
| **Message** | The user's message text |
| **Impact Score** | Calculated impact (0.0 – 1.0) |
| **Current_ST_Emotion** | Top short-term emotion for this message |
| **Current_ST_Score** | Score for top ST emotion |
| **Current_MT_Emotion** | Top mid-term emotion for this message |
| **Current_MT_Score** | Score for top MT emotion |
| **Current_LT_Emotion** | Top long-term emotion for this message |
| **Current_LT_Score** | Score for top LT emotion |
| **Profile_ST_Emotion** | Accumulated profile ST emotion |
| **Profile_ST_Score** | Score for profile ST emotion |
| **Profile_MT_Emotion** | Accumulated profile MT emotion |
| **Profile_MT_Score** | Score for profile MT emotion |
| **Profile_LT_Emotion** | Accumulated profile LT emotion |
| **Profile_LT_Score** | Score for profile LT emotion |
| **MT_Status** | Whether mid-term is activated |
| **LT_Status** | Whether long-term is activated |
| **Profile_Age_Days** | Days since profile creation |
| **Message_Count** | Total messages processed |

---

## Class: `ChatLogger`

### Constructor

```python
def __init__(self, file_path="chat_logs.xlsx")
```

**Parameters:**
- `file_path` (str): Path to the Excel file (default: "chat_logs.xlsx")

**Behavior:**
- Creates the file if it doesn't exist
- Sets up headers with formatting
- Configures column widths

---

### Method: `ensure_workbook()`

Creates the Excel file with proper structure if it doesn't exist.

```python
logger = ChatLogger("my_logs.xlsx")
# Automatically calls ensure_workbook() in __init__
```

**Header Styling:**
- Background: Blue (#4472C4)
- Font: White, Bold
- Alignment: Center, Wrapped text
- Row height: 30px

**Column Widths:**
| Column | Width |
|--------|-------|
| Timestamp | 25 |
| Message | 45 |
| Impact Score | 15 |
| Others | 18 |

---

### Method: `log_chat()`

Log a chat message with complete emotional state data.

```python
def log_chat(
    self,
    message: str,
    impact_score: float,
    current_state: dict,
    profile_state: dict,
    activation_status: dict = None,
    profile_age_days: int = 0,
    message_count: int = 0
)
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `message` | `str` | User's message |
| `impact_score` | `float` | Calculated impact (0.0-1.0) |
| `current_state` | `dict` | Current message emotions per state |
| `profile_state` | `dict` | Accumulated profile emotions |
| `activation_status` | `dict` | State activation status |
| `profile_age_days` | `int` | Days since profile creation |
| `message_count` | `int` | Total messages processed |

**Example:**

```python
logger = ChatLogger()

current_state = {
    'short_term': {'sadness': 0.72, 'grief': 0.15},
    'mid_term': {'sadness': 0.45, 'neutral': 0.30},
    'long_term': {'neutral': 0.35, 'sadness': 0.25}
}

profile_state = {
    'short_term': {'sadness': 0.55, 'joy': 0.20},
    'mid_term': {'neutral': 0.40, 'sadness': 0.30},
    'long_term': {'neutral': 0.45, 'joy': 0.25}
}

activation_status = {
    'short_term': True,
    'mid_term': True,
    'long_term': False
}

logger.log_chat(
    message="Miss my grandmother so much",
    impact_score=0.85,
    current_state=current_state,
    profile_state=profile_state,
    activation_status=activation_status,
    profile_age_days=45,
    message_count=150
)
```

---

## State Activation Handling

The logger shows "N/A" for states that aren't activated yet:

| Scenario | MT_Status | LT_Status | Display |
|----------|-----------|-----------|---------|
| New user (5 messages) | ❌ | ❌ | MT: N/A, LT: N/A |
| After 30 messages | ✅ | ❌ | MT: Active, LT: N/A |
| After 50+ messages | ✅ | ✅ | MT: Active, LT: Active |

---

## Output Example

A logged Excel row might look like:

| Timestamp | Message | Impact | ST_Emo | ST_Score | MT_Emo | MT_Score | ... |
|-----------|---------|--------|--------|----------|--------|----------|-----|
| 2026-02-19 14:30 | Miss my grandmother | 0.85 | sadness | 0.72 | sadness | 0.45 | ... |

---

## Integration

### With Orchestrator

```python
from orchestrator import process_user_message
from chat_logger import ChatLogger
from user_profile import UserProfile

logger = ChatLogger()
profile = UserProfile("user123")

# Process message
result = process_user_message(message, profile)

# Log the result
logger.log_chat(
    message=message,
    impact_score=result.impact_score,
    current_state={
        'short_term': result.current_emotions,
        'mid_term': result.current_emotions if profile.is_state_activated('mid_term') else {},
        'long_term': result.current_emotions if profile.is_state_activated('long_term') else {}
    },
    profile_state={
        'short_term': profile.short_term_state,
        'mid_term': profile.mid_term_state,
        'long_term': profile.long_term_state
    },
    activation_status=profile.state_activation_status,
    profile_age_days=profile.profile_age_days,
    message_count=profile.message_count
)
```

### With Test Scripts

The `test_orchestrator.py` and `auto_test.py` scripts automatically use the ChatLogger:

```bash
# Run interactive test
python test_orchestrator.py
# Creates/updates chat_logs.xlsx

# Run automated test
python auto_test.py
# Logs all 75 test messages
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `openpyxl` | Excel file creation and editing |
| `datetime` | Timestamp generation |
| `os` | File system operations |

Install:
```bash
pip install openpyxl
```

---

## File Management

### Default Location

The Excel file is created in the current working directory:
```
files/
├── orchestrator.py
├── chat_logger.py
├── chat_logs.xlsx  ← Created here
└── ...
```

### Custom Location

```python
# Log to a different file
logger = ChatLogger("/path/to/my_analysis.xlsx")
```

### Multiple Sessions

The logger appends to existing files, preserving previous logs:

```python
# Session 1
logger = ChatLogger()
logger.log_chat(...)  # Row 2

# Session 2 (same file)
logger = ChatLogger()
logger.log_chat(...)  # Row 3, continues from previous
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File not created | Check write permissions in directory |
| `ModuleNotFoundError: openpyxl` | Run `pip install openpyxl` |
| File locked error | Close Excel before running script |
| Missing columns | Delete file and restart to recreate |

---

## Related Documentation

- [API Reference](../api-reference.md) — Complete function signatures
- [User Profile Module](./user-profile.md) — Profile state management
- [Data Flow](../data-flow.md) — How data reaches the logger
