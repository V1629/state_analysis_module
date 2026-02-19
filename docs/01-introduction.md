# 01 — Introduction

> **Reading time:** 5 minutes  
> **Prerequisites:** None  
> **Next:** [02-quick-start.md](./02-quick-start.md)

---

## What is the Emotional State Analysis Module?

The **Emotional State Analysis Module** is a real-time emotional state tracking system that analyzes user messages to:

1. **Detect emotions** — Identify 27 different emotions from text
2. **Extract temporal references** — Understand when events happened
3. **Build evolving profiles** — Track emotions across three time horizons
4. **Calculate impact** — Determine how significant an emotional event is

> Think of it as a system that **understands how you're feeling** — not just right now, but how your emotional state has been **shifting over time**.

---

## The Problem It Solves

Traditional chatbots treat each message in isolation. They don't remember that:
- You mentioned losing your job **last week** (should affect mid-term response)
- Your grandmother passed away **3 years ago** (still affects long-term baseline)
- You've been stressed about exams **for the past month** (pattern recognition)

This module adds **temporal emotional intelligence** to AI companions.

---

## Key Capabilities

### 🌍 Multilingual Support

| Language | Example | Supported |
|----------|---------|:---------:|
| English | "3 years ago", "last week" | ✅ |
| Hindi | "3 saal pehle", "kal" | ✅ |
| Hinglish | "last month mein", "2 years pehle" | ✅ |

### 😊 27 Emotion Detection

The system detects a rich set of emotions:

| Positive | Negative | Neutral |
|----------|----------|---------|
| joy, love, gratitude | sadness, anger, fear | neutral, curiosity |
| excitement, optimism | grief, disappointment | confusion, surprise |
| pride, relief, caring | disgust, nervousness | realization, desire |

### ⏰ Three Temporal States

| State | Time Horizon | Purpose |
|-------|--------------|---------|
| **Short-Term (ST)** ⚡ | 0-30 days | Current mood |
| **Mid-Term (MT)** 📈 | 31-365 days | Ongoing patterns |
| **Long-Term (LT)** 🏛️ | 365+ days | Personality baseline |

---

## Example: How It Works

When a user sends:

```
"Yaar 3 saal pehle dadi chali gayi thi, aaj bhi bahut yaad aati hai"
```

The system processes it as:

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: "Yaar 3 saal pehle dadi chali gayi..."              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────────┐       ┌───────────────────┐
│ EMOTION DETECTION │       │ TEMPORAL EXTRACT  │
│                   │       │                   │
│ sadness:    0.72  │       │ "3 saal pehle"    │
│ grief:      0.15  │       │ → 1095 days ago   │
│ love:       0.08  │       │ → category: distant│
└────────┬──────────┘       └────────┬──────────┘
         │                           │
         └─────────────┬─────────────┘
                       ▼
            ┌─────────────────────┐
            │ IMPACT CALCULATION  │
            │                     │
            │ Score: 0.85 (HIGH)  │
            │ Strong emotion +    │
            │ personal loss +     │
            │ distant past        │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ PROFILE UPDATE      │
            │                     │
            │ ST: minimal (0.05)  │
            │ MT: moderate (0.30) │
            │ LT: high (0.80)     │
            │                     │
            │ → Affects long-term │
            │   baseline most     │
            └─────────────────────┘
```

**Result:** The system understands this is a significant emotional event from the distant past that primarily affects the user's long-term emotional baseline.

---

## Project Structure

```
files/
├── orchestrator.py          # 🎯 Core engine — ties everything together
├── emotional_detector.py    # 😊 Emotion detection via HuggingFace API
├── temporal_extractor.py    # ⏰ Temporal reference extraction
├── user_profile.py          # 👤 User emotional profile management
├── chat_logger.py           # 📊 Excel logger for chat history
│
├── test_orchestrator.py     # 🧪 Interactive test script
├── auto_test.py             # 🤖 Automated test (75 messages)
├── test_ema.py              # ✅ Unit tests for EMA
│
├── requirements.txt         # 📦 Python dependencies
├── .env                     # 🔑 HuggingFace API token
│
├── user_profiles/           # 💾 Saved user profiles (JSON)
└── docs/                    # 📚 You are here!
```

---

## Who Should Use This Documentation?

| Role | Focus Areas |
|------|-------------|
| **New Developer** | Start here, follow numbered order |
| **Backend Developer** | 03-architecture, 04-data-flow, 06-module-reference |
| **Data Scientist** | 05-core-concepts (EMA, PRISM) |
| **DevOps/Setup** | 02-quick-start, 08-configuration |
| **Debugger** | 09-diagrams, 07-api-reference |

---

## Next Steps

Now that you understand what this module does:

👉 **Continue to [02-quick-start.md](./02-quick-start.md)** to set up and run the module.

---

**Navigation:**
| Previous | Current | Next |
|----------|---------|------|
| — | 01-introduction.md | [02-quick-start.md](./02-quick-start.md) |
