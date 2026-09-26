from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


# ==================================================
# HEALTH
# ==================================================


def test_health_status():
    response = client.get("/api/v1/health/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


# ==================================================
# COMPANIES
# ==================================================


def test_companies_count():
    response = client.get("/api/v1/companies/")

    assert response.status_code == 200
    assert response.json()["count"] == 92


def test_companies_returns_list():
    response = client.get("/api/v1/companies/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["companies"], list)


def test_companies_search_tcs():
    response = client.get(
        "/api/v1/companies/",
        params={"search": "TCS"},
    )

    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_company_profile_tcs():
    response = client.get("/api/v1/companies/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "company" in data
    assert "sector" in data
    assert "latest_kpis" in data


def test_company_profile_abb():
    response = client.get("/api/v1/companies/ABB")

    assert response.status_code == 200
    assert response.json()["company_id"] == "ABB"


def test_unknown_company_returns_404():
    response = client.get("/api/v1/companies/NOTREAL")

    assert response.status_code == 404


# ==================================================
# COMPANY FINANCIAL STATEMENTS
# ==================================================


def test_company_pl_tcs():
    response = client.get("/api/v1/companies/TCS/pl")

    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_company_bs_tcs():
    response = client.get("/api/v1/companies/TCS/bs")

    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_company_cashflow_tcs():
    response = client.get(
        "/api/v1/companies/TCS/cashflow"
    )

    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_company_pl_contains_records():
    response = client.get("/api/v1/companies/TCS/pl")

    assert response.status_code == 200

    data = response.json()

    assert "pl_history" in data
    assert isinstance(data["pl_history"], list)


def test_company_bs_contains_records():
    response = client.get("/api/v1/companies/TCS/bs")

    assert response.status_code == 200

    data = response.json()

    assert "balance_sheet_history" in data
    assert isinstance(
        data["balance_sheet_history"],
        list,
    )


def test_company_cashflow_contains_records():
    response = client.get(
        "/api/v1/companies/TCS/cashflow"
    )

    assert response.status_code == 200

    data = response.json()

    assert "cashflow_history" in data
    assert isinstance(
        data["cashflow_history"],
        list,
    )


# ==================================================
# COMPANY RATIOS
# ==================================================


def test_company_ratios_tcs():
    response = client.get(
        "/api/v1/companies/TCS/ratios"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] > 0
    assert "ratios" in data


def test_company_ratios_abb():
    response = client.get(
        "/api/v1/companies/ABB/ratios"
    )

    assert response.status_code == 200
    assert response.json()["company_id"] == "ABB"


def test_company_ratios_unknown():
    response = client.get(
        "/api/v1/companies/NOTREAL/ratios"
    )

    assert response.status_code == 404


# ==================================================
# TEARSHEET
# ==================================================


def test_company_tearsheet_tcs():
    response = client.get(
        "/api/v1/companies/TCS/tearsheet"
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("application/pdf")


def test_company_tearsheet_abb():
    response = client.get(
        "/api/v1/companies/ABB/tearsheet"
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("application/pdf")


# ==================================================
# PEER COMPARISON
# ==================================================


def test_peer_compare_tcs():
    response = client.get(
        "/api/v1/companies/TCS/peers/compare"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "axes" in data
    assert "company" in data
    assert "peer_group_average" in data
    assert "benchmark" in data


def test_peer_compare_axes():
    response = client.get(
        "/api/v1/companies/TCS/peers/compare"
    )

    assert response.status_code == 200

    axes = response.json()["axes"]

    assert len(axes) == 8


# ==================================================
# SCREENER
# ==================================================


def test_screener_default():
    response = client.get(
        "/api/v1/screener/"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 50


def test_screener_min_roe():
    response = client.get(
        "/api/v1/screener/",
        params={"min_roe": 40},
    )

    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_screener_sector_filter():
    response = client.get(
        "/api/v1/screener/",
        params={
            "sector": "Information Technology"
        },
    )

    assert response.status_code == 200


def test_screener_invalid_parameter():
    response = client.get(
        "/api/v1/screener/",
        params={"min_roe": "invalid"},
    )

    assert response.status_code in (400, 422)


# ==================================================
# SECTORS
# ==================================================


def test_sectors_endpoint():
    response = client.get(
        "/api/v1/sectors/"
    )

    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_information_technology_sector():
    response = client.get(
        "/api/v1/sectors/"
        "Information Technology/companies"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 5


def test_unknown_sector():
    response = client.get(
        "/api/v1/sectors/"
        "Unknown Sector/companies"
    )

    assert response.status_code == 404


# ==================================================
# PEERS
# ==================================================


def test_private_banks_peer_group():
    response = client.get(
        "/api/v1/peers/Private Banks"
    )

    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_unknown_peer_group():
    response = client.get(
        "/api/v1/peers/Unknown Group"
    )

    assert response.status_code == 404


# ==================================================
# PORTFOLIO
# ==================================================


def test_portfolio_stats():
    response = client.get(
        "/api/v1/portfolio/stats"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 10


def test_portfolio_stats_contains_statistics():
    response = client.get(
        "/api/v1/portfolio/stats"
    )

    assert response.status_code == 200
    assert "statistics" in response.json()


def test_portfolio_clusters():
    response = client.get(
        "/api/v1/portfolio/clusters"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 92


def test_portfolio_clusters_contains_data():
    response = client.get(
        "/api/v1/portfolio/clusters"
    )

    assert response.status_code == 200
    assert "clusters" in response.json()


# ==================================================
# MARKET CAP
# ==================================================


def test_market_cap_exact_tcs():
    response = client.get(
        "/api/v1/market-cap/TCS"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == 6
    assert data["year_range"] == "2019-2024"


def test_market_cap_history_tcs():
    response = client.get(
        "/api/v1/valuation/market-cap/TCS"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 6


def test_market_cap_unknown_company():
    response = client.get(
        "/api/v1/market-cap/NOTREAL"
    )

    assert response.status_code == 404


# ==================================================
# VALUATION
# ==================================================


def test_valuation_tcs():
    response = client.get(
        "/api/v1/valuation/TCS"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "valuation" in data


def test_valuation_abb():
    response = client.get(
        "/api/v1/valuation/ABB"
    )

    assert response.status_code == 200
    assert response.json()["company_id"] == "ABB"


# ==================================================
# DOCUMENTS
# ==================================================


def test_documents_endpoint():
    response = client.get(
        "/api/v1/documents/"
    )

    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_company_documents_tcs():
    response = client.get(
        "/api/v1/companies/TCS/documents"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] > 0
    assert "documents" in data


def test_company_documents_abb():
    response = client.get(
        "/api/v1/companies/ABB/documents"
    )

    assert response.status_code == 200
    assert response.json()["count"] > 0