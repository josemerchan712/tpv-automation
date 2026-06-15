import pytest
from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash, create_access_token


@pytest.fixture
def registered_user(db):
    user = User(
        username="testcajero",
        password_hash=get_password_hash("secret123"),
        role=UserRole.cashier,
    )
    db.add(user)
    db.flush()
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client, registered_user):
    resp = client.post(
        "/auth/login", json={"username": "testcajero", "password": "secret123"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    resp = client.post(
        "/auth/login", json={"username": "testcajero", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post(
        "/auth/login", json={"username": "nobody", "password": "anything"}
    )
    assert resp.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────

def test_me_authenticated(client, registered_user):
    login = client.post(
        "/auth/login", json={"username": "testcajero", "password": "secret123"}
    )
    token = login.json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testcajero"
    assert data["role"] == "cashier"
    assert "id" in data


def test_me_no_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token(client):
    resp = client.get(
        "/auth/me", headers={"Authorization": "Bearer this.is.not.valid"}
    )
    assert resp.status_code == 401


def test_me_token_unknown_user(client):
    # Valid JWT but username not in DB.
    token = create_access_token({"sub": "ghost_user"})
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
