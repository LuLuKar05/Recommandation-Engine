graph TD
    %% Entities
    User[User / Admin]

    %% Processes
    P1[1.0 Manage Data\n(Load, Add, Purchase, Save)]
    P2[2.0 Calculate Similarity\n(Jaccard Algorithm)]
    P3[3.0 Generate Recommendations\n(Filter & Rank)]

    %% Data Stores
    DS1[(Book DataStore\nbooks.json)]
    DS2[(User DataStore\nusers.json)]

    %% Data Flows
    User -->|1. New Data / Purchase Action| P1
    P1 -->|2. Write Data| DS1
    P1 -->|3. Write Data| DS2
    DS1 -->|4. Read Book Data| P1
    DS2 -->|5. Read User History| P1

    User -->|6. Request Recommendation\n(Target User ID)| P3
    P3 -->|7. Trigger Calculation| P2
    DS2 -->|8. Read All User Histories| P2
    P2 -->|9. Return Similarity Scores| P3
    DS1 -->|10. Read Book Titles/Genre| P3
    P3 -->|11. Final Recommended List| User

    %% Styling
    classDef process fill:#E2F0CB,stroke:#8EBC00,stroke-width:2px;
    classDef store fill:#FFDDC1,stroke:#D35400,stroke-width:2px;
    classDef entity fill:#C1E1FF,stroke:#0074D9,stroke-width:2px;

    class P1,P2,P3 process;
    class DS1,DS2 store;
    class User entity;