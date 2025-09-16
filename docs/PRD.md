**Project Name:** AI Cost & Insights Copilot

**Problem Statement:**
FinOps analysts struggle to quickly understand cloud spend, identify anomalies, and take action on cost optimization. Existing dashboards are often static, lack context, and don’t answer natural language questions.

Users:
- FinOps Analysts  
- Cloud Administrators  
- Finance Managers 

Top use-cases:
1. Quickly view cloud spend breakdown by service, resource group, or owner.  
2. Detect cost anomalies or sudden usage spikes.  
3. Identify idle/underutilized resources to optimize costs.  
4. Ask questions in natural language

Success metrics:
- **Functional:** Ability to ingest cloud spend CSV/JSON and compute KPIs.  
- **AI/UX:** RAG-powered Q&A returns accurate answers with relevant sources ≥ 80% Recall@3.  
- **Operational:** System runs locally via Docker, endpoints respond <1s for typical queries.  
- **Business:** At least one actionable recommendation generated per dataset ingestion.

Assumptions & constraints:
- Prototype  SQLite + FAISS acceptable.
- LLM can be OpenAI/gemini/groq or a local model; if no key present, fallback to retrieval-only responses.
- No real cloud keys checked in; .env.example provided.
