# Backend API Specification

## 1. Konvensi Umum

- Base path: `/api`.
- Content type: `application/json`.
- Field request dan response: `camelCase` (lower camel case).
- Field internal Python dan database: `snake_case`; alias schema melakukan
  konversi di batas API.
- Nama class/type: `PascalCase`; nilai enum: `UPPER_SNAKE_CASE`.
- Contoh mapping: JSON `tonaseDiminta` <-> Python/database `tonase_diminta`.
- Authentication: `Authorization: Bearer <access_token>`.
- Error response minimal memuat `detail`.
- Endpoint collection mendukung `offset` (default `0`) dan `limit` (default
  `50`, maksimum `100`).

## 2. Authentication

### `POST /auth/register`

Publik. Membuat user baru setelah email dan password divalidasi. Password
di-hash dengan bcrypt. Role `ADMIN_GUDANG` harus dibuat melalui provisioning
terkontrol, bukan endpoint publik.

**Error penting:** `409` bila email sudah digunakan, `403` bila role admin
dikirim melalui register publik, dan `422` bila payload tidak valid.

### `POST /auth/login`

Publik. Mengembalikan:

```json
{
  "accessToken": "<jwt>",
  "tokenType": "bearer"
}
```

JWT wajib memuat `user_id`, `role`, dan expiry. Claim JWT mengikuti format
internal token dan tidak mengikuti alias JSON response.

## 3. Inventory

### `GET /mangga/`

Publik. Hanya mengembalikan inventaris dengan `isActive=true` dan
`tonaseTersedia > 0`. Mendukung query `offset` dan `limit`.

### `POST /mangga/`

Role: `PETANI`, `ADMIN_GUDANG`. Membuat stok baru. `idPetani` tidak boleh
dipalsukan oleh buyer dan harus berasal dari user/role yang sah.

### `PUT /mangga/{id}`

Terautentikasi. Mengubah field yang diizinkan sesuai ownership dan role.
Primary key dan foreign key tidak dapat diubah melalui update umum.

## 4. RFQ

### `POST /rfq/`

Role: `BUYER_B2B`. Server memvalidasi inventaris aktif, tonase positif, dan
ketersediaan stok. Status awal selalu `PENDING`; client tidak boleh mengirim
status final.

### `GET /rfq/me`

Role: `BUYER_B2B`. Query dibatasi dengan `idBuyer` dari token, bukan parameter
user dari client. Mendukung query `offset` dan `limit`.

### `GET /rfq/all`

Role: `ADMIN_GUDANG`. Mengembalikan RFQ dengan query `offset` dan `limit`.

### `PUT /rfq/{id}/approve`

Role: `ADMIN_GUDANG`. Operasi atomik: lock, validasi `PENDING`, cek stok
terkini, kurangi stok, ubah status ke `APPROVED`, dan buat tracking
`DIPROSES_PETANI`.

### Transisi status RFQ

```text
PENDING -> APPROVED
PENDING -> REJECTED
APPROVED -> COMPLETED
```

Endpoint tidak boleh mengizinkan transisi arbitrer atau approval berulang.

## 5. Logistics

### `GET /logistik/{id_rfq}`

Terautentikasi. Mengembalikan histori tracking berdasarkan RFQ. Akses buyer
dibatasi pada RFQ miliknya; admin dapat melihat seluruhnya. Mendukung query
`offset` dan `limit`.

### `POST /logistik/{id_rfq}/update-status`

Role: `ADMIN_GUDANG`. Menambahkan event baru dengan status enum dan catatan.
Histori lama tidak ditimpa.

## 6. Status Code

| Status | Penggunaan |
|---:|---|
| `200` | GET/update berhasil |
| `201` | resource baru berhasil dibuat |
| `400` | aturan bisnis/payload tidak dapat diproses |
| `401` | token hilang atau tidak valid |
| `403` | role tidak berwenang |
| `404` | resource tidak ditemukan |
| `409` | konflik state atau duplicate |
| `422` | validasi schema gagal |

## 7. Non-Goals API

API versi ini tidak menyediakan payment, invoice, refund, GPS real-time, chat,
notifikasi eksternal, multi-warehouse, pajak, maupun endpoint frontend/3D
rendering.
