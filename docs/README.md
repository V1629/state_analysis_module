# 📚 Emotional State Analysis Module — Documentation

> **Welcome, Developer!** This guide will help you understand the module completely.

---

## 🎯 Reading Order for New Developers

Follow this sequence to build understanding layer by layer:

| Order | Document | Time | What You'll Learn |
|:-----:|----------|:----:|-------------------|
| **1** | [01-introduction.md](./01-introduction.md) | 5 min | What this module does, why it exists |
| **2** | [02-quick-start.md](./02-quick-start.md) | 10 min | Setup, run the module, see it in action |
| **3** | [03-architecture.md](./03-architecture.md) | 15 min | High-level design, component overview |
| **4** | [04-data-flow.md](./04-data-flow.md) | 15 min | How data moves through the pipeline |
| **5** | [05-core-concepts.md](./05-core-concepts.md) | 20 min | EMA, PRISM, State Management theory |
| **6** | [06-module-reference.md](./06-module-reference.md) | 30 min | Each Python file explained in detail |
| **7** | [07-api-reference.md](./07-api-reference.md) | 20 min | Function signatures, parameters, examples |
| **8** | [08-configuration.md](./08-configuration.md) | 10 min | Environment setup, thresholds, tuning |
| **9** | [09-diagrams.md](./09-diagrams.md) | 10 min | All visual diagrams in one place |

**Total estimated reading time:** ~2.5 hours for complete understanding

---

## 🗂️ Documentation Structure

```
docs/
├── README.md                 ← You are here (Start!)
├── 01-introduction.md        ← What & Why
├── 02-quick-start.md         ← Get it running
├── 03-architecture.md        ← System design
├── 04-data-flow.md           ← Data pipeline
├── 05-core-concepts.md       ← EMA, PRISM, States
├── 06-module-reference.md    ← File-by-file guide
├── 07-api-reference.md       ← Functions & classes
├── 08-configuration.md       ← Setup & tuning
└── 09-diagrams.md            ← All Mermaid diagrams
```

---

## 🚀 Quick Reference by Task

### "I'm completely new to this project"
→ Start with **01-introduction.md** and follow the numbered order

### "I need to set up the development environment"
→ Jump to **02-quick-start.md**

### "I need to understand how a specific function works"
→ Go to **07-api-reference.md**

### "I need to fix a bug in the orchestrator"
→ Read **06-module-reference.md** § Orchestrator, then **04-data-flow.md**

### "I need to understand the math behind EMA"
→ Go to **05-core-concepts.md** § EMA Approach

### "I need to change thresholds or configuration"
→ Go to **08-configuration.md**

### "I want to see the system visually"
→ Go to **09-diagrams.md**

---

## ✅ Learning Checkpoints

After completing each level, you should be able to answer:

### After Level 1-2 (Introduction + Quick Start)
- [ ] What problem does this module solve?
- [ ] Can I run the module and see it working?

### After Level 3-4 (Architecture + Data Flow)
- [ ] What are the main components?
- [ ] How does a message flow from input to output?

### After Level 5 (Core Concepts)
- [ ] What is EMA and why do we use it?
- [ ] What are Short-Term, Mid-Term, and Long-Term states?
- [ ] How does Significance Score (SS) classify incidents?

### After Level 6-7 (Module + API Reference)
- [ ] What does each Python file do?
- [ ] How do I call the main functions?

### After Level 8 (Configuration)
- [ ] How do I set up the environment?
- [ ] What parameters can I tune?

---

## 📖 Additional Resources

- **Source Code**: The Python files in the parent directory
- **Tests**: `test_orchestrator.py`, `auto_test.py`, `test_ema.py`
- **Original Design Docs**: `architecture.md`, `EMA_approach.md`, `state_management.md`, `user_flow.md` (in parent directory)

---

**Happy Reading! 🎉**

*If you have questions, check if the answer is in the docs first. If not, that's a gap we should fill!*
