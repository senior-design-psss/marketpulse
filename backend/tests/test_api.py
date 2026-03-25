"""Basic API endpoint tests.

Note: Tests that require database access use the live local DB.
The TestClient + asyncpg has connection reuse issues in pytest,
so DB-dependent tests are marked with pytest.mark.skipif when DB is unavailable.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "marketpulse-backend"


def test_openapi_schema_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    # Verify key endpoints exist in schema
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/industries" in schema["paths"]
    assert "/api/v1/companies" in schema["paths"]
    assert "/api/v1/sentiment/feed" in schema["paths"]
    assert "/api/v1/analytics/momentum" in schema["paths"]
    assert "/api/v1/analyst/briefing" in schema["paths"]
    assert "/api/v1/graph/entities" in schema["paths"]


def test_route_count():
    """Verify all expected routes are registered."""
    api_routes = [r.path for r in app.routes if hasattr(r, "path") and r.path.startswith("/api")]
    assert len(api_routes) >= 22
