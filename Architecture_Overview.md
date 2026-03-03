```mermaid
graph TD
    User([User]) -->|HTTPS| Render[Render: Django]
    Render -->|SQL| Supabase[(Supabase: Postgres)]
    Render -->|Logs| BetterStack[Better Stack]
    
    subgraph Automation
        GA[GitHub Actions] -.->|Deploy| Render
    end

    style Render fill:#f9f,stroke:#333,stroke-width:2px
    style Supabase fill:#bbf,stroke:#333
    style BetterStack fill:#dfd,stroke:#333
