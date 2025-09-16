from sqlalchemy import func
from api.app.etl import SessionLocal, Billing, Resource

session = SessionLocal()

# Aggregate cost by owner for April 2025
results = session.query(
    Resource.owner,
    func.sum(Billing.cost).label("total_cost")
).join(Resource, Resource.resource_id == Billing.resource_id
).filter(Billing.invoice_month.like("2025-04%")
).group_by(Resource.owner).all()

session.close()

print("Cost by owner for April 2025:")
for owner, cost in results:
    print(f"{owner}: {cost}")
