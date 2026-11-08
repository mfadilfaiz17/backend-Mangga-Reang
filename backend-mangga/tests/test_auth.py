from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from jose import jwt

from core.config import settings
from core.security import verify_password
from models.domain_models import PasswordResetToken, User
from services import password_reset

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


def test_authenticated_user_can_read_server_role(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "buyerpass123",
            "namaLengkap": "Buyer Test",
            "role": "BUYER_B2B",
        },
    )
    token = login(client, "buyer@example.com", "buyerpass123")

    response = client.get("/api/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["role"] == "BUYER_B2B"


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_authenticated_user_can_update_profile_without_changing_role(
    client: TestClient,
) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "buyerpass123",
            "namaLengkap": "Buyer Test",
            "role": "BUYER_B2B",
        },
    )
    token = login(client, "buyer@example.com", "buyerpass123")

    response = client.patch(
        "/api/auth/me",
        headers=auth_headers(token),
        json={
            "namaLengkap": "Buyer Updated",
            "namaPerusahaan": "PT Updated",
            "role": "ADMIN_GUDANG",
        },
    )

    assert response.status_code == 200
    assert response.json()["namaLengkap"] == "Buyer Updated"
    assert response.json()["namaPerusahaan"] == "PT Updated"
    assert response.json()["role"] == "BUYER_B2B"


def test_authenticated_user_can_change_password(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "buyerpass123",
            "namaLengkap": "Buyer Test",
            "role": "BUYER_B2B",
        },
    )
    token = login(client, "buyer@example.com", "buyerpass123")

    response = client.post(
        "/api/auth/me/password",
        headers=auth_headers(token),
        json={
            "currentPassword": "buyerpass123",
            "newPassword": "newbuyerpass123",
        },
    )

    assert response.status_code == 204
    assert login(client, "buyer@example.com", "newbuyerpass123")


def test_login_rate_limit_rejects_repeated_failures(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "ratelimit@example.com",
            "password": "buyerpass123",
            "namaLengkap": "Buyer Test",
            "role": "BUYER_B2B",
        },
    )
    for _ in range(5):
        response = client.post(
            "/api/auth/login",
            json={"email": "ratelimit@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    response = client.post(
        "/api/auth/login",
        json={"email": "ratelimit@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 429


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


def test_password_reset_email_flow_uses_one_time_token(
    client: TestClient, db_session
) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "reset@example.com",
            "password": "oldpass123",
            "namaLengkap": "Reset User",
            "role": "BUYER_B2B",
        },
    )
    sent: list[str] = []
    original_config = (
        settings.SMTP_HOST,
        settings.SMTP_USERNAME,
        settings.SMTP_PASSWORD,
        settings.SMTP_FROM_EMAIL,
    )
    original_sender = password_reset._send_reset_email
    settings.SMTP_HOST = "smtp.example.com"
    settings.SMTP_USERNAME = "sender@example.com"
    settings.SMTP_PASSWORD = "smtp-password"
    settings.SMTP_FROM_EMAIL = "sender@example.com"
    password_reset._send_reset_email = lambda email, token: sent.append(token)
    try:
        response = client.post(
            "/api/auth/password-reset/request",
            json={"email": "reset@example.com"},
        )
        assert response.status_code == 202
        assert sent
        assert "token" not in response.json()

        reset_token = db_session.query(PasswordResetToken).one()
        reset_token_value = sent[0]
        assert reset_token.token_hash != reset_token_value

        confirmed = client.post(
            "/api/auth/password-reset/confirm",
            json={"token": reset_token_value, "newPassword": "newpass123"},
        )
        assert confirmed.status_code == 204
        user = db_session.query(User).filter(User.email == "reset@example.com").one()
        assert verify_password("newpass123", user.hashed_password)

        reused = client.post(
            "/api/auth/password-reset/confirm",
            json={"token": reset_token_value, "newPassword": "anotherpass123"},
        )
        assert reused.status_code == 400
    finally:
        (
            settings.SMTP_HOST,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL,
        ) = original_config
        password_reset._send_reset_email = original_sender


def test_password_reset_request_does_not_reveal_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/auth/password-reset/request",
        json={"email": "unknown@example.com"},
    )
    assert response.status_code == 202
    assert response.json()["detail"].startswith("Jika email terdaftar")
