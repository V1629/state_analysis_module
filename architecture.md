# AI Companion System Architecture

This document contains diagrams describing the system components and data flow.

## Components
- Data Layer (SQLite + Encryption)
- Analysis Layer (behavioral + semantic)
- Intent Recognition Layer (phrase graphs + distributions)
- Response Generation Layer (strategy + templates)
- Learning Layer (updates + pruning)
- Utilities (embeddings, personality NN, crypto)

## Architecture Diagram
```mermaid
flowchart LR
  A[User Input] --> B[Analysis Layer]
  B --> C[Contextual Embedding]
  B --> D[Behavioral Features]
  C --> E[Intent Recognition]
  D --> E
  E --> F[Response Generation]
  F --> G[Output to User]
  E --> H[Learning Layer]
  F --> H
  H --> I[Data Layer]
  I --> C
  I --> B
  style I fill:#f9f,stroke:#333,stroke-width:1px
```

## Sequence Diagram (Interaction Cycle)
```mermaid
sequenceDiagram
  participant U as User
  participant A as Analysis
  participant I as Intent
  participant R as Response
  participant L as Learning
  participant D as Data
  U->>A: send(message, typing_info)
  A->>D: fetch(relevant_history)
  A->>I: build_contextual_embedding
  I->>D: query_phrase_mappings
  I->>R: intent + urgency
  R->>U: render_response
  U->>D: followup stored
  R->>L: outcome signals
  L->>D: update models
```

## State Diagram (User Understanding Evolution)
```mermaid
stateDiagram-v2
  [*] --> NewProfile
  NewProfile --> ActiveLearning
  ActiveLearning --> StableProfile : sufficient data
  StableProfile --> Adaptation : drift detected
  Adaptation --> StableProfile : model updated
  StableProfile --> [*]
```

## Entity-Relationship Diagram (Storage)
```mermaid
erDiagram
    USERS ||--o{ INTERACTIONS : "has"
    USERS ||--o{ PHRASE_MAP : "owns"
    USERS ||--o{ PERSONALITY_MODEL : "holds"

    INTERACTIONS {
        INTEGER id PK
        TEXT user_id FK
        DATETIME ts
        BLOB message_encrypted
        BLOB embedding
        TEXT behavioral_json
    }

    PHRASE_MAP {
        TEXT user_id FK
        TEXT phrase PK
        REAL weight
        TEXT contexts_json
    }

    PERSONALITY_MODEL {
        TEXT user_id FK
        BLOB model_blob
        DATETIME updated_at
    }
```