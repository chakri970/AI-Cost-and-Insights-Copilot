from typing import List, Dict


class Retriever:
    def __init__(self):
        # PH:in real RAG you load FAISS here
        self.docs = [
            {
                "text": "FinOps tip: Review idle resources every month.",
                "source": "finops_tips.md",
            },
            {
                "text": "Azure cost spikes often come from storage or compute scaling.",
                "source": "finops_tips.md",
            },
        ]

    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        # just return first k docs
        return self.docs[:k]
