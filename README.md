# AI Cost & Insights Copilot

A small AI-native analytics app that ingests cloud spend data, computes KPIs, and answers natural-language questions with actionable recommendations.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Setup & Running](#setup--running)
4. [Usage](#usage)
5. [Testing & Evaluation](#testing--evaluation)
6. [Decisions & Trade-offs](#decisions--trade-offs)
7. [Future Work](#future-work)

---

## Project Overview
As a FinOps analyst, this tool allows you to:

- Ingest monthly cloud usage & cost data
- Compute KPIs and detect anomalies
- Ask questions in plain English (e.g., “Why did Azure spend jump 22% in May?”)
- Receive grounded answers with sources, charts, and 1–3 specific next steps

---

## Architecture
- **Data Layer:** SQLite with `billing` and `resources` tables
- **ETL & KPI Layer:** CSV ingestion, quality checks, KPI computation
- **AI Layer (RAG Q&A):** FAISS vector store, embeddings via `SentenceTransformer`, system/few-shot prompting
- **Service Layer:** FastAPI API endpoints (`/kpi`, `/ask`) + minimal Streamlit
- **Recommendations:** Idle/underutilized resources, cost spikes, tagging gaps

CSV/JSON → ETL → DB → KPIs → Vector Store → Retriever → LLM → API/UI


---

## Setup & Running

**Requirements:**
- Python 3.10+
- Docker & Docker Compose
- Virtualenv (optional)

**Steps:**
1. Clone repo
```bash
git clone <repo-url>
cd finops_copilot
```
2.Create virtual environment & install dependencies
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```
3.Copy .env.example to .env and set secrets/keys if needed

4.Run with Docker Compose
```bash
docker-compose up --build
```
5.Access UI & API

Streamlit UI: http://localhost:8501

API endpoints:

`/kpi?month=YYYY-MM`

`/ask POST JSON { "question": "<your question>" \}`

---
##Usage

Example Questions:

"Show total spend for April by service and resource group"

"Which resources look idle, and how much could we save?"



Example API call:
```bash
curl -X POST http://localhost:8000/ask \
-H "Content-Type: application/json" \
-d '{"question": "Show me cost by Bob for April"}'
```
---
##Testing & Evaluation

Run all unit tests:
```bash
pytest tests/
```
- ETL, KPI, retriever, and API tested

- Evaluation metrics:

- Retrieval Recall@k (top-3)

- Answer quality: subjective rubric 1–5

---
## Decisions & Trade-offs

- SQLite chosen for simplicity, not massive scalability

- FAISS chosen for fast local vector search

- Few-shot prompting keeps LLM usage lightweight

- Recommendations are heuristic-based for explainability
---
### Future Work

- Add caching for repeated queries

- Role-based access (viewer/admin)

- Budget threshold alerts & notifications

- Full CI/CD integration (GitHub Actions)

- Slack/Teams integration for /ask commands

---
# CONTACT
- chakrifavofvd@gmail.com
