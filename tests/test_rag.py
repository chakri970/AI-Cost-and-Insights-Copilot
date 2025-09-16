import os
import pytest
import json
from api.app.rag import Retriever, sync_db_to_vectors, get_cost_by_owner
from api.app.etl import SessionLocal, generate_sample, init_db, load_csv_to_db, load_resources_to_db
import pandas as pd

@pytest.fixture(scope="module")
def setup_db(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("data")
    billing_csv = tmp_path / "sample_billing.csv"
    generate_sample(str(billing_csv), months=2, rows_per_month=5)
    init_db()
    load_csv_to_db(str(billing_csv))

    # Resources
    df = pd.read_csv(billing_csv)
    df_resources = df[['resource_id', 'tags_json']].drop_duplicates().copy()
    df_resources['owner'] = df_resources['tags_json'].apply(lambda x: json.loads(x).get('owner', 'unknown'))
    df_resources['env'] = 'dev'
    resources_csv = tmp_path / "sample_resources.csv"
    df_resources.to_csv(resources_csv, index=False)
    load_resources_to_db(str(resources_csv))

    return tmp_path

@pytest.mark.parametrize("top_k", [1,3,5])
def test_retriever_query(tmp_path_factory, top_k):
    tmp_path = tmp_path_factory.mktemp("vector")
    vect_path = tmp_path / "vector_store.index"
    docs_path = str(vect_path) + ".pkl"

    retriever = Retriever(index_path=str(vect_path))
    results = retriever.query("Show top Azure costs", top_k=top_k)

    assert isinstance(results, list)
    if results and isinstance(results[0], dict):
        assert all('text' in r and 'source' in r for r in results)
    else:
        assert all(isinstance(r, str) for r in results)

@pytest.mark.usefixtures("setup_db")
def test_sync_db_to_vectors(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("vector")
    vect_path = tmp_path / "vector_store.index"
    docs_path = str(vect_path) + ".pkl"

    from api.app import rag
    rag.VECTOR_INDEX_PATH = str(vect_path)
    rag.DOCS_PICKLE_PATH = docs_path

    sync_db_to_vectors()

    assert os.path.exists(vect_path)
    assert os.path.exists(docs_path)

    retriever = rag.Retriever(index_path=str(vect_path))
    results = retriever.query("Compute cost")
    assert isinstance(results, list)
    assert all('text' in r and 'source' in r for r in results)

@pytest.mark.usefixtures("setup_db")
def test_get_cost_by_owner():
    month = "2025-04"
    data = get_cost_by_owner(month)
    assert isinstance(data, list)
    assert all(isinstance(t, tuple) and len(t) == 2 for t in data)
    for owner, total in data:
        assert isinstance(owner, str)
        assert isinstance(total, (float, int))
