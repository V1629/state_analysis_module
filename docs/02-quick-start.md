# 02 — Quick Start

> **Reading time:** 10 minutes  
> **Prerequisites:** [01-introduction.md](./01-introduction.md)  
> **Next:** [03-architecture.md](./03-architecture.md)

---

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.10+** installed
- ✅ A **HuggingFace account** (free) — [Sign up here](https://huggingface.co/join)
- ✅ **Git** for cloning the repository

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/V1629/state_analysis_module.git
cd state_analysis_module
```

---

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

You should see `(venv)` in your terminal prompt.

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**What gets installed:**
| Package | Purpose |
|---------|---------|
| `huggingface_hub` | HuggingFace Inference API |
| `python-dotenv` | Environment variable loading |
| `openpyxl` | Excel file creation |
| `dateparser` | Date parsing (optional but recommended) |
| `pytest` | Unit testing |

---

## Step 4: Set Up HuggingFace API Token

1. Go to [HuggingFace Tokens](https://huggingface.co/settings/tokens)
2. Click **"New token"**
3. Name it (e.g., "emotional-state-module")
4. Select **"Read"** access
5. Copy the token

Create a `.env` file in the project root:

```bash
echo "hf_token=hf_YOUR_TOKEN_HERE" > .env
```

**Replace `hf_YOUR_TOKEN_HERE` with your actual token.**

---

## Step 5: Run the Interactive Test

```bash
python test_orchestrator.py
```

You should see:
```
✅ HuggingFace client initialized successfully
💬 You: 
```

---

## Step 6: Try It Out!

Type a message and see the analysis:

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

---

## Interactive Commands

Inside the chat, you can use these commands:

| Command | What it does |
|---------|--------------|
| `profile` | View your full emotional profile |
| `history` | See emotion frequency analysis |
| `states` | See short/mid/long-term activation status |
| `exit` | Quit the chat |

**Example:**
```
💬 You: states

📊 STATE ACTIVATION STATUS:
   ⚡ Short-term: Active (always)
   📈 Mid-term: Not activated (need 30 messages or 14 days)
   🏛️ Long-term: Not activated (need 50 messages or 90 days)
```

---

## Step 7: Run Automated Test (Optional)

To see the full emotional journey simulation:

```bash
python auto_test.py
```

This sends **75 pre-written Hinglish messages** simulating a realistic emotional journey:

| Phase | Messages | Emotional State |
|-------|----------|-----------------|
| Casual Start | 1–10 | 😐 Neutral |
| Mild Stress | 11–20 | 😟 Work pressure |
| Growing Doubt | 21–30 | 😰 Self-doubt |
| Emotional Low | 31–42 | 😢 Sadness |
| Turning Point | 43–52 | 🌤️ Small positives |
| Building Up | 53–63 | 😊 Improvement |
| Feeling Strong | 64–75 | 💪 Confidence |

After running, check `chat_logs.xlsx` for the complete analysis.

---

## Step 8: Run Unit Tests

```bash
pytest test_ema.py -v
```

Expected output:
```
test_ema.py::test_ema_update PASSED
test_ema.py::test_adaptive_alpha PASSED
test_ema.py::test_state_activation PASSED
...
```

---

## Verify Installation Checklist

- [ ] `python test_orchestrator.py` runs without errors
- [ ] Emotions are detected from your messages
- [ ] Temporal references are extracted
- [ ] Impact scores are calculated
- [ ] `chat_logs.xlsx` is created after chatting

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `HF_TOKEN environment variable not set` | Create `.env` file with `hf_token=your_token` |
| `ModuleNotFoundError: huggingface_hub` | Run `pip install -r requirements.txt` |
| `dateparser not installed` warning | Run `pip install dateparser` |
| `chat_logs.xlsx` not created | Check write permissions in directory |
| API rate limit errors | Wait a few minutes, HuggingFace has rate limits |

---

## What's Next?

Now that you have the module running, it's time to understand **how it works**:

👉 **Continue to [03-architecture.md](./03-architecture.md)** to learn about the system design.

---

**Navigation:**
| Previous | Current | Next |
|----------|---------|------|
| [01-introduction.md](./01-introduction.md) | 02-quick-start.md | [03-architecture.md](./03-architecture.md) |
