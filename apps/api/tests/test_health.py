from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_response_shape():
    client = TestClient(create_app())

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["service"] == "api"
    assert body["data"]["status"] == "ok"
    assert "request_id" not in body["data"]
    assert "x-request-id" in response.headers
