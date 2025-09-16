# Technical Design — Summary

Architecture:
- ETL reads CSV -> loads tables (billing, resources) in SQLite.
- Transformations compute KPIs: monthly totals, by service,month trend.
- Embeddings: sentence-transformers -> FAISS index of billing/resources rows + docs (finops_tips.md).
- FastAPI:
  - /kpi?month=YYYY-MM -> returns KPI JSON
  - /ask POST {question} -> performs retrieval, builds prompt with retrieved chunks, calls LLM (if configured), returns answer + sources + suggestions
- UI (Streamlit): KPI view and chat box that calls API.
- Packaging: Dockerfile for API and UI + docker-compose.
- Observability: structured logs via loguru, request id, timer.

- **Data Layer:** 
- Storage: SQLite/Postgres (local)
- billing (id, invoice_month, account_id, subscription, service, resource_group, resource_id, region, usage_qty, unit_cost, cost)
- resources (resource_id, owner, env, tags_json)

- **ETL & KPI Layer:**  
  - CSV/JSON ingestion → DB  
  - Quality checks: nulls, negative costs, duplicates  
  - KPIs: monthly spend by service/resource group, top N cost drivers, 6-month trends  
- **AI Layer (RAG Q&A):**  
  - Retrieval: FAISS/Chroma vector store  
  - Embeddings: `SentenceTransformer`  
  - Prompting: system prompt + few-shot examples  
  - Output: answer text + small chart/table
- **Recommendations:**  
  - Rules: idle resources, unit-cost spikes, missing tags  
  - Output: resource impacted + estimated monthly savings

- **Service Layer:**  
  - API: FastAPI  
    - `/kpi?month=YYYY-MM` → returns KPIs  
    - `/ask` → natural language Q&A with sources + suggestions  
  - Minimal UI: Streamlit web page (chat + KPI dashboard)
  
- **Trade-offs**:
- SQLite chosen for simplicity (fast to set up) vs Postgres (more robust).
- FAISS used for local vector store; production would use managed vector DB.
- groq for LLM integration but code supports running without keys (fallback retrieval-only).

- **Risks & Mitigation:** 
- **Hallucination risk**: mitigate by returning source list + prompt instructions and low temperature.
- **Prompt-injection**: filter user input and do not allow user-supplied system instructions.
- **Data quality:** Use quality checks + validation  
- **Incorrect AI answers:** Include sources + fallback path  
- **Cost estimates inaccuracy:** Heuristic-based recommendations clearly labeled

- **Alternatives Considered:** 
- Replace FAISS with Chroma or Pinecone.
- Replace groq with local Llama-like model (if privacy/price needed).
- PostgreSQL instead of SQLite → more scalable  
- Full LLM answer vs. RAG → RAG ensures grounded responses