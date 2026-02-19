# Emotional State Analysis Module

> **Official Documentation** | Version 2.0  
> **Repository**: [V1629/state_analysis_module](https://github.com/V1629/state_analysis_module)  
> **Last Updated**: February 2026

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Module Reference](#module-reference)
5. [Documentation Index](#documentation-index)

---

## Overview

The **Emotional State Analysis Module** is a real-time emotional state tracking system that analyzes user messages to detect emotions, extract temporal references, and build evolving emotional profiles across three temporal dimensions:

- **Short-Term (ST)**: Recent emotions (0-30 days) — captures current mood
- **Mid-Term (MT)**: Rolling patterns (31-365 days) — tracks emotional trends  
- **Long-Term (LT)**: Baseline personality (365+ days) — represents stable traits

### What It Does

When a user sends a message like:

```
"Yaar 3 saal pehle dadi chali gayi thi, aaj bhi bahut yaad aati hai"
```

The system will:

| Step | Action | Result |
|------|--------|--------|
| 1 | **Detect emotions** | `sadness (0.72)`, `grief (0.15)`, `love (0.08)` |
| 2 | **Extract temporal references** | `"3 saal pehle"` → 1095 days ago (distant) |
| 3 | **Calculate impact** | `0.85` (high — strong emotion + personal loss) |
| 4 | **Update emotional profile** | ST, MT, LT states adjust via EMA |
| 5 | **Log everything** | Chat logs exported to Excel with full tracking |

### Key Features

- 🌍 **Multilingual Support**: English, Hindi, and Hinglish
- 😊 **27 Emotion Detection**: Using HuggingFace multilingual model
- ⏰ **Temporal Extraction**: 40+ regex patterns for time expressions
- 📈 **EMA-Based Learning**: Smooth, adaptive state evolution
- 💾 **Persistent Profiles**: JSON-based user profile storage
- 📊 **Excel Logging**: Comprehensive chat history with emotional states

---

## Architecture

The module follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│         (test_orchestrator.py / auto_test.py)           │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    ORCHESTRATOR                          │
│              (orchestrator.py)                          │
│   • Impact Calculation  • State Management              │
│   • Adaptive Weights    • Behavioral Analysis           │
└──────┬────────────────────────────────────┬─────────────┘
       │                                    │
┌──────▼──────────┐              ┌──────────▼──────────┐
│ EMOTION DETECTOR│              │ TEMPORAL EXTRACTOR  │
│emotional_detector│              │temporal_extractor.py│
│      .py        │              │                     │
│ • HuggingFace   │              │ • Regex Patterns    │
│ • 27 emotions   │              │ • Date Parsing      │
└──────┬──────────┘              └──────────┬──────────┘
       │                                    │
       └────────────────┬───────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   USER PROFILE                           │
│                (user_profile.py)                        │
│   • Short/Mid/Long Term States  • Message History       │
│   • Adaptive Weights            • JSON Persistence      │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   CHAT LOGGER                            │
│                 (chat_logger.py)                        │
│   • Excel Export  • State Tracking  • History Analysis  │
└─────────────────────────────────────────────────────────┘
```

For detailed architecture diagrams, see:
- [Architecture Diagram](./diagrams/architecture-diagram.md)
- [Sequence Diagram](./diagrams/sequence-diagram.md)
- [State Evolution Diagram](./diagrams/state-diagram.md)

---

## Quick Start

### Prerequisites

- Python 3.10+
- HuggingFace account (free) for emotion detection API

### Installation

```bash
# Clone the repository
git clone https://github.com/V1629/state_analysis_module.git
cd state_analysis_module

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up HuggingFace token
echo "hf_token=hf_YOUR_TOKEN_HERE" > .env

# Run interactive chat
python test_orchestrator.py
```

### Verify Installation

```bash
# Run unit tests
pytest test_ema.py -v

# Run automated test (75 messages)
python auto_test.py
```

---

## Module Reference

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| [`orchestrator.py`](./modules/orchestrator.md) | Core engine — ties everything together | `ImpactCalculator`, `process_user_message()` |
| [`emotional_detector.py`](./modules/emotional-detector.md) | Emotion detection via HuggingFace API | `classify_emotions()` |
| [`temporal_extractor.py`](./modules/temporal-extractor.md) | Temporal reference extraction | `TemporalExtractor`, `ParsedTemporal` |
| [`user_profile.py`](./modules/user-profile.md) | User emotional profile management | `UserProfile`, `ALL_EMOTIONS` |
| [`chat_logger.py`](./modules/chat-logger.md) | Excel logging for chat history | `ChatLogger` |

---

## Documentation Index

### Core Documentation

| Document | Description |
|----------|-------------|
| [📖 Documentation Overview](./documentation.md) | This file — main entry point |
| [🏗️ Architecture Guide](./architecture-guide.md) | System design and component interaction |
| [🔧 API Reference](./api-reference.md) | Function signatures and usage examples |
| [📊 Data Flow](./data-flow.md) | How data moves through the system |
| [⚙️ Configuration](./configuration.md) | Environment setup and parameters |

### Technical Deep-Dives

| Document | Description |
|----------|-------------|
| [📈 EMA Approach](./ema-approach.md) | Exponential Moving Average technical design |
| [🔄 State Management](./state-management.md) | Temporal state classification and transitions |

### Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture Diagram](./diagrams/architecture-diagram.md) | High-level system flow |
| [Sequence Diagram](./diagrams/sequence-diagram.md) | Interaction cycle |
| [State Diagram](./diagrams/state-diagram.md) | Profile evolution states |
| [ER Diagram](./diagrams/entity-relationship-diagram.md) | Data storage structure |
| [State Management Flow](./diagrams/state-management-flow.md) | Complete state pipeline |
| [User Interaction Flow](./diagrams/user-interaction-flow.md) | Message processing flow |

### Module Documentation

| Module | Description |
|--------|-------------|
| [Orchestrator](./modules/orchestrator.md) | Central coordination and impact calculation |
| [Emotional Detector](./modules/emotional-detector.md) | HuggingFace emotion classification |
| [Temporal Extractor](./modules/temporal-extractor.md) | Time expression parsing |
| [User Profile](./modules/user-profile.md) | Profile state management |
| [Chat Logger](./modules/chat-logger.md) | Excel export functionality |

---

## License

MIT License — see [LICENSE](../LICENSE) for details.

---

## Contributing

Contributions welcome! See the main [README](../README.md) for contribution guidelines.
