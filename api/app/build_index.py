import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Paths (outside api folder)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
os.makedirs(BASE_DIR, exist_ok=True)

VECTOR_INDEX_PATH = os.path.join(BASE_DIR, "vector_store.index")
DOCS_PICKLE_PATH = os.path.join(BASE_DIR, "vector_store.index.pkl")


# Ex docs
docs = [
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


# Create embeddings

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embed_model.encode([d["text"] for d in docs])


# Build FAISS index

d = embeddings.shape[1]
index = faiss.IndexFlatL2(d)
index.add(np.array(embeddings, dtype="float32"))
# Save index and docs pickle

faiss.write_index(index, VECTOR_INDEX_PATH)
with open(DOCS_PICKLE_PATH, "wb") as f:
    pickle.dump(docs, f)

print(f"FAISS index and docs pickle created at:")
print(f"   {VECTOR_INDEX_PATH}")
print(f"   {DOCS_PICKLE_PATH}")
