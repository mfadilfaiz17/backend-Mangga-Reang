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


def test_non_admin_cannot_approve_rfq(
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

    response = client.put(
        f"/api/rfq/{rfq_id}/approve",
        headers=auth_headers(buyer_token),
    )
    assert response.status_code == 403


def test_admin_can_reject_pending_rfq_without_changing_stock(
    client: TestClient,
    admin_user: User,
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    farmer_token = login(client, "farmer@example.com", "testpass123")
    inventory_id = create_inventory(client, farmer_token)
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")
    rfq_id = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    ).json()["id"]
    admin_token = login(client, "admin@example.com", "adminpass123")

    response = client.put(
        f"/api/rfq/{rfq_id}/reject",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["statusNego"] == "REJECTED"
    assert client.get("/api/mangga/").json()[0]["tonaseTersedia"] == "10.000"


def test_admin_can_complete_approved_rfq(
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
    approved = client.put(
        f"/api/rfq/{rfq_id}/approve",
        headers=auth_headers(admin_token),
    )
    assert approved.status_code == 200

    response = client.put(
        f"/api/rfq/{rfq_id}/complete",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["statusNego"] == "COMPLETED"


def test_buyer_cannot_read_another_buyers_rfq(
    client: TestClient,
    admin_user: User,
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer-one@example.com", role="BUYER_B2B", name="Buyer One")
    buyer_one_token = login(client, "buyer-one@example.com", "testpass123")
    client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_one_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    )
    register(client, email="buyer-two@example.com", role="BUYER_B2B", name="Buyer Two")
    buyer_two_token = login(client, "buyer-two@example.com", "testpass123")

    response = client.get("/api/rfq/me", headers=auth_headers(buyer_two_token))
    assert response.status_code == 200
    assert response.json() == []


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


def test_tracking_requires_order_approval_and_follows_milestones(
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

    before_approval = client.post(
        f"/api/logistik/{rfq_id}/update-status",
        headers=auth_headers(admin_token),
        json={"statusMilestone": "SORTIR_GUDANG"},
    )
    assert before_approval.status_code == 409

    assert client.put(
        f"/api/rfq/{rfq_id}/approve",
        headers=auth_headers(admin_token),
    ).status_code == 200
    valid_next = client.post(
        f"/api/logistik/{rfq_id}/update-status",
        headers=auth_headers(admin_token),
        json={"statusMilestone": "SORTIR_GUDANG", "catatanQc": "Lulus sortir"},
    )
    assert valid_next.status_code == 201

    duplicate = client.post(
        f"/api/logistik/{rfq_id}/update-status",
        headers=auth_headers(admin_token),
        json={"statusMilestone": "SORTIR_GUDANG"},
    )
    assert duplicate.status_code == 409

    backward = client.post(
        f"/api/logistik/{rfq_id}/update-status",
        headers=auth_headers(admin_token),
        json={"statusMilestone": "DIPROSES_PETANI"},
    )
    assert backward.status_code == 409


def test_buyer_cannot_update_tracking_or_mass_assign_actor(
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
    assert client.put(
        f"/api/rfq/{rfq_id}/approve",
        headers=auth_headers(admin_token),
    ).status_code == 200

    response = client.post(
        f"/api/logistik/{rfq_id}/update-status",
        headers=auth_headers(buyer_token),
        json={
            "statusMilestone": "SORTIR_GUDANG",
            "updatedBy": 999,
        },
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
