```mermaid
graph TB
    %% Node Definitions
    User((User))
    GA[GitHub Actions]
    Secrets[Render Secrets]
    Staging[Django: Staging]
    Prod[Django: Production]
    SDB[(Supabase: Staging DB)]
    PDB[(Supabase: Prod DB)]
    BS[BetterStack]
    Backup{{Cloud Backup}}

    %% Flow
    User -->|HTTPS| Prod
    
    subgraph "CI/CD & Config"
        GA -->|1. Test & Lint| GA
        GA -->|2. Deploy| Staging
        GA -->|3. Promote| Prod
        Secrets -.->|Inject Env| Staging
        Secrets -.->|Inject Env| Prod
    end

    subgraph "Staging Environment"
        Staging <--> SDB
    end

    subgraph "Production Environment"
        Prod <--> PDB
        Prod -->|Structured Logs| BS
        PDB -->|Weekly| Backup
    end

    %% Professional Styling Classes
    classDef automation fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#01579b;
    classDef app fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#4a148c;
    classDef storage fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#1b5e20;
    classDef monitoring fill:#fff8e1,stroke:#ff6f00,stroke-width:2px,color:#ff6f00;
    classDef config fill:#eceff1,stroke:#37474f,stroke-width:1px,color:#37474f,stroke-dasharray: 5 5;

    class GA automation;
    class Staging,Prod app;
    class SDB,PDB,Backup storage;
    class BS monitoring;
    class Secrets config;