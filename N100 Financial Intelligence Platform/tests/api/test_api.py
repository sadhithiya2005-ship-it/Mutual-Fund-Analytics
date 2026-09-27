
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_companies():
    response = client.get("/api/v1/companies/")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["companies"]) == 92


def test_ratios():
    response = client.get("/api/v1/ratios/ABB")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert data["company_name"] == "Abbott India Ltd"
    assert data["count"] > 0


def test_valuation():
    response = client.get("/api/v1/valuation/ABB")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert data["company_name"] == "Abbott India Ltd"
    assert "valuation" in data