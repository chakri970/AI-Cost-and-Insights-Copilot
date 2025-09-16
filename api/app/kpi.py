from sqlalchemy import func, desc
from .etl import SessionLocal
from .models import Billing, Resource
import pandas as pd


def get_cost_by_owner(month: str):
    session = SessionLocal()
    # Aggregate cost per owner after deduplicating per resource
    subquery = (
        session.query(Billing.resource_id, func.min(Billing.cost).label("cost"))
        .filter(Billing.invoice_month.like(f"{month}%"))
        .group_by(Billing.resource_id)
        .subquery()
    )

    results = (
        session.query(Resource.owner, func.sum(subquery.c.cost).label("total_cost"))
        .join(subquery, Resource.resource_id == subquery.c.resource_id)
        .group_by(Resource.owner)
        .all()
    )
    session.close()
    return [(owner if owner else "unknown", total) for owner, total in results]


def monthly_trend(owner: str):
    """
    Returns month-wise cost trend for a given owner
    """
    session = SessionLocal()

    # Example query to get monthly cost trend
    results = (
        session.query(Billing.invoice_month, func.sum(Billing.cost).label("total_cost"))
        .join(Resource, Resource.resource_id == Billing.resource_id)
        .filter(Resource.owner == owner)
        .group_by(Billing.invoice_month)
        .order_by(Billing.invoice_month)
        .all()
    )

    return [{"month": r.invoice_month, "total_cost": r.total_cost} for r in results]


def top_service_expenditures(service_keyword: str = "network", n: int = 5):
    session = SessionLocal()
    try:
        results = (
            session.query(
                Billing.service,
                Billing.resource_id,
                Resource.owner,
                func.sum(Billing.cost).label("total_cost"),
            )
            .join(Resource, Resource.resource_id == Billing.resource_id)
            .filter(Billing.service.ilike(f"%{service_keyword}%"))
            .group_by(Billing.service, Billing.resource_id, Resource.owner)
            .order_by(desc("total_cost"))
            .limit(n)
            .all()
        )
        return results
    finally:
        session.close()
