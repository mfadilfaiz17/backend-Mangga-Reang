# Backend Architecture

## 1. Tujuan

Dokumen ini menetapkan batas arsitektur backend Juragan Mangga Reang. PRD tetap menjadi sumber kebenaran untuk kebutuhan produk; dokumen ini menjelaskan cara kebutuhan tersebut diimplementasikan.

## 2. Keputusan Arsitektur

- **Gaya:** decoupled monolithic REST API.
- **Runtime:** Python 3.10+ dengan FastAPI.
- **Persistence:** PostgreSQL melalui SQLAlchemy.
- **Validation:** Pydantic v2.
- **Authentication:** JWT Bearer.
- **Password hashing:** bcrypt melalui Passlib.
- **API contract:** JSON dengan nama field `camelCase`; Python dan database
  tetap menggunakan `snake_case`.
- **Transaction boundary:** service layer, bukan router.

Monolith dipilih karena domain masih terfokus pada katalog, RFQ, dan tracking. Modul tetap dipisahkan agar dapat diekstrak bila skala dan kebutuhan operasional meningkat.

## 3. Layering

```text
HTTP Request
    -> Router / Dependency
    -> Schema Validation
    -> Application Service
    -> CRUD / Repository
    -> SQLAlchemy Session
    -> PostgreSQL
```

### Konvensi Penamaan Antar-Layer

- **JSON API:** `camelCase`, misalnya `tonaseDiminta` dan `namaPerusahaan`.
- **Python internal:** `snake_case`, misalnya `tonase_diminta` dan
  `nama_perusahaan`.
- **Kolom database:** `snake_case`, misalnya `harga_per_ton`.
- **Class/type:** `PascalCase`, misalnya `RfqTransaction`.
- **Enum value:** `UPPER_SNAKE_CASE`, misalnya `ADMIN_GUDANG`.

Schema Pydantic menggunakan alias camelCase saat validasi dan serialisasi.
Karena itu frontend tidak perlu mengikuti nama field internal Python.

### Router

Router hanya menangani parsing request, dependency, status code, dan pemetaan response. Router tidak boleh menghitung harga, mengurangi stok, atau mengatur transisi status.

### Schema

Schema request dan response harus terpisah. Schema response tidak boleh mengekspos `hashed_password` atau detail internal persistence.
Nama field JSON mengikuti `camelCase`, sementara nama atribut Python tetap
`snake_case` melalui alias schema.

### Service

Service memiliki aturan lintas entity, terutama pembuatan dan persetujuan RFQ. Service mengatur transaksi, locking, dan rollback.

### CRUD/Repository

CRUD menangani query entity yang terisolasi. Query tidak boleh diam-diam melakukan perubahan pada entity lain.

### Model

Model SQLAlchemy hanya memuat mapping persistence, constraint database yang relevan, relationship, dan metadata.

## 4. Struktur Modul

```text
backend-mangga/
├── api/
│   ├── deps.py
│   └── routes/
├── core/
│   ├── config.py
│   └── security.py
├── crud/
├── db/
├── models/
├── schemas/
├── services/
├── tests/
└── main.py
```

Implementasi menggunakan package top-level (`api`, `core`, `crud`, `db`, `models`, `schemas`, dan `services`) ketika dijalankan dari folder `backend-mangga`. Jangan mencampurnya dengan prefix `app` pada import.

## 5. Dependency dan Konfigurasi

- `DATABASE_URL`, JWT secret, algorithm, expiry, dan `CORS_ORIGINS` hanya berasal dari environment/configuration.
- Jangan menaruh secret di source code, dokumentasi contoh, atau commit.
- Session database dibuat melalui dependency request-scoped dan selalu ditutup.
- `main.py` hanya membuat aplikasi, memasang middleware yang diperlukan, dan mendaftarkan router.

## 6. Konsistensi Transaksi

Persetujuan RFQ adalah satu unit kerja:

1. Lock RFQ dan inventaris terkait.
2. Validasi status dan saldo stok.
3. Kurangi stok.
4. Ubah status RFQ.
5. Tambahkan tracking pertama.
6. Commit.

Kegagalan pada langkah apa pun harus rollback seluruh unit kerja. Retry dan idempotency tidak boleh menghasilkan pengurangan stok kedua.

## 7. Kondisi Implementasi Saat Ini

[domain_models.py](<D:/faiz/Mangga Reang GTNIC/backend-mangga/models/domain_models.py>) sekarang menyediakan:

- enum domain;
- model `User`, `Inventory`, `RfqTransaction`, dan `LogisticsTracking`;
- relationship dan foreign key antar entity.

Alembic migration, constraint database, pagination, dan integration test
menjadi bagian dari hardening sebelum deployment production.
