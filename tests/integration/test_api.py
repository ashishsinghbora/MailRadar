import uuid
from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    resp2 = client.get("/api/v1/health")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "healthy"


def test_auth_workflow(client: TestClient):
    random_email = f"test_{uuid.uuid4().hex[:6]}@example.org"
    register_payload = {
        "email": random_email,
        "password": "StrongPassword123!",
        "full_name": "API Tester",
        "organization_name": "API Testing Lab"
    }

    # 1. Register
    reg_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    token = data["access_token"]

    # 2. Get Me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == random_email

    # 3. Login
    login_resp = client.post("/api/v1/auth/login/json", json={
        "email": random_email,
        "password": "StrongPassword123!"
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_projects_crud(client: TestClient, auth_headers):
    # Create project
    proj_payload = {
        "name": "telemetry-agent",
        "full_name": "mesh-dev/telemetry-agent",
        "description": "Distributed agent for high throughput metrics.",
        "owner": "mesh-dev",
        "stars_count": 840,
        "forks_count": 92,
        "language": "Go",
        "topics": ["telemetry", "metrics", "agent"],
        "repository_url": "https://github.com/mesh-dev/telemetry-agent"
    }

    create_resp = client.post("/api/v1/projects", json=proj_payload, headers=auth_headers)
    assert create_resp.status_code == 200
    proj_data = create_resp.json()
    proj_id = proj_data["id"]

    # List projects
    list_resp = client.get("/api/v1/projects", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(p["id"] == proj_id for p in items)

    # Get project
    get_resp = client.get(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "telemetry-agent"


def test_contacts_export(client: TestClient, auth_headers):
    # Export CSV
    csv_resp = client.get("/api/v1/contacts/export?format=csv", headers=auth_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "Email,Full Name" in csv_resp.text

    # Export JSON
    json_resp = client.get("/api/v1/contacts/export?format=json", headers=auth_headers)
    assert json_resp.status_code == 200
    assert "application/json" in json_resp.headers["content-type"]
