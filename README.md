# Backend Juragan Mangga Reang

Backend REST API untuk platform B2B supply chain mangga. Backend ini menjadi penghubung antara petani, buyer B2B, dan admin gudang untuk mengelola inventaris, pengajuan pembelian, persetujuan pesanan, dan status logistik.

## Status Implementasi

Fondasi proyek saat ini sudah menyediakan:

- konfigurasi aplikasi berbasis environment;
- dependency FastAPI, SQLAlchemy, PostgreSQL, Pydantic Settings, JWT, dan bcrypt;
- koneksi database SQLAlchemy;
- model awal `Mangga` untuk tabel `mangga_inventaris`.

Fitur yang masih perlu diimplementasikan secara bertahap:

- model user dan role;
- autentikasi register/login;
- dependency JWT dan role authorization;
- schema request/response;
- CRUD inventaris, RFQ, dan tracking;
- transaksi persetujuan RFQ yang atomik;
- router API dan integration test.

README ini menjelaskan cara menjalankan backend dan batas kondisi implementasi saat ini. Detail kontrak endpoint, model data, aturan engineering, arsitektur, dan keamanan dikelola pada dokumen teknis terpisah.

## Teknologi

- Python 3.10+
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- Pydantic Settings
- `python-jose` untuk JWT
- Passlib dan bcrypt untuk password hashing

## Struktur Saat Ini

```text
backend-mangga/
├── core/
│   └── config.py
└── models/
    └── domain_models.py
```

`domain_models.py` saat ini masih mengimpor konfigurasi melalui `app.core.config`. Pastikan package dijalankan dari struktur package yang menyediakan import `app`, atau sesuaikan import ketika struktur aplikasi final dibentuk.

## Persiapan Lokal

### 1. Buat virtual environment

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependency

```powershell
python -m pip install -r requirements.txt
```

### 3. Siapkan environment

Salin `.env.example` menjadi `.env`, kemudian isi:

- `DATABASE_URL` dengan kredensial PostgreSQL lokal;
- `SECRET_KEY` dengan nilai acak yang panjang;
- `ACCESS_TOKEN_EXPIRE_MINUTES` sesuai kebutuhan environment.

File `.env` diabaikan Git dan tidak boleh di-commit. Nilai pada `.env.example` hanya template dan bukan kredensial aktif.

### 4. Siapkan database

Buat database PostgreSQL bernama `mangga_db` atau sesuaikan nama database pada `DATABASE_URL`. Migration dan bootstrap tabel belum tersedia pada kondisi implementasi saat ini, sehingga jangan menganggap seluruh tabel domain sudah otomatis dibuat.

## Menjalankan API

Entry point FastAPI belum tersedia pada kondisi saat ini. Setelah `main.py` dibuat, jalankan dari root proyek dengan:

```powershell
python -m uvicorn app.main:app --reload
```

Jika entry point menggunakan lokasi berbeda, sesuaikan module path pada perintah Uvicorn.

## Alur Backend

Target alur bisnis backend:

1. User melakukan register dan login.
2. Buyer melihat inventaris mangga aktif dengan stok positif.
3. Buyer membuat RFQ dengan tonase yang tersedia.
4. Admin gudang menyetujui RFQ.
5. Sistem mengurangi stok dan membuat tracking awal.
6. Admin memperbarui milestone hingga pesanan selesai.

Approval RFQ harus diproses sebagai satu transaksi database agar stok tidak negatif dan tidak terpotong dua kali ketika terdapat request bersamaan.

## Environment Variables

| Variable | Kegunaan |
|---|---|
| `PROJECT_NAME` | Nama aplikasi |
| `VERSION` | Versi API |
| `DATABASE_URL` | Connection string PostgreSQL |
| `SECRET_KEY` | Secret untuk signing JWT |
| `ALGORITHM` | Algoritma JWT, default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Masa berlaku access token |

Jangan menaruh password, JWT secret, access token, atau connection string production di repository, log, issue, atau dokumentasi.

## Pemeriksaan Sebelum Pull Request

- Pastikan `.env` tidak muncul dalam staged changes.
- Jalankan test dan type check yang tersedia.
- Pastikan tidak ada secret di source code atau log.
- Pastikan perubahan database memiliki migration.
- Pastikan endpoint privat memvalidasi token dan role.
- Pastikan perubahan stok memiliki test untuk kondisi race dan rollback.
