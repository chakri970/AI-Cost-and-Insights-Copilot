import os
import pytest
from api.app.etl import generate_sample, init_db, load_csv_to_db, load_resources_to_db, SessionLocal
from api.app.models import Billing, Resource
import pandas as pd
import json

def test_generate_and_load(tmp_path):
    # ------------------------
    # 1️⃣ Generate sample billing CSV
    # ------------------------
    billing_path = tmp_path / "sample_billing.csv"
    generate_sample(str(billing_path), months=2, rows_per_month=5)
    assert os.path.exists(billing_path), "Sample billing CSV not created"

    # ------------------------
    # 2️⃣ Initialize DB
    # ------------------------
    init_db()

    # ------------------------
    # 3️⃣ Load billing CSV into DB
    # ------------------------
    checks = load_csv_to_db(str(billing_path))
    assert isinstance(checks, list), "Load checks should return a list"

    # ------------------------
    # 4️⃣ Validate Billing table
    # ------------------------
    session = SessionLocal()
    try:
        count = session.query(Billing).count()
        assert count > 0, "No rows inserted in Billing table"
        assert session.query(Billing).filter(Billing.cost < 0).count() == 0
    finally:
        session.close()

    # ------------------------
    # 5️⃣ Generate and load Resource CSV
    # ------------------------
    # Extract unique resources from billing CSV
    df = pd.read_csv(billing_path)
    resource_path = tmp_path / "sample_resources.csv"
    df_resources = df[['resource_id', 'tags_json']].drop_duplicates().copy()
    df_resources['owner'] = df_resources['tags_json'].apply(lambda x: json.loads(x).get('owner', 'unknown'))
    df_resources['env'] = 'dev'
    df_resources.to_csv(resource_path, index=False)
    assert os.path.exists(resource_path), "Resource CSV not created"

    # Load resources
    msg = load_resources_to_db(str(resource_path))
    assert "Inserted/updated" in msg

    # Validate Resource table
    session = SessionLocal()
    try:
        count_res = session.query(Resource).count()
        assert count_res > 0, "No rows inserted in Resource table"
    finally:
        session.close()
