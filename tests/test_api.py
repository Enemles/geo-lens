"""End-to-end API tests through the real app (mock provider, offline)."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_creates_and_returns_result(client):
    r = client.post(
        "/api/analyze",
        json={"brand": "Yolando", "category": "AI brand-visibility tools"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] is not None
    assert body["brand"] == "Yolando"
    assert 0 <= body["visibility_score"] <= 100
    assert len(body["results"]) > 0
    assert all(0 <= m["score"] <= 1 for m in body["results"])


def test_analyze_rejects_empty_brand(client):
    r = client.post("/api/analyze", json={"brand": ""})
    assert r.status_code == 422


def test_list_and_get_roundtrip(client):
    created = client.post("/api/analyze", json={"brand": "Acme"}).json()
    cid = created["id"]

    listed = client.get("/api/analyses").json()
    assert any(a["id"] == cid for a in listed)

    fetched = client.get(f"/api/analyses/{cid}").json()
    assert fetched["id"] == cid
    assert fetched["brand"] == "Acme"
    assert len(fetched["results"]) == len(created["results"])


def test_get_missing_returns_404(client):
    assert client.get("/api/analyses/999999").status_code == 404


def test_delete_then_gone(client):
    cid = client.post("/api/analyze", json={"brand": "Temp"}).json()["id"]
    assert client.delete(f"/api/analyses/{cid}").status_code == 204
    assert client.get(f"/api/analyses/{cid}").status_code == 404


def test_stream_emits_progress_and_summary(client):
    r = client.post(
        "/api/analyze/stream",
        json={"brand": "Yolando", "category": "AI tools"},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    assert "event: progress" in r.text
    assert "event: summary" in r.text
