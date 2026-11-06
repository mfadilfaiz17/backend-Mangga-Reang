# Backend Roadmap

Dokumen ini digunakan untuk memantau progres pekerjaan backend Mangga Reang.
Status diubah ketika pekerjaan benar-benar sudah diverifikasi.

## Status

- `[x]` Selesai dan sudah diverifikasi
- `[-]` Sedang dikerjakan
- `[ ]` Belum dikerjakan
- `[~]` Ditunda atau menunggu keputusan

## Selesai

- [x] Menetapkan scope produk pada PRD.
- [x] Memisahkan dokumentasi arsitektur, data model, API, rules, dan security.
- [x] Menyiapkan struktur package backend.
- [x] Menyiapkan konfigurasi environment dan `.gitignore`.
- [x] Menghubungkan backend ke PostgreSQL lokal.
- [x] Membuat model user, inventaris, RFQ, dan tracking.
- [x] Menambahkan register dan login.
- [x] Menambahkan password hashing dengan bcrypt.
- [x] Menambahkan JWT Bearer authentication.
- [x] Menambahkan role authorization untuk buyer, petani, dan admin.
- [x] Menambahkan alias JSON `camelCase`.
- [x] Menambahkan endpoint inventaris.
- [x] Menambahkan endpoint RFQ.
- [x] Menambahkan endpoint tracking logistik.
- [x] Menambahkan approval RFQ dengan transaksi dan row lock.
- [x] Menjalankan backend melalui Uvicorn.
- [x] Memverifikasi Swagger UI pada `/docs`.
- [x] Memverifikasi register melalui PostgreSQL dengan response `201 Created`.

## Tahap Berikutnya

### 1. Pengujian Otomatis

- [x] Menyiapkan framework dan konfigurasi test.
- [x] Test register dan login.
- [x] Test password salah dan token tidak valid.
- [x] Test authorization setiap role.
- [x] Test pembuatan dan pembaruan inventaris.
- [x] Test pembuatan RFQ dan validasi stok.
- [x] Test buyer hanya melihat RFQ miliknya.
- [x] Test approval RFQ dan pengurangan stok.
- [x] Test approval ganda dan stok tidak mencukupi.
- [x] Test akses tracking dan isolasi data buyer.
- [x] Test rollback ketika proses transaksi gagal.
- [ ] Test approval bersamaan dengan stok terbatas pada PostgreSQL.

### 2. Database dan Migration

- [x] Menambahkan Alembic.
- [x] Membuat initial migration.
- [x] Menambahkan prosedur upgrade dan downgrade.
- [x] Menguji migration pada database kosong.
- [x] Menambahkan constraint non-negatif dan constraint tonase RFQ.
- [ ] Menghapus ketergantungan development pada `create_all()` setelah migration siap.

### 3. Admin Development

- [x] Membuat provisioning admin secara terkontrol untuk development.
- [x] Menolak pembuatan admin melalui register publik.
- [x] Menguji endpoint admin dengan akun hasil provisioning.
- [x] Mendokumentasikan prosedur admin pada README.

### 4. API Hardening

- [ ] Menyamakan seluruh error response.
- [x] Menambahkan pagination untuk endpoint collection.
- [ ] Menambahkan filter yang diperlukan pada daftar RFQ dan inventaris.
- [x] Memastikan response tidak membocorkan stack trace atau data sensitif.
- [x] Memeriksa konfigurasi CORS sesuai environment.

### 5. Security Verification

- [x] Menguji token hilang, invalid, expired, dan algorithm yang tidak diizinkan.
- [ ] Menguji IDOR pada RFQ dan tracking.
- [ ] Menguji mass assignment pada status, harga, actor, dan owner.
- [ ] Menguji SQL injection pada parameter dan filter.
- [x] Menambahkan logging untuk login gagal dan authorization denied.
- [ ] Menambahkan rate limiting login sesuai kebutuhan deployment.

## Backlog

- [x] Menambahkan observability dan health check database.
- [ ] Menambahkan dependency dan secret scanning pada CI.
- [ ] Menambahkan integration test dengan PostgreSQL terisolasi.
- [ ] Menyiapkan konfigurasi deployment.
- [ ] Menyusun API client atau collection untuk pengujian berulang.

## Ditunda

- [~] Menentukan tombol dan layout frontend.
- [~] Menentukan dashboard buyer, petani, dan admin.
- [~] Integrasi payment gateway.
- [~] Integrasi kurir atau GPS real-time.
- [~] Notifikasi email, SMS, WhatsApp, atau push notification.

## Aturan Pembaruan Roadmap

1. Tandai `[x]` hanya setelah pekerjaan berhasil diuji atau diverifikasi.
2. Tambahkan detail endpoint, schema, dan aturan kontrak ke dokumen teknis terkait.
3. Perbarui [README.md](./README.md) jika cara instalasi atau menjalankan backend berubah.
4. Jangan memasukkan rancangan tombol frontend sebelum kebutuhan frontend disepakati.
5. Pekerjaan production tidak dianggap selesai hanya karena berhasil di development.