from fastapi.testclient import TestClient

from .conftest import auth_headers, login


def register(client: TestClient, *, email: str, role: str, name: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "testpass123",
            "namaLengkap": name,
            "role": role,
        },
    )
    assert response.status_code == 201, response.text


def create_inventory(client: TestClient, token: str) -> int:
    response = client.post(
        "/api/mangga/",
        headers=auth_headers(token),
        json={
            "varietas": "GEDONG_GINCU",
            "grade": "GRADE_A",
            "tonaseTersedia": 10,
            "hargaPerTon": 5000000,
            "lokasiKebun": "Cianjur",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_farmer_can_create_and_update_inventory(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer Test")
    farmer_token = login(client, "farmer@example.com", "testpass123")
    inventory_id = create_inventory(client, farmer_token)

    response = client.put(
        f"/api/mangga/{inventory_id}",
        headers=auth_headers(farmer_token),
        json={"tonaseTersedia": 8, "hargaPerTon": 5200000},
    )
    assert response.status_code == 200
    assert response.json()["tonaseTersedia"] == "8.000"


def test_buyer_cannot_create_inventory(client: TestClient) -> None:
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer Test")
    buyer_token = login(client, "buyer@example.com", "testpass123")

    response = client.post(
        "/api/mangga/",
        headers=auth_headers(buyer_token),
        json={
            "varietas": "GEDONG_GINCU",
            "grade": "GRADE_A",
            "tonaseTersedia": 10,
            "hargaPerTon": 5000000,
            "lokasiKebun": "Cianjur",
        },
    )
    assert response.status_code == 403


def test_buyer_creates_rfq_and_sees_own_orders(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")

    response = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 2},
    )
    assert response.status_code == 201
    assert response.json()["statusNego"] == "PENDING"
    assert response.json()["totalHarga"] == "10000000.00"

    orders = client.get("/api/rfq/me", headers=auth_headers(buyer_token))
    assert orders.status_code == 200
    assert len(orders.json()) == 1


def test_rfq_rejects_tonnage_above_stock(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")

    response = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_token),
        json={"idMangga": inventory_id, "tonaseDiminta": 11},
    )
    assert response.status_code == 409
