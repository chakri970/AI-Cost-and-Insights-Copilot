"""FAISS-based vector store wrappers using sentence-transformers."""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle

# Model dims vary — all-MiniLM-L6-v2 -> 384-dim
EMB_MODEL = "all-MiniLM-L6-v2"
DIM = 384


class FaissStore:
    def __init__(self, dim=DIM, index_path="./infra/faiss_data/index.faiss"):
        self.model = SentenceTransformer(EMB_MODEL)
        self.dim = dim
        self.index_path = index_path
        os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            meta_path = index_path + ".meta"
            if os.path.exists(meta_path):
                with open(meta_path, "rb") as fh:
                    self.metadata = pickle.load(fh)
            else:
                self.metadata = []
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.metadata = []

    def add_texts(self, texts, metadatas):
        embs = self.model.encode(texts, show_progress_bar=False)
        embs = np.array(embs).astype("float32")
        self.index.add(embs)
        self.metadata.extend(metadatas)
        self._persist()

    def search(self, query, top_k=5):
        q_emb = self.model.encode([query]).astype("float32")
        D, I = self.index.search(q_emb, top_k)
        results = []
        for idx in I[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results

    def _persist(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path + ".meta", "wb") as fh:
            pickle.dump(self.metadata, fh)
