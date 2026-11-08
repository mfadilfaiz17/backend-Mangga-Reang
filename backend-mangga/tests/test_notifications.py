from fastapi.testclient import TestClient

from models.domain_models import User

from .conftest import auth_headers, login
from .test_inventory_rfq import create_inventory, register


def test_notifications_are_user_scoped_and_markable(
    client: TestClient, admin_user: User
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer-one@example.com", role="BUYER_B2B", name="Buyer One")
    buyer_one_token = login(client, "buyer-one@example.com", "testpass123")
    created = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_one_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    )
    assert created.status_code == 201

    notifications = client.get(
        "/api/notifications/me", headers=auth_headers(buyer_one_token)
    )
    assert notifications.status_code == 200
    assert notifications.json()[0]["notificationType"] == "RFQ_CREATED"
    assert notifications.json()[0]["isRead"] is False

    marked = client.patch(
        "/api/notifications/me/read-all", headers=auth_headers(buyer_one_token)
    )
    assert marked.status_code == 200
    assert marked.json()["updatedCount"] == 1

    register(client, email="buyer-two@example.com", role="BUYER_B2B", name="Buyer Two")
    buyer_two_token = login(client, "buyer-two@example.com", "testpass123")
    other_notifications = client.get(
        "/api/notifications/me", headers=auth_headers(buyer_two_token)
    )
    assert other_notifications.status_code == 200
    assert other_notifications.json() == []


def test_rfq_status_and_tracking_create_buyer_notifications(
    client: TestClient, admin_user: User
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
        f"/api/rfq/{rfq_id}/approve", headers=auth_headers(admin_token)
    ).status_code == 200
    assert client.post(
        f"/api/logistik/{rfq_id}/update-status",
        headers=auth_headers(admin_token),
        json={"statusMilestone": "SORTIR_GUDANG"},
    ).status_code == 201

    notifications = client.get(
        "/api/notifications/me", headers=auth_headers(buyer_token)
    ).json()
    assert [item["notificationType"] for item in notifications[:3]] == [
        "TRACKING_UPDATED",
        "RFQ_APPROVED",
        "RFQ_CREATED",
    ]
