import pytest
import pandas as pd
from api.app.kpi import get_cost_by_owner, monthly_trend, top_service_expenditures

# Test get_cost_by_owner
def test_get_cost_by_owner():
    data = get_cost_by_owner("2025-04")
    assert isinstance(data, list), "Expected list of tuples"
    for owner, cost in data:
        assert isinstance(owner, str), "Owner should be a string"
        assert isinstance(cost, (float, int)), "Cost should be numeric"

# Test monthly_trend
def test_monthly_trend():
    owner = "alice"  # or any owner that exists in your DB
    df = monthly_trend(owner)
    assert isinstance(df, list), "Expected a list of dicts"
    for row in df:
        assert "month" in row
        assert "total_cost" in row
        assert isinstance(row["month"], str)
        assert isinstance(row["total_cost"], (float, int))

# Test top_service_expenditures
def test_top_service_expenditures():
    results = top_service_expenditures(service_keyword="network", n=3)
    assert isinstance(results, list), "Expected list of tuples"
    assert len(results) <= 3, "Returned list should not exceed limit n"
    for service, resource_id, owner, total_cost in results:
        assert isinstance(service, str)
        assert isinstance(resource_id, (int, str))
        assert isinstance(owner, str) or owner is None
        assert isinstance(total_cost, (float, int))
