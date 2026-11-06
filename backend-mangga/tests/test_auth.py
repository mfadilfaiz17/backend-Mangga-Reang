from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from jose import jwt

from core.config import settings

from .conftest import auth_headers, login


def test_register_and_login_use_camel_case(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "buyerpass123",
            "namaLengkap": "Buyer Test",
            "role": "BUYER_B2B",
            "namaPerusahaan": "PT Test",
        },
    )

    assert response.status_code == 201
    assert response.json()["namaLengkap"] == "Buyer Test"
    assert "hashedPassword" not in response.json()
    assert login(client, "buyer@example.com", "buyerpass123")


def test_register_rejects_admin_and_short_password(client: TestClient) -> None:
    short_password = client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.com",
            "password": "short",
            "namaLengkap": "Admin",
            "role": "ADMIN_GUDANG",
        },
    )
    assert short_password.status_code == 422

    admin_role = client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.com",
            "password": "adminpass123",
            "namaLengkap": "Admin",
            "role": "ADMIN_GUDANG",
        },
    )
    assert admin_role.status_code == 403


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "buyerpass123",
            "namaLengkap": "Buyer Test",
            "role": "BUYER_B2B",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "buyer@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_private_endpoint_requires_valid_token(client: TestClient) -> None:
    response = client.post(
        "/api/mangga/",
        json={
            "varietas": "GEDONG_GINCU",
            "grade": "GRADE_A",
            "tonaseTersedia": 10,
            "hargaPerTon": 5000000,
            "lokasiKebun": "Cianjur",
        },
    )
    assert response.status_code == 401

    invalid_token = client.get(
        "/api/rfq/me",
        headers=auth_headers("not-a-valid-token"),
    )
    assert invalid_token.status_code == 401


def test_expired_and_wrong_algorithm_tokens_are_rejected(client: TestClient) -> None:
    expired = jwt.encode(
        {
            "user_id": "1",
            "role": "BUYER_B2B",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    expired_response = client.get(
        "/api/rfq/me",
        headers=auth_headers(expired),
    )
    assert expired_response.status_code == 401

    wrong_algorithm = jwt.encode(
        {
            "user_id": "1",
            "role": "BUYER_B2B",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm="HS384",
    )
    wrong_algorithm_response = client.get(
        "/api/rfq/me",
        headers=auth_headers(wrong_algorithm),
    )
    assert wrong_algorithm_response.status_code == 401


def test_health_check_reports_database(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
