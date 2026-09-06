from __future__ import annotations

def create_session(client):
    response = client.post(
        "/api/sessions",
        json={"requested_language": "hi-IN"},
    )
    assert response.status_code == 201
    return response.get_json()


def auth(data):
    return {"Authorization": f"Bearer {data['caller_capability']}"}


def test_health_has_correlation_id(client):
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"]
    assert response.headers["Cache-Control"] == "no-store"


def test_create_session_returns_scoped_join_material(client):
    data = create_session(client)

    assert data["status"] == "created"
    assert data["requested_language"] == "hi-IN"
    assert data["rtc"]["channel"].startswith("echosphere-")
    assert data["rtc"]["token"].startswith("token-echosphere-")
    assert "app_certificate" not in data["rtc"]
    assert "customer_secret" not in str(data).lower()


def test_session_requires_matching_capability(client):
    data = create_session(client)

    response = client.get(
        f"/api/sessions/{data['session_id']}",
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def test_start_and_end_are_idempotent(client):
    data = create_session(client)
    endpoint = f"/api/sessions/{data['session_id']}"

    first_start = client.post(endpoint + "/start", headers=auth(data))
    second_start = client.post(endpoint + "/start", headers=auth(data))
    assert first_start.status_code == 202
    assert second_start.status_code == 202
    assert first_start.get_json()["status"] == "disclosure"

    first_end = client.post(endpoint + "/end", headers=auth(data))
    second_end = client.post(endpoint + "/end", headers=auth(data))
    assert first_end.status_code == 202
    assert second_end.status_code == 202
    assert second_end.get_json()["status"] == "ended"


def test_rejects_unsupported_language(client):
    response = client.post(
        "/api/sessions",
        json={"requested_language": "fr-FR"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"
