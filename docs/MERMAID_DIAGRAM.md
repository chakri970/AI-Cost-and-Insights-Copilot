```mermaid
flowchart TD
  CSV[CSV/JSON billing] --> ETL[ETL: ingest & QC]
  ETL --> DB[(SQLite)]
  DB --> CHUNKER[Chunker + Metadata]
  CHUNKER --> EMBEDS[Gemini Embeddings]
  EMBEDS --> FAISS[FAISS Vector Store]
  UI[Streamlit UI] -->|Query| API[FastAPI]
  API --> FAISS
  API --> DB
  API --> Gemini[Gemini Generate]
  Gemini --> API
  API --> UI
