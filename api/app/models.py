from sqlalchemy import Column, Integer, String, Float, JSON
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Billing(Base):
    __tablename__ = "billing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_month = Column(String, index=True)
    account_id = Column(String)
    subscription = Column(String)
    service = Column(String, index=True)
    resource_group = Column(String, index=True)
    resource_id = Column(String, index=True)
    region = Column(String)
    usage_qty = Column(Float)
    unit_cost = Column(Float)
    cost = Column(Float)


class Resource(Base):
    __tablename__ = "resources"
    resource_id = Column(String, primary_key=True)
    owner = Column(String, nullable=True)
    env = Column(String)
    tags_json = Column(JSON)
