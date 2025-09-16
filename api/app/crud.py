from sqlalchemy.orm import sessionmaker
from .models import Billing, Resource
from .etl import engine
from sqlalchemy import func

Session = sessionmaker(bind=engine)


def kpi_for_month(month: str):
    session = Session()
    total = (
        session.query(func.sum(Billing.cost))
        .filter(Billing.invoice_month == month)
        .scalar()
        or 0.0
    )
    by_service = (
        session.query(Billing.service, func.sum(Billing.cost))
        .filter(Billing.invoice_month == month)
        .group_by(Billing.service)
        .all()
    )
    by_rg = (
        session.query(Billing.resource_group, func.sum(Billing.cost))
        .filter(Billing.invoice_month == month)
        .group_by(Billing.resource_group)
        .all()
    )
    session.close()
    return {
        "month": month,
        "total_cost": float(total),
        "by_service": {s: float(c) for s, c in by_service},
        "by_resource_group": {rg: float(c) for rg, c in by_rg},
    }


# Recommendation heuristics
def detect_idle_resources(threshold_usage=1.0, month=None):
    """
    Detect resources with usage_qty below threshold in the given month.
    Returns list of (resource_id, cost, estimated_saving)
    """
    session = Session()
    q = session.query(Billing).filter(Billing.usage_qty <= threshold_usage)
    if month:
        q = q.filter(Billing.invoice_month == month)
    rows = q.all()
    results = []
    for r in rows:
        # heuristic: if usage <= threshold, estimate 50% saving by shutting down
        est = r.cost * 0.5
        results.append(
            {
                "resource_id": r.resource_id,
                "cost": r.cost,
                "estimated_saving": est,
                "source": f"billing:{r.id}",
            }
        )
    session.close()
    return results


def missing_owner_tags(month=None):
    session = Session()
    q = session.query(Billing).filter(
        (Billing.resource_group == "unknown") | (Billing.service == "unknown")
    )
    if month:
        q = q.filter(Billing.invoice_month == month)
    rows = q.all()
    out = [
        {"resource_id": r.resource_id, "cost": r.cost, "source": f"billing:{r.id}"}
        for r in rows
    ]
    session.close()
    return out
