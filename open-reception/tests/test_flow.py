import os
from pathlib import Path

db_file = Path(__file__).parent / "test.sqlite3"
if db_file.exists():
    db_file.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"

from fastapi.testclient import TestClient
from app.main import Base, SessionLocal, User, app, engine, password_hash


def test_login_passport_application_and_matching_flow():
    with TestClient(app) as client:
        registered = client.post("/auth/register", json={"email": "member@example.org", "password": "correct-horse-battery"}).json()
        assert registered["status"] == "member"

        login = client.post("/auth/login", json={"email": "member@example.org", "password": "correct-horse-battery"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        passport = client.put("/passport/human", headers=headers, json={"display_name": "Steward Kim", "domains": ["food-desert"]})
        assert passport.status_code == 200

        application = client.post(
            "/steward-human/applications", headers=headers,
            json={"domain": "food-desert", "statement": "I will supervise community food access tasks."},
        )
        assert application.status_code == 201

        recommendation = client.post(
            "/matching/recommendations", headers=headers,
            json={"domain": "food-desert", "risk": "low", "required_permissions": ["research"]},
        )
        body = recommendation.json()
        assert body["status"] == "recommendation_only"
        assert body["human_approval_required"] is True
        assert body["candidates"][0]["agent_id"] == "luna"


def test_admin_kill_switch_blocks_matching():
    with TestClient(app) as client:
        with SessionLocal() as db:
            admin = User(email="admin@example.org", password_hash=password_hash("administrator-pass"), role="admin")
            db.add(admin)
            db.commit()
        login = client.post("/auth/login", json={"email": "admin@example.org", "password": "administrator-pass"}).json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        assert client.post("/admin/kill-switch", headers=headers, json={"active": True, "reason": "safety drill"}).status_code == 200
        response = client.post("/matching/recommendations", headers=headers, json={"domain": "food-desert"})
        assert response.status_code == 423
        client.post("/admin/kill-switch", headers=headers, json={"active": False, "reason": "drill complete"})
