
```mermaid
graph TD
    A["💬 simple_chat.py<br/>User Input"] --> B[" orchestrator<br/>process_user_message"]
    
    B --> C[" _detect_emotions"]
    B --> D[" _extract_temporal"]
    
    C --> E[" Emotions<br/>Dict"]
    D --> F["⏱ Temporal<br/>Dict"]
    
    E --> G[" _calculate_and<br/>_apply_impact"]
    F --> G
    
    G --> H[" Impact<br/>Calculation"]
    
    H --> I[" state_updates<br/>Dict"]
    
    I --> J[" _update_user<br/>_profile"]
    
    J --> K["update_short_term"]
    J --> L[" update_mid_term"]
    J --> M[" update_long_term"]
    
    K --> N["Profile<br/>Updated"]
    L --> N
    M --> N
    
    B --> O["add_message_to<br/>_history"]
    
    O --> P[" History<br/>Updated"]
    
    N --> Q[" IncidentAnalysis<br/>Returned"]
    P --> Q
    
    Q --> R[" Generate<br/>Response"]
    
    R --> S[" Display to<br/>User"]
    ```