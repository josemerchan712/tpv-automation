import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db():
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash


@pytest.fixture
def admin_user(db):
    user = User(
        username="admin_test",
        password_hash=get_password_hash("admin123"),
        role=UserRole.admin,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def cashier_user(db):
    user = User(
        username="cashier_test",
        password_hash=get_password_hash("cash123"),
        role=UserRole.cashier,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def admin_headers(client, admin_user):
    resp = client.post(
        "/auth/login", json={"username": "admin_test", "password": "admin123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cashier_headers(client, cashier_user):
    resp = client.post(
        "/auth/login", json={"username": "cashier_test", "password": "cash123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
