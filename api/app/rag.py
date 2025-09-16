import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from .utils import dummy_retrieve, logger
import pandas as pd
from sqlalchemy import func, text as sql_text

# DB imports
from .etl import SessionLocal, Billing, Resource  # Use engine-bound session
from .models import Billing, Resource
from .db import get_billing_rows, get_resource_rows


# Vector store paths (outside api folder)

VECTOR_INDEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "vector_store.index",
)
DOCS_PICKLE_PATH = VECTOR_INDEX_PATH + ".pkl"


# Retriever class


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
        D, I = self.index.search(np.array(q_emb, dtype="float32"), top_k)
        return [self.docs[i] for i in I[0] if i < len(self.docs)]


# Instantiate retriever

retriever = Retriever()


# DB → Vector sync


def sync_db_to_vectors():
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    docs = []

    # --- Billing + Resources joined ---
    db = SessionLocal()
    try:
        rows = (
            db.execute(
                sql_text(
                    """
            SELECT b.invoice_month, b.account_id, b.subscription, b.service,
                   b.resource_group, b.resource_id, b.region,
                   b.usage_qty, b.unit_cost, b.cost,
                   r.owner, r.env, r.tags_json
            FROM billing b
            LEFT JOIN resources r
              ON b.resource_id = r.resource_id
        """
                )
            )
            .mappings()
            .all()
        )
    finally:
        db.close()

    for row in rows:
        text = (
            f"Invoice Month: {row['invoice_month']}, "
            f"Account: {row['account_id']}, Subscription: {row['subscription']}, "
            f"Service: {row['service']}, Resource Group: {row['resource_group']}, "
            f"Resource ID: {row['resource_id']}, Region: {row['region']}, "
            f"Usage Qty: {row['usage_qty']}, Unit Cost: {row['unit_cost']}, "
            f"Cost: {row['cost']}, "
            f"Owner: {row.get('owner', 'N/A')}, "
            f"Environment: {row.get('env', 'N/A')}, "
            f"Tags: {row.get('tags_json', '{}')}"
        )
        docs.append({"text": text, "source": "billing+resources"})

    # --- Create embeddings ---
    embeddings = embed_model.encode([d["text"] for d in docs])

    # --- Build FAISS index ---
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # --- Save index + docs ---
    faiss.write_index(index, VECTOR_INDEX_PATH)
    with open(DOCS_PICKLE_PATH, "wb") as f:
        pickle.dump(docs, f)

    print(f"✅ Vector store synced with {len(docs)} joined docs.")


def get_cost_by_owner(month: str):
    session = SessionLocal()

    # Fetch unique billing entries per resource per month
    results = (
        session.query(Resource.owner, func.sum(Billing.cost).label("total_cost"))
        .join(Resource, Resource.resource_id == Billing.resource_id)
        .filter(Billing.invoice_month.like(f"{month}%"))
        .group_by(Resource.owner)
        .distinct(
            Billing.invoice_month,
            Billing.account_id,
            Billing.subscription,
            Billing.service,
            Billing.resource_group,
            Billing.resource_id,
            Billing.region,
            Billing.usage_qty,
            Billing.unit_cost,
            Billing.cost,
        )
        .all()
    )

    session.close()

    return [(owner if owner else "unknown", total) for owner, total in results]
