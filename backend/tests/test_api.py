import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["app_name"] == "CYBERSCOPE"
    assert "synthetic data" in data["disclaimer"]


def test_dashboard_stats():
    response = client.get("/api/stats/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert data["kpis"]["total_cases"] >= 40
    assert data["kpis"]["detected_campaigns"] >= 3


def test_list_cases_and_filter():
    response = client.get("/api/cases?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    first_case = data[0]
    assert "case_number" in first_case
    assert "risk_score" in first_case

    # Filter by severity
    high_resp = client.get("/api/cases?severity=HIGH")
    assert high_resp.status_code == 200
    for c in high_resp.json():
        assert c["severity"] == "HIGH"


def test_get_case_detail_and_timeline():
    # Fetch first case
    list_resp = client.get("/api/cases?limit=1")
    first_id = list_resp.json()[0]["id"]

    detail_resp = client.get(f"/api/cases/{first_id}")
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert "risk_breakdown" in data
    assert "signals" in data["risk_breakdown"]

    timeline_resp = client.get(f"/api/cases/{first_id}/timeline")
    assert timeline_resp.status_code == 200
    assert "events" in timeline_resp.json()


def test_graph_endpoints():
    graph_resp = client.get("/api/graph?limit=50")
    assert graph_resp.status_code == 200
    g_data = graph_resp.json()
    assert "nodes" in g_data
    assert "edges" in g_data
    assert len(g_data["nodes"]) > 0

    shared_resp = client.get("/api/graph/shared-infrastructure")
    assert shared_resp.status_code == 200
    assert "shared_infrastructure" in shared_resp.json()


def test_transactions_and_trace():
    tx_resp = client.get("/api/transactions?limit=10")
    assert tx_resp.status_code == 200
    txs = tx_resp.json()
    assert len(txs) > 0

    first_tx = txs[0]
    trace_payload = {
        "start_transaction_id": first_tx["id"],
        "max_hops": 3
    }
    trace_resp = client.post("/api/transactions/trace-funds", json=trace_payload)
    assert trace_resp.status_code == 200
    t_data = trace_resp.json()
    assert "nodes" in t_data
    assert "edges" in t_data


def test_campaigns():
    camp_resp = client.get("/api/campaigns")
    assert camp_resp.status_code == 200
    camps = camp_resp.json()
    assert len(camps) >= 3
    first_camp = camps[0]

    detail_resp = client.get(f"/api/campaigns/{first_camp['id']}")
    assert detail_resp.status_code == 200
    c_data = detail_resp.json()
    assert "cases" in c_data


def test_investigations_cyber_assist():
    query_payload = {
        "case_id": 1,
        "query": "Why was this case flagged?"
    }
    resp = client.post("/api/investigations/query", json=query_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "evidence_citations" in data
    assert "recommended_next_steps" in data
    assert len(data["evidence_citations"]) > 0


def test_natural_language_search():
    search_resp = client.get("/api/search?q=secure-kyc-update.com")
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert "results" in data or "cases" in data
