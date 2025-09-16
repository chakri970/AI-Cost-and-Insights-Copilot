"""
ETL: loads billing.csv and resources.csv into SQLite (SQLAlchemy).
Includes sample data generator and quality checks.

Usage:
  python etl.py --generate-sample
  python etl.py --load ./data/billing.csv
  python etl.py --load-resources ./data/resources.csv
"""

import argparse
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import json
import os
from .models import Base, Billing, Resource

DB_PATH = r"D:\finops_copilot\data\finops.db"  # absolute path
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Example tables
from sqlalchemy import Column, Integer, String, Float, Date


# Init


def init_db():
    os.makedirs("./data", exist_ok=True)
    Base.metadata.create_all(engine)


# Billing loader


def load_csv_to_db(csv_path: str):
    df = pd.read_csv(csv_path)

    # fill some defaults
    df = df.fillna(
        {
            "usage_qty": 0.0,
            "unit_cost": 0.0,
            "cost": 0.0,
            "resource_group": "unknown",
            "service": "unknown",
        }
    )

    # quality checks
    checks = []
    if df["resource_id"].isnull().any():
        checks.append("null_resource_id")
    if (df["cost"] < 0).any():
        checks.append("negative_cost")
    if df["resource_id"].duplicated().sum() > 0:
        checks.append("duplicate_resource_ids")

    session = SessionLocal()
    for _, r in df.iterrows():
        b = Billing(
            invoice_month=str(r["invoice_month"]),
            account_id=str(r.get("account_id", "")),
            subscription=str(r.get("subscription", "")),
            service=str(r.get("service", "")),
            resource_group=str(r.get("resource_group", "")),
            resource_id=str(r.get("resource_id", "")),
            region=str(r.get("region", "")),
            usage_qty=float(r.get("usage_qty", 0.0)),
            unit_cost=float(r.get("unit_cost", 0.0)),
            cost=float(r.get("cost", 0.0)),
        )
        session.add(b)
    session.commit()
    session.close()
    return checks


# Resources loader


def load_resources_to_db(csv_path: str):
    df = pd.read_csv(csv_path)

    session = SessionLocal()
    for _, r in df.iterrows():
        res = Resource(
            resource_id=str(r.get("resource_id", "")),
            owner=str(r.get("owner", "")),
            env=str(r.get("env", "")),
            tags_json=str(r.get("tags_json", "{}")),
        )
        session.merge(res)  # upsert
    session.commit()
    session.close()

    return f"Inserted/updated {len(df)} resources"


# Sample generator (billing only)


def generate_sample(
    path: str = "./data/sample_billing.csv", months: int = 6, rows_per_month: int = 200
):
    import random, csv

    services = ["Compute", "Storage", "DB", "Networking", "AI", "Analytics"]
    regions = ["eastus", "westus", "centralindia"]
    owners = ["alice", "bob", "carol", None]

    rows = []
    base = pd.Timestamp.today()
    for m in range(months):
        month_dt = base - pd.DateOffset(months=(months - 1 - m))
        month_str = month_dt.strftime("%Y-%m")
        for i in range(rows_per_month):
            service = random.choice(services)
            rg = random.choice(["rg-prod", "rg-dev", "rg-test", "rg-unknown"])
            resource_id = f"res-{service[:3].lower()}-{m}-{i}"
            usage = round(random.random() * 100, 3)
            unit_cost = round(random.random() * 2.5, 3)
            cost = round(usage * unit_cost, 3)
            owner = random.choice(owners)
            tags = {"owner": owner} if owner else {}
            rows.append(
                [
                    month_str,
                    "acct-1",
                    "sub-1",
                    service,
                    rg,
                    resource_id,
                    random.choice(regions),
                    usage,
                    unit_cost,
                    cost,
                    json.dumps(tags),
                ]
            )
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "invoice_month",
                "account_id",
                "subscription",
                "service",
                "resource_group",
                "resource_id",
                "region",
                "usage_qty",
                "unit_cost",
                "cost",
                "tags_json",
            ]
        )
        w.writerows(rows)
    print("sample generated:", path)


# ------------------------
# CLI
# ------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-sample", action="store_true")
    parser.add_argument("--path", type=str, default="./data/sample_billing.csv")
    parser.add_argument("--load", type=str, default=None, help="Load billing CSV")
    parser.add_argument(
        "--load-resources", type=str, default=None, help="Load resources CSV"
    )
    args = parser.parse_args()

    init_db()

    if args.generate_sample:
        generate_sample(args.path)

    if args.load:
        checks = load_csv_to_db(args.load)
        print("Billing quality checks:", checks)

    if args.load_resources:
        msg = load_resources_to_db(args.load_resources)
        print("Resources load:", msg)
