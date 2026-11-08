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

    mine = client.get("/api/mangga/me", headers=auth_headers(farmer_token))
    assert mine.status_code == 200
    assert mine.json()[0]["tonaseTersedia"] == "8.000"


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


def test_farmer_cannot_update_another_farmers_inventory(client: TestClient) -> None:
    register(client, email="owner@example.com", role="PETANI", name="Owner")
    inventory_id = create_inventory(client, login(client, "owner@example.com", "testpass123"))
    register(client, email="other@example.com", role="PETANI", name="Other")
    other_token = login(client, "other@example.com", "testpass123")

    response = client.put(
        f"/api/mangga/{inventory_id}",
        headers=auth_headers(other_token),
        json={"tonaseTersedia": 1},
    )
    assert response.status_code == 403


def test_buyer_cannot_update_inventory(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")

    response = client.put(
        f"/api/mangga/{inventory_id}",
        headers=auth_headers(buyer_token),
        json={"tonaseTersedia": 1},
    )
    assert response.status_code == 403


def test_inventory_update_rejects_mass_assignment(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    farmer_token = login(client, "farmer@example.com", "testpass123")
    inventory_id = create_inventory(client, farmer_token)

    response = client.put(
        f"/api/mangga/{inventory_id}",
        headers=auth_headers(farmer_token),
        json={"idPetani": 999, "status": "APPROVED"},
    )
    assert response.status_code == 422


def test_public_inventory_filters_active_positive_stock(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    farmer_token = login(client, "farmer@example.com", "testpass123")
    inventory_id = create_inventory(client, farmer_token)

    updated = client.put(
        f"/api/mangga/{inventory_id}",
        headers=auth_headers(farmer_token),
        json={"tonaseTersedia": 0},
    )
    assert updated.status_code == 200

    response = client.get("/api/mangga/?varietas=GEDONG_GINCU&grade=GRADE_A&lokasi=cian")
    assert response.status_code == 200
    assert response.json() == []


def test_private_inventory_includes_zero_stock(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    farmer_token = login(client, "farmer@example.com", "testpass123")
    inventory_id = create_inventory(client, farmer_token)
    response = client.put(
        f"/api/mangga/{inventory_id}",
        headers=auth_headers(farmer_token),
        json={"tonaseTersedia": 0, "isActive": False},
    )
    assert response.status_code == 200

    mine = client.get("/api/mangga/me", headers=auth_headers(farmer_token))
    assert mine.status_code == 200
    assert mine.json()[0]["isActive"] is False


def test_admin_can_create_inventory_for_existing_farmer(
    client: TestClient, admin_user: object
) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    farmer_token = login(client, "farmer@example.com", "testpass123")
    farmer_id = client.get("/api/auth/me", headers=auth_headers(farmer_token)).json()["id"]
    admin_token = login(client, "admin@example.com", "adminpass123")

    response = client.post(
        "/api/mangga/",
        headers=auth_headers(admin_token),
        json={
            "idPetani": farmer_id,
            "varietas": "CENGKIR",
            "grade": "GRADE_B",
            "tonaseTersedia": 5,
            "hargaPerTon": 3000000,
            "lokasiKebun": "Majalengka",
        },
    )
    assert response.status_code == 201
    assert response.json()["idPetani"] == farmer_id

    inventory_id = response.json()["id"]
    update = client.put(
        f"/api/mangga/{inventory_id}",
        headers=auth_headers(admin_token),
        json={"isActive": False},
    )
    assert update.status_code == 200
    assert update.json()["isActive"] is False


def test_inventory_location_filter_is_parameterized(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    create_inventory(client, login(client, "farmer@example.com", "testpass123"))

    response = client.get("/api/mangga/?lokasi=%27%20OR%201%3D1%20--")
    assert response.status_code == 200
    assert response.json() == []


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


def test_rfq_rejects_mass_assignment(client: TestClient) -> None:
    register(client, email="farmer@example.com", role="PETANI", name="Farmer")
    inventory_id = create_inventory(client, login(client, "farmer@example.com", "testpass123"))
    register(client, email="buyer@example.com", role="BUYER_B2B", name="Buyer")
    buyer_token = login(client, "buyer@example.com", "testpass123")

    response = client.post(
        "/api/rfq/",
        headers=auth_headers(buyer_token),
        json={
            "idMangga": inventory_id,
            "tonaseDiminta": 2,
            "statusNego": "APPROVED",
            "totalHarga": 1,
            "idBuyer": 999,
        },
    )
    assert response.status_code == 422
