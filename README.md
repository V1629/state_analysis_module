# Emotional State Analysis Module

A real-time emotional state tracking system that analyzes user messages to detect emotions, extract temporal references, and build evolving emotional profiles across short-term, mid-term, and long-term time horizons.

> Think of it as a system that **understands how you're feeling** — not just right now, but how your emotional state has been **shifting over time**.

---

## What Does This Project Do?

When a user sends a message like:

```
"Yaar 3 saal pehle dadi chali gayi thi, aaj bhi bahut yaad aati hai"
```

The system will:

1. **Detect emotions** → `sadness (0.72)`, `grief (0.15)`, `love (0.08)`
2. **Extract temporal references** → `"3 saal pehle"` → 1095 days ago (distant)
3. **Calculate impact** → `0.85` (high — strong emotion + personal loss)
4. **Update emotional profile** → Short-term, Mid-term, and Long-term states adjust via EMA (Exponential Moving Average)
5. **Log everything** → Chat logs exported to Excel with full state tracking

---

##  Project Structure

```
files/
├── orchestrator.py          # 🎯 Core engine — ties everything together
├── emotional_detector.py    # 😊 Emotion detection via HuggingFace API
├── temporal_extractor.py    # ⏰ Temporal reference extraction (EN/HI/Hinglish)
├── user_profile.py          # 👤 User emotional profile with EMA-based state tracking
├── chat_logger.py           # 📊 Excel logger for chat + emotional state
├── test_orchestrator.py     # 🧪 Interactive test script (manual chat)
├── auto_test.py             # 🤖 Automated test — sends 75 Hinglish messages
├── test_ema.py              # ✅ Unit tests for EMA implementation
├── requirements.txt         # 📦 Python dependencies
├── .env                     # 🔑 HuggingFace API token (you create this)
│
├── architecture.md          # System architecture diagrams (Mermaid)
├── EMA_approach.md          # EMA technical design document
├── state_management.md      # State management flow diagrams
├── user_flow.md             # User interaction flow diagram
│
├── user_profiles/           # 💾 Saved user profiles (JSON)
└── chat_logs.xlsx           # 📋 Generated chat logs (auto-created)
```

---

## ⚡ Quick Setup (5 minutes)

### Prerequisites

- Python 3.10+
- A free [HuggingFace](https://huggingface.co/) account (for the emotion detection API)

### Step 1 — Clone the repo

```bash
git clone https://github.com/V1629/state_analysis_module.git
cd state_analysis_module
```

### Step 2 — Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set up your HuggingFace API token

1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token (read access is enough)
3. Create a `.env` file in the project root:

```bash
echo "hf_token=hf_YOUR_TOKEN_HERE" > .env
```

### Step 5 — Run it!

```bash
python test_orchestrator.py
```

That's it. You'll see a `💬 You:` prompt — start chatting!

---

## 🚀 How to Use

### Option 1: Interactive Chat (Manual)

```bash
python test_orchestrator.py
```

Type messages and see real-time analysis:

```
💬 You: I'm really stressed about my exams next week

😊 EMOTIONS DETECTED:
   1. nervousness           │ ████████████████          │ 0.6523
   2. fear                  │ ████████                  │ 0.3210

⏰ TEMPORAL REFERENCES:
   Phrases found: ['next week']
   • next week → Category: future | Confidence: 0.95

💥 IMPACT SCORE: 0.7842 🟡 MEDIUM
```

**Commands inside the chat:**

| Command    | What it does                              |
|------------|-------------------------------------------|
| `profile`  | View your full emotional profile          |
| `history`  | See emotion frequency analysis            |
| `states`   | See short/mid/long-term activation status |
| `exit`     | Quit the chat                             |

### Option 2: Automated Test (75 Messages)

```bash
python auto_test.py
```

This sends 75 pre-written Hinglish messages that simulate a **realistic emotional journey**:

| Phase | Messages | Emotional State |
|-------|----------|-----------------|
| Casual Start | 1–10 | 😐 Neutral — just vibing |
| Mild Stress | 11–20 | 😟 Work pressure creeping in |
| Growing Doubt | 21–30 | 😰 Self-doubt, overthinking |
| Emotional Low | 31–42 | 😢 Sadness, isolation, vulnerability |
| Turning Point | 43–52 | 🌤️ Small positive moments |
| Building Up | 53–63 | 😊 Improvement, momentum |
| Feeling Strong | 64–75 | 💪 Gratitude, confidence, peace |

### Option 3: Run Unit Tests

```bash
pytest test_ema.py -v
```

---

## 🔬 How It Works (Under the Hood)

### The Pipeline

```
User Message
    │
    ├──► Emotion Detection (HuggingFace multilingual_go_emotions)
    │       → 27 emotions with probability scores
    │
    ├──► Temporal Extraction (Regex + dateparser)
    │       → "3 years ago" → 1095 days, category: distant
    │
    ├──► Impact Calculation
    │       → Weighted sum of: emotion intensity + recency + repetition + confidence
    │
    └──► Profile Update (EMA)
            → Short-term state  (⚡ reactive, α=0.15)
            → Mid-term state    (📈 moderate, rolling window of 15 messages)
            → Long-term state   (🏛️ stable baseline, α=0.02)
```

### Emotional State Tracking (EMA)

The system tracks emotions across **3 time horizons** using Exponential Moving Average:

```
State(t) = α × NewEmotion + (1 - α) × State(t-1)
```

| State | Activation | Learning Rate | Purpose |
|-------|------------|---------------|---------|
| **Short-term** ⚡ | From message 1 | α = 0.15 (fast) | Current mood |
| **Mid-term** 📈 | After 14 days + 30 messages | Rolling window | Emotional trends |
| **Long-term** 🏛️ | After 90 days + 50 messages | α = 0.02 (slow) | Personality baseline |

### Supported Languages

| Language | Example | Supported? |
|----------|---------|------------|
| English | "3 years ago", "last week" | ✅ |
| Hindi | "3 saal pehle", "kal" | ✅ |
| Hinglish | "last month mein", "2 years pehle" | ✅ |

---

## 📊 Output — Excel Logs

Every message is automatically logged to `chat_logs.xlsx` with:

| Column | Description |
|--------|-------------|
| Timestamp | When the message was sent |
| Message | The user's message |
| Impact Score | Calculated impact (0.0 – 1.0) |
| Current ST/MT/LT Emotion | Detected emotion for this message |
| Profile ST/MT/LT Emotion | Accumulated profile emotion |
| MT/LT Status | Whether mid/long-term states are active |
| Profile Age | Days since profile was created |
| Message Count | Total messages processed |

---

## 🧩 Key Components

### `emotional_detector.py`
- Uses the [`AnasAlokla/multilingual_go_emotions`](https://huggingface.co/AnasAlokla/multilingual_go_emotions) model via HuggingFace Inference API
- Detects **27 emotions** (joy, sadness, anger, fear, surprise, love, gratitude, etc.)
- Supports English, Hindi, and Hinglish text

### `temporal_extractor.py`
- **40+ regex patterns** for temporal extraction across 3 languages
- Parses relative dates ("3 years ago"), absolute dates ("May 2020"), and vague expressions ("bahut pehle")
- Categorizes into: `recent` (0-30d), `medium` (31-365d), `distant` (365d+), `future`

### `orchestrator.py`
- The **brain** of the system — connects emotion detection + temporal extraction + profile updates
- Calculates impact scores using: emotion intensity, recency weight, repetition boost, and temporal confidence
- Handles adaptive weight learning and behavioral analysis

### `user_profile.py`
- Manages per-user emotional profiles with EMA-based state updates
- Tracks 27 emotions across 3 time horizons
- Persists profiles to JSON for continuity across sessions
- Adaptive learning rate: α decreases as more data is collected (stabilizes over time)

---

## 📖 Documentation

| Document | What it covers |
|----------|---------------|
| [`architecture.md`](architecture.md) | System architecture with Mermaid diagrams |
| [`EMA_approach.md`](EMA_approach.md) | Full EMA technical design — all 14 parameter groups |
| [`state_management.md`](state_management.md) | State management flow and classification logic |
| [`user_flow.md`](user_flow.md) | End-to-end user interaction flow |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `No module named 'huggingface_hub'` | Run `pip install -r requirements.txt` inside venv |
| `HF_TOKEN environment variable not set` | Create a `.env` file with `hf_token=hf_YOUR_TOKEN` |
| `dateparser not installed` warning | Run `pip install dateparser` (optional but recommended) |
| Mid/Long-term states show "Not activated" | Send more messages — MT needs 30 msgs, LT needs 50 msgs |
| `chat_logs.xlsx` not created | It auto-creates on first message; check write permissions |

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional language support (Urdu, Bengali, Tamil)
- More advanced NLP-based temporal parsing
- Dashboard / web UI for visualizing emotional trends
- Integration with conversational AI frameworks
- Real-time WebSocket support
