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


def test_api_routes_are_registered_only_under_v1():
    client = TestClient(create_app())

    assert client.get("/api/v1/health/live").status_code == 200
    assert client.post("/api/v1/search", json={"query": "Docker startup failure"}).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.test", "password": "wrong-password"},
    ).status_code == 401
    assert client.post("/search", json={"query": "Docker startup failure"}).status_code == 404
    assert client.post(
        "/auth/login",
        json={"email": "missing@example.test", "password": "wrong-password"},
    ).status_code == 404


def test_no_duplicate_route_path_method_combinations():
    routes = []
    for route in create_app().routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if not methods or path is None:
            continue
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.append((path, method))

    assert len(routes) == len(set(routes))
