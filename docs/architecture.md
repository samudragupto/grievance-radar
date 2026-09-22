# Grievance Radar System Architecture

## Overview
Grievance Radar is designed around human-in-the-loop municipal data analytics. The architecture separates citizen data ingestion, statistical anomaly detection, officer verification, and executive briefing into distinct modular services.

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Ingestion["1. Citizen Ingestion & Privacy"]
        A[Public Complaint Feed CSV / JSON] --> B[preprocess.py Anonymization Engine]
        B -->|Redacted Text & Metadata| C[(SQLite / DB)]
    end

    subgraph Analytics["2. Unsupervised NLP & Spike Detection"]
        C --> D[embed.py all-MiniLM-L6-v2]
        D --> E[cluster.py BERTopic / K-Means]
        E --> F[analyze.py Rolling Baseline & Z-Score Engine]
        F --> G{Z >= 2.5 & +50% Surge?}
        G -->|Yes| H[Flagged Findings Pool]
    end

    subgraph HumanLoop["3. Human-in-the-Loop Officer Review"]
        H --> I[Officer Dashboard UI]
        I -->|Officer Decision| J{Action}
        J -->|Confirm / Refine| K[(Confirmed Findings Table)]
        J -->|Dismiss| L[Audit Trail Archive]
    end

    subgraph Publishing["4. Executive Output & Public Transparency"]
        K --> M[brief_generator.py ReportLab Engine]
        M --> N[One-Page Monday Brief PDF]
        C --> O[Public Trends & Leaflet Map Endpoint]
    end
```

## Architectural Boundaries

1. **Privacy Invariant**:
   Raw citizen phone numbers, Aadhaar numbers, and names never reach embedding models or the public trends view. Redaction is enforced in `app/services/preprocess.py` prior to database commit.

2. **Decoupled Fallback Clustering**:
   `cluster.py` leverages BERTopic when PyTorch/huggingface components are resident, but defaults seamlessly to high-speed Scikit-Learn K-Means with dynamic TF-IDF label generation if resources or memory limits are constrained.

3. **Strict Human Gatekeeper**:
   The Monday Brief PDF compilation endpoint (`/api/brief`) strictly filters `status == 'confirmed'`, guaranteeing that no unverified or false-positive statistical spike appears on the final executive brief.
