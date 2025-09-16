import os
from pathlib import Path
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker


# Absolute path to finops.db

BASE_DIR = Path(__file__).resolve().parents[2]  # go 3 levels up

DB_PATH = BASE_DIR / "data" / "finops.db"

# Ensure path is absolute
DB_PATH = DB_PATH.resolve()

DATABASE_URL = f"sqlite:///{DB_PATH}"
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

#  Check file existence before creating engine
if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found at: {DB_PATH}")

DATABASE_URL = f"sqlite:///{DB_PATH}"
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
metadata = MetaData()


# Query helpers


def get_billing_rows():
    db = SessionLocal()
    try:
        rows = (
            db.execute(
                text(
                    """
            SELECT invoice_month, account_id, subscription, service, 
                resource_group, resource_id, region, usage_qty, 
                unit_cost, cost
            FROM billing
        """
                )
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
    finally:
        db.close()


def get_resource_rows():
    db = SessionLocal()
    try:
        rows = (
            db.execute(
                text(
                    """
            SELECT resource_id, owner, env, tags_json
            FROM resources
        """
                )
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
    finally:
        db.close()
