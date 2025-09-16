import pytest
from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)

# ------------------------
# Test /health endpoint
# ------------------------
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# ------------------------
# Test /cost_by_owner endpoint
# ------------------------
def test_cost_by_owner():
    month = "2025-08"
    response = client.get(f"/cost_by_owner?month={month}")
    assert response.status_code == 200
    data = response.json()
    assert "month" in data
    assert data["month"] == month
    assert "data" in data

# ------------------------
# Test /kpi endpoint
# ------------------------
def test_kpi():
    month = "2025-08"
    response = client.get(f"/kpi?month={month}")
    assert response.status_code == 200
    data = response.json()
    assert "month" in data
    assert data["month"] == month
    assert "cost_by_owner" in data

# ------------------------
# Test /monthly_trend endpoint
# ------------------------
def test_monthly_trend():
    owner = "alice"
    response = client.get(f"/monthly_trend?owner={owner}")
    assert response.status_code == 200
    data = response.json()
    assert "owner" in data
    assert data["owner"] == owner
    assert "monthly_trend" in data  # must match main.py key

# ------------------------
# Test /ask endpoint
# ------------------------
def test_ask():
    payload = {"question": "Show cost by owner alice in August 2025"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "table" in data
    assert "trend" in data
    assert "top_service" in data
    assert "suggestions" in data
