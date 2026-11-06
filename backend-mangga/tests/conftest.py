import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.deps import get_db
from core.security import hash_password
from db.session import Base
from main import app
from models.domain_models import Role, User


TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def reset_database() -> Iterator[None]:
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session() -> Iterator[Session]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        nama_lengkap="Admin Gudang",
        role=Role.ADMIN_GUDANG,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["accessToken"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
