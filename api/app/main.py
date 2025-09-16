import os
import calendar
from .utils import logger
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
import logging
import streamlit as st
import re
from .etl import SessionLocal
from sqlalchemy import func

from .models import Billing, Resource
from .kpi import get_cost_by_owner, monthly_trend, top_service_expenditures


# For vector store
import faiss
import pickle
from sentence_transformers import SentenceTransformer

from .rag import retriever, sync_db_to_vectors, get_cost_by_owner

# sync_db_to_vectors()

# Load environment variables

load_dotenv()


# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Init FastAPI

app = FastAPI(title="FinOps Copilot with Groq")


####cost by owner endpoint


@app.get("/cost_by_owner")
def cost_by_owner(month: str):
    """
    Returns actual cost by owner for a given month (YYYY-MM)
    """
    data = get_cost_by_owner(month)
    return {"month": month, "data": data}


# Sync DB → vectors on startup


@app.on_event("startup")
def startup_event():
    try:
        logger.info("Syncing DB to vector store on startup...")
        sync_db_to_vectors()
        logger.info("Vector store ready.")
    except Exception as e:
        logger.exception("Failed to sync vector store, using fallback retriever.")


# Init Groq client

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise RuntimeError("⚠️ Missing GROQ_API_KEY in .env")

client = Groq(api_key=groq_api_key)


# Prompt-injection sanitizer


def sanitize_user_input(s: str) -> str:
    banned = ["SYSTEM:", "Assistant:", "<!--", "```", "eval(", "os.", "import "]
    out = s
    for b in banned:
        out = out.replace(b, "")
    if len(out) > 2000:
        out = out[:2000]
    return out


# Request schema


class AskRequest(BaseModel):
    question: str


def parse_month_year(question: str):
    """
    Extract month from question. Returns YYYY-MM format.
    Defaults to current year if not found.
    """
    month, year = None, None
    for i, m in enumerate(calendar.month_name):
        if m.lower() in question.lower():
            month = i
            break
    y_match = re.search(r"20\d{2}", question)
    year = int(y_match.group(0)) if y_match else 2025
    if month:
        return f"{year}-{month:02d}"
    return None


def parse_owner(question: str):
    """
    Extract owner from question. Returns lowercase to match DB.
    """
    m = re.search(r"by (\w+)", question.lower())
    return m.group(1) if m else None


def parse_top_n_service(question: str):
    word_to_num = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    tokens = question.lower().split()
    n = next((int(t) for t in tokens if t.isdigit()), None)
    if not n:
        n = next((word_to_num[t] for t in tokens if t in word_to_num), None)
    return n


def get_cost_by_owner_for_owner(month: str, owner: str):
    """
    Fetch total cost for a specific owner and month.
    Returns list of dicts.
    """
    session = SessionLocal()
    try:
        results = (
            session.query(Resource.owner, func.sum(Billing.cost).label("total_cost"))
            .join(Billing, Billing.resource_id == Resource.resource_id)
            .filter(Resource.owner.ilike(f"%{owner}%"))
            .filter(Billing.invoice_month.like(f"{month}%"))
            .group_by(Resource.owner)
            .all()
        )
        return [
            {"Owner": o if o else "unknown", "Cost": float(total)}
            for o, total in results
        ]
    finally:
        session.close()


def get_highest_paid_owner(month: str):
    """
    Returns owner with highest total cost for a given month
    """
    session = SessionLocal()
    try:
        result = (
            session.query(Resource.owner, func.sum(Billing.cost).label("total_cost"))
            .join(Billing, Resource.resource_id == Billing.resource_id)
            .filter(Billing.invoice_month.like(f"{month}%"))
            .group_by(Resource.owner)
            .order_by(func.sum(Billing.cost).desc())
            .first()
        )
        if result:
            owner, total = result
            return {"Owner": owner if owner else "unknown", "Cost": float(total)}
        return None
    finally:
        session.close()


def get_most_used_service(owner: str = None, month: str = None):
    """
    Returns service with highest usage (cost) optionally filtered by owner/month
    """
    session = SessionLocal()
    try:
        query = session.query(
            Billing.service, func.sum(Billing.cost).label("total_cost")
        ).join(Resource, Resource.resource_id == Billing.resource_id)

        if owner:
            query = query.filter(Resource.owner.ilike(f"%{owner}%"))
        if month:
            query = query.filter(Billing.invoice_month.like(f"{month}%"))

        query = query.group_by(Billing.service).order_by(func.sum(Billing.cost).desc())
        result = query.first()
        if result:
            service, total = result
            return {"Service": service, "Cost": float(total)}
        return None
    finally:
        session.close()


@app.get("/kpi")
def kpi(month: str):
    data = get_cost_by_owner(month)
    return {"month": month, "cost_by_owner": data}


@app.get("/monthly_trend")
def monthly_trend_api(owner: str):
    data = monthly_trend(owner)
    return {"owner": owner, "monthly_trend": data}


# Dummy retriever (replace with vector store later)


def dummy_retrieve(query: str, k: int = 5):
    return [
        {
            "source": "finops_tips.md",
            "text": "Monitor Azure cost anomalies using Cost Explorer.",
        },
        {
            "source": "finops_tips.md",
            "text": "May often has spikes due to fiscal year-end workloads.",
        },
        {
            "source": "finops_tips.md",
            "text": "Always tag resources properly to track cost allocation.",
        },
    ]


# Vector store retriever

VECTOR_INDEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data/vector_store.index",
)  # outside api folder

DOCS_PICKLE_PATH = VECTOR_INDEX_PATH + ".pkl"


class Retriever:
    def __init__(self, index_path=VECTOR_INDEX_PATH):
        self.index = None
        self.docs = []
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        if os.path.exists(index_path) and os.path.exists(DOCS_PICKLE_PATH):
            self.index = faiss.read_index(index_path)
            with open(DOCS_PICKLE_PATH, "rb") as f:
                self.docs = pickle.load(f)
            logger.info("✅ Vector store loaded successfully.")
        else:
            logger.warning("⚠️ Vector store not found. Using dummy retriever.")

    def query(self, query: str, top_k=5):
        if self.index is None:
            return dummy_retrieve(query, k=top_k)
        q_emb = self.embed_model.encode([query])
        D, I = self.index.search(q_emb, top_k)
        return [self.docs[i] for i in I[0] if i < len(self.docs)]


retriever = Retriever()


# Dummy retriever fallback


def dummy_retrieve(query: str, k: int = 5):
    return [
        {
            "source": "finops_tips.md",
            "text": "Monitor Azure cost anomalies using Cost Explorer.",
        },
        {
            "source": "finops_tips.md",
            "text": "May often has spikes due to fiscal year-end workloads.",
        },
        {
            "source": "finops_tips.md",
            "text": "Always tag resources properly to track cost allocation.",
        },
    ]


# ------------------------
# /ask endpoint
# ------------------------
@app.post("/ask")
async def ask(req: AskRequest):
    question = sanitize_user_input(req.question)

    # Step 1: Retrieve context from FAISS

    relevant_docs = retriever.query(question, top_k=10)
    context_texts = "\n".join([d["text"] for d in relevant_docs])
    sources = [d["source"] for d in relevant_docs]

    # Step 2: Parse structured info

    table_data, trend_data, top_service_data = None, None, None
    month = parse_month_year(question)
    owner = parse_owner(question)
    top_n = parse_top_n_service(question)

    # Step 3: Structured KPI enrichments

    # Cost by owner → filter by owner and month if available
    if "cost by owner" in question.lower():
        if owner and month:
            table_data = get_cost_by_owner_for_owner(month, owner)
        elif month:
            table_data = get_cost_by_owner(month)

    # Monthly trend → detect "trend for <owner>"
    if "trend" in question.lower() and owner:
        trend_data = monthly_trend(owner)

    if "highest paid" in question.lower() and month:
        table_data = get_highest_paid_owner(month)

    if "mostly taken service" in question.lower():
        top_service_data = get_most_used_service(owner=owner, month=month)

    # Top-N services → detect number + service keyword
    if "top" in question.lower() and top_n:
        m = re.search(r"in\s+(\w+)", question.lower())
        service_keyword = m.group(1) if m else None
        if service_keyword:
            rows = top_service_expenditures(service_keyword, top_n)
            if rows:
                top_service_data = "\n".join(
                    [
                        f"{i+1}. Service={r[0]}, Resource={r[1]}, Owner={r[2] or 'unknown'}, Cost=${round(r[3],2)}"
                        for i, r in enumerate(rows)
                    ]
                )

    # Step 4: Build LLM prompt

    prompt = f"""
You are a FinOps Copilot with access to billing and resource data.
Answer the user question using the context below. Use aggregated cost insights 
(by owner, service, or month) whenever possible. 

If totals or rankings are requested, compute and summarize them.
If the answer cannot be derived from the context, say "No data found."

Context:
{context_texts}
"""

    if table_data:
        prompt += f"\nCost by Owner Data:\n{table_data}\n"
    if trend_data:
        prompt += f"\nMonthly Trend Data:\n{trend_data}\n"
    if top_service_data:
        prompt += f"\nTop Service Expenditures:\n{top_service_data}\n"

    prompt += f"\nUser Question: {question}\nAnswer:\n"

    # Step 5: Call Groq LLaMA

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful FinOps assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.2,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logging.error(f"Groq LLaMA API failed: {e}")
        answer = "Sorry, I could not generate an answer right now."

    # Step 6: Return full response

    return {
        "answer": answer,
        "sources": sources,
        "table": table_data,
        "trend": trend_data,
        "top_service": top_service_data,
        "suggestions": [],
    }


# Health check


@app.get("/health")
async def health():
    return {"status": "ok"}
