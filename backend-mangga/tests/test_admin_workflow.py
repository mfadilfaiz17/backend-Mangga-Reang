from fastapi.testclient import TestClient
import pytest

from models.domain_models import User

from .conftest import auth_headers, login
from .test_inventory_rfq import create_inventory, register


def test_admin_approval_reduces_stock_and_creates_tracking(
    client: TestClient,
    admin_user: User,
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")
    rfq_id = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    ).json()["id"]
    admin_token = login(client, "admin@example.com", "adminpass123")

    response = client.put(
        f"/api/rfq/{rfq_id}/approve",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["statusNego"] == "APPROVED"
    assert client.get("/api/mangga/").json()[0]["tonaseTersedia"] == "8.000"

    tracking = client.get(
        f"/api/logistik/{rfq_id}",
        headers=auth_headers(buyer_token),
    )
    assert tracking.status_code == 200
    assert tracking.json()[0]["statusMilestone"] == "DIPROSES_PETANI"


def test_admin_cannot_approve_rfq_twice(
    client: TestClient,
    admin_user: User,
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")
    rfq_id = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    ).json()["id"]
    admin_token = login(client, "admin@example.com", "adminpass123")

    first = client.put(f"/api/rfq/{rfq_id}/approve", headers=auth_headers(admin_token))
    second = client.put(f"/api/rfq/{rfq_id}/approve", headers=auth_headers(admin_token))
    assert first.status_code == 200
    assert second.status_code == 409


def test_buyer_cannot_view_another_buyers_tracking(
    client: TestClient,
    admin_user: User,
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer-one@example.com", role="BUYER_B2B", name="Buyer One")
    buyer_one_token = login(client, "buyer-one@example.com", "testpass123")
    rfq_id = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_one_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    ).json()["id"]
    admin_token = login(client, "admin@example.com", "adminpass123")
    client.put(f"/api/rfq/{rfq_id}/approve", headers=auth_headers(admin_token))

    register(client, email="buyer-two@example.com", role="BUYER_B2B", name="Buyer Two")
    buyer_two_token = login(client, "buyer-two@example.com", "testpass123")
    response = client.get(
        f"/api/logistik/{rfq_id}",
        headers=auth_headers(buyer_two_token),
    )
    assert response.status_code == 403


def test_approval_rolls_back_when_tracking_creation_fails(
    client: TestClient,
    admin_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")
    rfq_id = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    ).json()["id"]
    admin_token = login(client, "admin@example.com", "adminpass123")

    def fail_tracking_creation(*args: object, **kwargs: object) -> None:
        raise RuntimeError("tracking failure")

    monkeypatch.setattr(
        "services.rfq.logistics.create",
        fail_tracking_creation,
    )
    with pytest.raises(RuntimeError, match="tracking failure"):
        client.put(
            f"/api/rfq/{rfq_id}/approve",
            headers=auth_headers(admin_token),
        )

    orders = client.get("/api/rfq/me", headers=auth_headers(buyer_token))
    assert orders.json()[0]["statusNego"] == "PENDING"
    assert client.get("/api/mangga/").json()[0]["tonaseTersedia"] == "10.000"
