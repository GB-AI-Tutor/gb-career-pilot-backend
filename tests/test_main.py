def test_health_check(client):
    response = client.get("/health")
    assert response.json()["status"] == "healthy"