from api.app.vector_store import FaissStore
from api.app.retriever import Retriever
from api.app.etl import init_db, generate_sample, load_csv_to_db
from pathlib import Path

def test_retrieve_stub():
    retriever = Retriever()

    # Test default k=3
    results = retriever.retrieve("any query")
    assert isinstance(results, list), "Results should be a list"
    assert len(results) <= 3, "Results should not exceed default k=3"
    for doc in results:
        assert isinstance(doc, dict), "Each result should be a dict"
        assert "text" in doc, "'text' key missing in result"
        assert "source" in doc, "'source' key missing in result"

    # Test custom k
    results_k1 = retriever.retrieve("any query", k=1)
    assert len(results_k1) == 1, "Should return exactly 1 result when k=1"
    assert results_k1[0]["text"] == "FinOps tip: Review idle resources every month."