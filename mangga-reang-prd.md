# Product Requirements Document (PRD)

## Juragan Mangga Reang

**Jenis produk:** Platform B2B e-commerce dan supply chain mangga
**Komponen:** Backend REST API
**Arsitektur:** Decoupled monolithic API
**Target pengguna:** Petani, buyer B2B, dan admin gudang
  
## 1. Tujuan Produk

Platform ini menghubungkan petani mangga dengan buyer B2B melalui katalog stok, pengajuan pembelian (RFQ), persetujuan pesanan, dan pelacakan milestone logistik.

Backend harus menyediakan:

1. Autentikasi dan otorisasi berbasis peran.
2. Katalog inventaris mangga yang dapat dilihat publik.
3. Alur pengajuan dan persetujuan pesanan B2B.
4. Pengurangan stok secara konsisten ketika pesanan disetujui.
5. Timeline traceability untuk setiap pesanan.

## 2. Ruang Lingkup

### 2.1 Termasuk dalam versi ini

- Registrasi dan login pengguna.
- Peran `ADMIN_GUDANG`, `PETANI`, dan `BUYER_B2B`.
- Manajemen stok mangga.
- Pembuatan dan persetujuan RFQ.
- Riwayat pesanan milik buyer.
- Daftar seluruh pesanan untuk admin gudang.
- Pencatatan dan pembaruan milestone logistik.
- PostgreSQL sebagai database utama.

### 2.2 Tidak termasuk dalam versi ini

- Pembayaran online, invoice, dan refund.
- Integrasi payment gateway.
- Integrasi kurir, GPS, atau pelacakan kendaraan secara real-time.
- Chat antara petani dan buyer.
- Notifikasi email, SMS, WhatsApp, atau push notification.
- Manajemen multi-gudang.
- Perhitungan pajak dan biaya pengiriman.
- Frontend, termasuk etalase 3D.

## 3. Batasan Teknis

- Python 3.10 atau lebih baru.
- FastAPI untuk REST API.
- SQLAlchemy sebagai ORM.
- Pydantic v2 untuk validasi dan serialisasi.
- PostgreSQL sebagai database.
- JWT Bearer untuk autentikasi.
- Password wajib di-hash menggunakan bcrypt melalui Passlib.
- Konvensi penamaan mengikuti batas layer: field JSON pada request/response
  menggunakan `camelCase` untuk kompatibilitas frontend; nama variabel,
  fungsi, field Pydantic internal, dan kolom database menggunakan `snake_case`.
  Nama class menggunakan `PascalCase`, sedangkan nilai enum menggunakan
  `UPPER_SNAKE_CASE`.
- Struktur kode mengikuti pola:
  - `app/api/`
  - `app/crud/`
  - `app/models/`
  - `app/schemas/`
  - `main.py`
hanya digunakan untuk inisialisasi aplikasi dan registrasi router; logika bisnis tidak boleh ditempatkan di sana.

## 4. Peran dan Hak Akses

| Peran | Hak akses utama |
|---|---|
| `ADMIN_GUDANG` | Melihat seluruh pesanan, mengelola stok, menyetujui RFQ, dan memperbarui milestone logistik |
| `PETANI` | Menambahkan stok panen dan memperbarui stok yang dikelolanya |
| `BUYER_B2B` | Melihat katalog, membuat RFQ, dan melihat riwayat pesanannya sendiri |

Kecuali endpoint autentikasi dan katalog publik, seluruh endpoint wajib menggunakan `Depends(get_current_user)` dan JWT Bearer.

## 5. Model Data

### 5.1 `users`

| Kolom | Tipe/aturan |
|---|---|
| `id` | UUID atau Integer, primary key |
| `email` | String, unique, indexed |
| `hashed_password` | String |
| `nama_lengkap` | String |
| `role` | Enum: `ADMIN_GUDANG`, `PETANI`, `BUYER_B2B` |
| `nama_perusahaan` | String nullable, digunakan oleh buyer |

### 5.2 `mangga_inventaris`

| Kolom | Tipe/aturan |
|---|---|
| `id` | Integer, primary key |
| `id_petani` | Foreign key ke `users.id` |
| `varietas` | Enum: `GEDONG_GINCU`, `CENGKIR`, `HARUMANIS` |
| `grade` | Enum: `GRADE_A`, `GRADE_B`, `GRADE_C` |
| `tonase_tersedia` | Float, satuan ton |
| `harga_per_ton` | Decimal atau Float |
| `lokasi_kebun` | String |
| `is_active` | Boolean, default `True` |

### 5.3 `rfq_transactions`

| Kolom | Tipe/aturan |
|---|---|
| `id` | Integer, primary key |
| `id_buyer` | Foreign key ke `users.id` |
| `id_mangga` | Foreign key ke `mangga_inventaris.id` |
| `tonase_diminta` | Float, harus lebih besar dari nol |
| `status_nego` | Enum: `PENDING`, `APPROVED`, `REJECTED`, `COMPLETED` |
| `total_harga` | Decimal atau Float |
| `tanggal_pesanan` | DateTime |

### 5.4 `logistik_tracking`

| Kolom | Tipe/aturan |
|---|---|
| `id` | Integer, primary key |
| `id_rfq` | Foreign key ke `rfq_transactions.id` |
| `status_milestone` | Enum: `DIPROSES_PETANI`, `SORTIR_GUDANG`, `IN_TRANSIT`, `DELIVERED` |
| `catatan_qc` | String nullable, misalnya hasil QC atau plat nomor truk |
| `updated_at` | DateTime |
| `updated_by` | Foreign key ke `users.id` |

## 6. Endpoint API

Prefix utama: `/api`

### 6.1 Auth — `/api/auth`

| Method | Path | Akses | Kebutuhan |
|---|---|---|---|
| `POST` | `/register` | Publik | Mendaftarkan user baru; password di-hash dengan bcrypt |
| `POST` | `/login` | Publik | Mengembalikan `{ "access_token": "...", "token_type": "bearer" }` |

Payload JWT wajib memuat `user_id` dan `role`.

### 6.2 Inventaris — `/api/mangga`

| Method | Path | Akses | Kebutuhan |
|---|---|---|---|
| `GET` | `/` | Publik | Hanya menampilkan `is_active=True` dan `tonase_tersedia > 0` |
| `POST` | `/` | Petani/Admin | Menambahkan stok panen |
| `PUT` | `/{id}` | Terautentikasi | Memperbarui tonase atau harga sesuai hak akses |

### 6.3 RFQ — `/api/rfq`

| Method | Path | Akses | Kebutuhan |
|---|---|---|---|
| `POST` | `/` | Buyer | `tonase_diminta` tidak boleh melebihi stok; status awal `PENDING` |
| `GET` | `/me` | Buyer | Hanya menampilkan pesanan milik user aktif |
| `GET` | `/all` | Admin | Menampilkan seluruh pesanan |
| `PUT` | `/{id}/approve` | Admin | Menyetujui RFQ, mengurangi stok, dan membuat tracking awal |

Persetujuan RFQ wajib dilakukan dalam satu transaksi database. Stok tidak boleh menjadi negatif dan RFQ yang sudah diproses tidak boleh disetujui ulang.

### 6.4 Logistik — `/api/logistik`

| Method | Path | Akses | Kebutuhan |
|---|---|---|---|
| `GET` | `/{id_rfq}` | Terautentikasi | Mengembalikan daftar timeline tracking |
| `POST` | `/{id_rfq}/update-status` | Admin | Menambahkan milestone baru beserta catatan |

## 7. Aturan Validasi dan Error

- Email harus valid dan tidak boleh duplikat.
- Password tidak boleh disimpan dalam bentuk plaintext.
- Nilai tonase dan harga harus valid serta tidak negatif.
- Foreign key harus mengarah ke data yang tersedia.
- User hanya boleh mengakses resource sesuai perannya.
- Gunakan HTTP status code yang sesuai (`400`, `401`, `403`, `404`, `409`, dan `422`).
- Error response harus konsisten dan tidak membocorkan password, secret, atau detail internal database.

## 8. Urutan Implementasi

1. Model SQLAlchemy dan konfigurasi database.
2. Enum domain dan skema Pydantic (`Create`, `Update`, dan `Response`).
3. Utilitas keamanan, hashing password, JWT, dan dependency autentikasi.
4. Fungsi database di `app/crud/`.
5. Service atau fungsi transaksi untuk aturan bisnis RFQ dan stok.
6. Router di `app/api/routes/`.
7. Registrasi router di `main.py`.
8. Test untuk autentikasi, otorisasi, validasi stok, dan transisi milestone.

Untuk Pydantic v2, response schema wajib menggunakan `ConfigDict(from_attributes=True)`.

## 9. Kriteria Penerimaan

- User dapat register dan login, serta menerima JWT yang valid.
- Endpoint publik hanya membuka katalog dan autentikasi.
- Endpoint yang membutuhkan login menolak request tanpa token atau dengan token tidak valid.
- Buyer tidak dapat membuat RFQ melebihi stok.
- Persetujuan RFQ mengurangi stok dan membuat tracking awal secara atomik.
- RFQ yang sama tidak dapat disetujui dua kali.
- Buyer hanya dapat melihat pesanannya sendiri.
- Admin dapat melihat seluruh pesanan dan mengubah milestone.
- Seluruh payload API menggunakan `camelCase`. Implementasi Python dan database
  tetap menggunakan `snake_case`; alias Pydantic menangani konversi di batas
  API. Contoh: JSON `tonaseDiminta` dipetakan ke field Python/database
  `tonase_diminta`.
