# 09 — Diagrams

> **Reading time:** 10 minutes (visual reference)  
> **Prerequisites:** [01-introduction.md](./01-introduction.md)  

---

## Overview

This document contains all Mermaid diagrams from the module documentation, consolidated for easy reference.

---

# System Architecture

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Input
        U[User Message]
    end
    
    subgraph "Temporal Extractor"
        TE[temporal_extractor.py]
        TE --> |Extract| TP[Time Phrases]
        TP --> |Categorize| TC[Temporal Category]
    end
    
    subgraph "Emotional Detector"
        ED[emotional_detector.py]
        ED --> |Detect| EM[27 Emotions]
    end
    
    subgraph "Orchestrator"
        O[orchestrator.py]
        O --> |Calculate| IW[Impact Weights]
    end
    
    subgraph "User Profile"
        UP[user_profile.py]
        UP --> |Update| ST[Short-Term State]
        UP --> |Update| MT[Mid-Term State]
        UP --> |Update| LT[Long-Term State]
    end
    
    subgraph "Chat Logger"
        CL[chat_logger.py]
        CL --> |Export| XL[Excel Log]
    end
    
    U --> TE
    U --> ED
    TE --> O
    ED --> O
    O --> UP
    O --> CL
```

---

## Component Interaction

```mermaid
graph TB
    subgraph "External"
        HF[HuggingFace API]
        FS[File System]
    end
    
    subgraph "Core Modules"
        O[orchestrator.py]
        ED[emotional_detector.py]
        TE[temporal_extractor.py]
        UP[user_profile.py]
        CL[chat_logger.py]
    end
    
    O -->|text| ED
    ED -->|API call| HF
    HF -->|emotions| ED
    ED -->|emotions dict| O
    
    O -->|text| TE
    TE -->|temporal info| O
    
    O -->|update request| UP
    UP -->|read/write| FS
    
    O -->|log request| CL
    CL -->|write xlsx| FS
```

---

# Data Flow

## Message Processing Pipeline

```mermaid
flowchart LR
    subgraph Stage1 [Stage 1: Input]
        M[User Message]
    end
    
    subgraph Stage2 [Stage 2: Analysis]
        direction TB
        TE[Temporal Extraction]
        ED[Emotion Detection]
    end
    
    subgraph Stage3 [Stage 3: Calculation]
        IC[Impact Calculation]
    end
    
    subgraph Stage4 [Stage 4: Update]
        direction TB
        ST[Short-Term]
        MT[Mid-Term]
        LT[Long-Term]
    end
    
    subgraph Stage5 [Stage 5: Output]
        direction TB
        PR[Profile Save]
        LOG[Chat Log]
    end
    
    M --> TE & ED
    TE & ED --> IC
    IC --> ST & MT & LT
    ST & MT & LT --> PR & LOG
```

---

## State Update Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant TE as Temporal Extractor
    participant ED as Emotion Detector
    participant UP as User Profile
    participant CL as Chat Logger
    
    U->>O: Send message
    O->>TE: Extract temporal refs
    TE-->>O: TimePhrase[], category
    O->>ED: Classify emotions
    ED-->>O: emotion scores (27)
    O->>O: Calculate impact weights
    O->>UP: Update states
    UP->>UP: Apply EMA
    UP-->>O: Updated states
    O->>CL: Log interaction
    CL-->>O: Log path
    O-->>U: Response with context
```

---

# State Management

## State Activation Flow

```mermaid
stateDiagram-v2
    [*] --> ST_Only: First message
    ST_Only --> ST_MT: 14 days OR 30 messages
    ST_MT --> All_Active: 90 days OR 50 messages
    All_Active --> All_Active: Continues
    
    note right of ST_Only
        Only short-term active
        α = 0.15
    end note
    
    note right of ST_MT
        Short + Mid-term active
        MT uses rolling window
    end note
    
    note right of All_Active
        All three states active
        LT uses α = 0.02
    end note
```

---

## Temporal Category Impact Distribution

```mermaid
graph TB
    subgraph Recent ["Recent (0-30 days)"]
        R_ST[ST: 70%]
        R_MT[MT: 20%]
        R_LT[LT: 10%]
    end
    
    subgraph Medium ["Medium (1-12 months)"]
        M_ST[ST: 30%]
        M_MT[MT: 50%]
        M_LT[LT: 20%]
    end
    
    subgraph Distant ["Distant (1+ years)"]
        D_ST[ST: 5%]
        D_MT[MT: 30%]
        D_LT[LT: 80%]
    end
    
    subgraph Future ["Future"]
        F_ST[ST: 70%]
        F_MT[MT: 40%]
        F_LT[LT: 0%]
    end
```

---

## EMA State Evolution

```mermaid
graph LR
    subgraph "Message Stream"
        M1[Msg 1] --> M2[Msg 2] --> M3[Msg 3] --> M4[Msg N]
    end
    
    subgraph "Short-Term (α=0.15)"
        ST1[State] --> ST2[State'] --> ST3[State''] --> ST4[State''']
    end
    
    subgraph "Long-Term (α=0.02)"
        LT1[State] --> LT2[≈State] --> LT3[≈State] --> LT4[Slowly evolving]
    end
    
    M1 -.-> ST1 & LT1
    M2 -.-> ST2 & LT2
    M3 -.-> ST3 & LT3
    M4 -.-> ST4 & LT4
```

---

# User Interaction

## Complete User Flow

```mermaid
flowchart TB
    Start([User Opens App]) --> Input[User Types Message]
    Input --> Process{Process Message}
    
    Process --> Temporal[Extract Temporal Refs]
    Process --> Emotion[Detect Emotions]
    
    Temporal --> Category{Categorize}
    Category --> |recent| Recent[0-30 days]
    Category --> |medium| Medium[1-12 months]
    Category --> |distant| Distant[1+ years]
    Category --> |future| Future[Future event]
    
    Emotion --> Classify[27 Emotion Scores]
    
    Recent & Medium & Distant & Future --> Impact[Calculate Impact]
    Classify --> Impact
    
    Impact --> UpdateST[Update Short-Term]
    Impact --> UpdateMT[Update Mid-Term]
    Impact --> UpdateLT[Update Long-Term]
    
    UpdateST & UpdateMT & UpdateLT --> Save[Save Profile]
    Save --> Log[Log to Excel]
    Log --> Response([AI Response])
    
    Response --> |User continues| Input
```

---

## Profile Lifecycle

```mermaid
stateDiagram-v2
    [*] --> New: First interaction
    New --> Growing: Regular usage
    Growing --> Mature: 90+ days
    Mature --> Mature: Continued use
    
    state New {
        [*] --> STOnly
        STOnly: Short-term only
    }
    
    state Growing {
        [*] --> ST_MT
        ST_MT: Short + Mid-term
    }
    
    state Mature {
        [*] --> AllStates
        AllStates: All states active
    }
```

---

# Entity Relationships

## Data Model

```mermaid
erDiagram
    USER ||--o{ MESSAGE : sends
    USER ||--|| PROFILE : has
    MESSAGE ||--o{ EMOTION : contains
    MESSAGE ||--o{ TIME_PHRASE : contains
    PROFILE ||--|| ST_STATE : has
    PROFILE ||--|| MT_STATE : has
    PROFILE ||--|| LT_STATE : has
    
    USER {
        string user_id PK
        datetime created_at
    }
    
    MESSAGE {
        string text
        datetime timestamp
        string temporal_category
    }
    
    EMOTION {
        string name
        float score
    }
    
    TIME_PHRASE {
        string original
        string normalized
        int days_ago
    }
    
    PROFILE {
        string user_id PK
        int message_count
        bool mt_activated
        bool lt_activated
    }
    
    ST_STATE {
        float admiration
        float joy
        float sadness
    }
    
    MT_STATE {
        float admiration
        float joy
        float sadness
    }
    
    LT_STATE {
        float admiration
        float joy
        float sadness
    }
```

---

# Algorithm Visualization

## EMA Formula

```mermaid
graph LR
    subgraph "EMA Update"
        New[New Value] --> |× α| Weighted1[Weighted New]
        Old[Old EMA] --> |× 1-α| Weighted2[Weighted Old]
        Weighted1 --> Add((+))
        Weighted2 --> Add
        Add --> Result[New EMA]
    end
    
    subgraph "Example α=0.15"
        N[0.8] --> |× 0.15| W1[0.12]
        O[0.5] --> |× 0.85| W2[0.425]
        W1 --> A((+))
        W2 --> A
        A --> R[0.545]
    end
```

---

## PRISM Scoring

```mermaid
graph TB
    subgraph "PRISM Components"
        P[P: Persistence<br/>0.1-10]
        R[R: Resonance<br/>1-10]
        I[I: Impact<br/>1-5]
        S[S: Severity<br/>0.1-3]
        M[M: Malleability<br/>0.5-2]
    end
    
    P --> Mult1[×]
    R --> Mult1
    Mult1 --> Mult2[×]
    I --> Mult2
    Mult2 --> Mult3[×]
    S --> Mult3
    Mult3 --> Div[÷]
    M --> Div
    Div --> SS[Significance Score]
    
    SS --> |< 15| ST[Short-Term]
    SS --> |15-75| MT[Mid-Term]
    SS --> |≥ 75| LT[Long-Term]
```

---

## Decay Curves

```mermaid
graph TB
    subgraph "Short-Term Decay"
        direction LR
        D0[Day 0: 100%] --> D2[Day 2: 55%] --> D7[Day 7: 12%] --> D14[Day 14: 1.5%]
    end
    
    subgraph "Mid-Term Decay"
        direction LR
        M0[Day 0: 100%] --> M30[Day 30: 80%] --> M60[Day 60: 50%] --> M120[Day 120: 10%]
    end
    
    subgraph "Long-Term"
        direction LR
        L0[Initial] --> L100[Day 100] --> L365[Year 1] --> LN[Never fully decays]
    end
```

---

# File Dependencies

## Import Graph

```mermaid
graph TD
    O[orchestrator.py]
    ED[emotional_detector.py]
    TE[temporal_extractor.py]
    UP[user_profile.py]
    CL[chat_logger.py]
    
    O --> ED
    O --> TE
    O --> UP
    O --> CL
    
    ED --> |requests| REQ[requests]
    ED --> |os| OS[os]
    
    TE --> |re| RE[re]
    TE --> |datetime| DT[datetime]
    
    UP --> |json| JSON[json]
    UP --> |datetime| DT
    UP --> |os| OS
    
    CL --> |openpyxl| OPX[openpyxl]
    CL --> |datetime| DT
```

---

## Directory Structure

```mermaid
graph TD
    Root[project/]
    Root --> Env[.env]
    Root --> Req[requirements.txt]
    Root --> Orch[orchestrator.py]
    Root --> ED[emotional_detector.py]
    Root --> TE[temporal_extractor.py]
    Root --> UP[user_profile.py]
    Root --> CL[chat_logger.py]
    Root --> Profiles[user_profiles/]
    Root --> Docs[docs/]
    
    Profiles --> JSON1[user123.json]
    Profiles --> XLS1[user123_chat_log.xlsx]
    
    Docs --> D1[README.md]
    Docs --> D2[01-introduction.md]
    Docs --> D3[...]
    Docs --> D9[09-diagrams.md]
```

---

# Quick Reference

## All Diagrams Index

| Diagram | Section | Purpose |
|---------|---------|---------|
| High-Level Architecture | [Architecture](#high-level-architecture) | System overview |
| Component Interaction | [Architecture](#component-interaction) | Module connections |
| Message Pipeline | [Data Flow](#message-processing-pipeline) | Processing stages |
| State Update Sequence | [Data Flow](#state-update-flow) | Step-by-step flow |
| State Activation | [State Management](#state-activation-flow) | When states activate |
| Impact Distribution | [State Management](#temporal-category-impact-distribution) | Category → State mapping |
| EMA Evolution | [State Management](#ema-state-evolution) | How states change |
| User Flow | [User Interaction](#complete-user-flow) | End-to-end user journey |
| Profile Lifecycle | [User Interaction](#profile-lifecycle) | Profile maturity |
| Data Model | [Entity Relationships](#data-model) | ER diagram |
| EMA Formula | [Algorithms](#ema-formula) | Math visualization |
| PRISM Scoring | [Algorithms](#prism-scoring) | Score calculation |
| Decay Curves | [Algorithms](#decay-curves) | Time-based decay |
| Import Graph | [Dependencies](#import-graph) | Module imports |
| Directory Structure | [Dependencies](#directory-structure) | File organization |

---

**Navigation:**
| Previous | Current | Home |
|----------|---------|------|
| [08-configuration.md](./08-configuration.md) | 09-diagrams.md | [README.md](./README.md) |
