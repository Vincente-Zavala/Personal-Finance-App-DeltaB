```mermaid
graph TB
    %% Node Definitions
    User((User))
    GA[GitHub Actions]
    TF[Terraform]
    Repo[(GitHub Repo)]
    
    subgraph "Local Environment"
        K8s_Local[K8s: Local Cluster]
        Docker[Docker Compose / setup.sh]
    end

    subgraph "Managed Cloud (Render)"
        Staging[Render: Staging]
        Prod[Render: Production]
    end

    SDB[(Supabase: Staging DB)]
    PDB[(Supabase: Prod DB)]
    BS[BetterStack]

    %% Flow
    User -->|HTTPS| Prod
    
    subgraph "CI/CD & Provisioning"
        GA -->|1. Test & Lint| Repo
        Repo -->|2. Build & Deploy| Staging
        Repo -->|2. Build & Deploy| Prod
        GA -.->|Trigger Hook| Staging
        TF -->|Provision & Config| Staging
        TF -->|Provision & Config| Prod
    end

    subgraph "Data & Monitoring"
        Staging <--> SDB
        Prod <--> PDB
        Prod -->|Structured Logs| BS
        K8s_Local -.->|Local Testing| SDB
        Docker -.->|Local Dev| SDB
    end

    %% Unified Professional Styling
    classDef automation fill:#f0f7ff,stroke:#005cc5,stroke-width:2px,color:#005cc5;
    classDef app fill:#f6f8fa,stroke:#24292e,stroke-width:2px,color:#24292e;
    classDef storage fill:#e6ffed,stroke:#22863a,stroke-width:2px,color:#22863a;
    classDef monitoring fill:#f1f8ff,stroke:#0366d6,stroke-width:2px,color:#0366d6;
    classDef local fill:#ffffff,stroke:#6a737d,stroke-width:1.5px,color:#6a737d,stroke-dasharray: 5 5;
    
    %% Neutralize line text and connector color
    linkStyle default color:#444,stroke:#d1d5da,stroke-width:1px;

    class GA,TF automation;
    class Staging,Prod app;
    class SDB,PDB,Repo storage;
    class BS monitoring;
    class K8s_Local,Docker local;