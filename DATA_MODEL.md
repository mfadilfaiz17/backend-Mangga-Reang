# Data Model and Schema

## 1. Sumber Kebenaran

Kebutuhan entity berasal dari PRD. Dokumen ini menambahkan keputusan persistence, constraint, dan migrasi yang wajib dijaga oleh backend.

## 2. Entity

### Konvensi Nama

Nama tabel dan kolom database pada dokumen ini menggunakan `snake_case`.
Nama atribut Python juga menggunakan `snake_case`, sedangkan representasi
JSON API menggunakan `camelCase` melalui alias Pydantic. Jadi, misalnya,
kolom `nama_perusahaan` dikirim ke frontend sebagai `namaPerusahaan`.
Nama class menggunakan `PascalCase`, dan nilai enum menggunakan
`UPPER_SNAKE_CASE`.

### `users`

| Field | Tipe | Constraint |
|---|---|---|
| `id` | UUID atau Integer | primary key |
| `email` | String | unique, indexed, normalized |
| `hashed_password` | String | wajib, tidak boleh dikembalikan API |
| `nama_lengkap` | String | wajib |
| `role` | Enum | `ADMIN_GUDANG`, `PETANI`, `BUYER_B2B` |
| `nama_perusahaan` | String nullable | relevan untuk buyer |

### `mangga_inventaris`

| Field | Tipe | Constraint |
|---|---|---|
| `id` | Integer | primary key |
| `id_petani` | FK | `users.id` |
| `varietas` | Enum | `GEDONG_GINCU`, `CENGKIR`, `HARUMANIS` |
| `grade` | Enum | `GRADE_A`, `GRADE_B`, `GRADE_C` |
| `tonase_tersedia` | Numeric | `>= 0`, satuan ton |
| `harga_per_ton` | Numeric | `>= 0`, gunakan Decimal/Numeric |
| `lokasi_kebun` | String | wajib |
| `is_active` | Boolean | default `true` |

### `rfq_transactions`

| Field | Tipe | Constraint |
|---|---|---|
| `id` | Integer | primary key |
| `id_buyer` | FK | `users.id` |
| `id_mangga` | FK | `mangga_inventaris.id` |
| `tonase_diminta` | Numeric | `> 0` |
| `status_nego` | Enum | `PENDING`, `APPROVED`, `REJECTED`, `COMPLETED` |
| `total_harga` | Numeric | dihitung server |
| `tanggal_pesanan` | DateTime | timezone-aware |

### `logistik_tracking`

| Field | Tipe | Constraint |
|---|---|---|
| `id` | Integer | primary key |
| `id_rfq` | FK | `rfq_transactions.id` |
| `status_milestone` | Enum | `DIPROSES_PETANI`, `SORTIR_GUDANG`, `IN_TRANSIT`, `DELIVERED` |
| `catatan_qc` | String nullable | catatan operasional/QC |
| `updated_at` | DateTime | timezone-aware |
| `updated_by` | FK | `users.id` |

## 3. Relationship dan Index

- Satu user dapat memiliki banyak inventaris sebagai petani.
- Satu buyer dapat memiliki banyak RFQ.
- Satu inventaris dapat direferensikan banyak RFQ.
- Satu RFQ memiliki banyak tracking event.
- Index wajib: `users.email`, `mangga_inventaris.is_active`, `rfq_transactions.id_buyer`, `rfq_transactions.status_nego`, dan `logistik_tracking.id_rfq`.
- Foreign key wajib memiliki perilaku delete yang eksplisit. Jangan menghapus histori pesanan secara cascade tanpa keputusan bisnis.

## 4. Tipe Uang dan Waktu

- Gunakan `NUMERIC/Decimal`, bukan `Float`, untuk harga dan total.
- Gunakan timezone-aware UTC untuk timestamp.
- `total_harga` dihitung server dari `tonase_diminta * harga_per_ton` pada saat RFQ dibuat.
- Nilai yang diterima client tidak boleh menggantikan nilai kalkulasi server.

## 5. Migration Rules

- Gunakan Alembic sebagai migration tool; jangan membuat perubahan schema manual di production.
- Setiap perubahan entity harus memiliki migration dan rollback strategy.
- Constraint database yang aktif mencakup stok tidak negatif, harga tidak negatif,
  tonase RFQ positif, dan total harga tidak negatif.
- Data existing pada `Mangga` di [domain_models.py](<D:/faiz/Mangga Reang GTNIC/backend-mangga/models/domain_models.py>) harus dipetakan secara eksplisit sebelum rename `tonase` menjadi `tonase_tersedia`.
- Jangan mengklaim schema target sudah aktif sebelum migration berhasil dijalankan.

## 6. Pydantic Schema

Pisahkan minimal:

- `UserCreate`, `UserResponse`
- `LoginRequest`, `TokenResponse`
- `ManggaCreate`, `ManggaUpdate`, `ManggaResponse`
- `RFQCreate`, `RFQResponse`
- `TrackingCreate`, `TrackingResponse`

Schema response Pydantic v2 menggunakan `ConfigDict(from_attributes=True)`.

## 7. Menjalankan Migration

Dari root project pada database baru:

```powershell
python -m alembic upgrade head
```

Untuk database development lama yang sudah dibuat dengan `create_all()`, backup
terlebih dahulu, pastikan tabel sesuai initial schema, lalu adopsi dan terapkan
constraint:

```powershell
python -m alembic stamp 20261106_0001
python -m alembic upgrade head
```

Jangan menjalankan `upgrade head` pada database lama sebelum `stamp`, karena
initial migration akan mencoba membuat tabel yang sudah ada.
