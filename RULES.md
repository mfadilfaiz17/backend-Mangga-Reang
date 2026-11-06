# Backend Rules and Agent Guidelines

## 1. Aturan Prioritas

1. PRD menentukan scope dan kebutuhan bisnis.
2. Dokumen ini menentukan guardrail implementasi.
3. Kode dan test menjadi bukti perilaku aktual.
4. Jika dokumen bertentangan dengan kode, jangan menebak: identifikasi gap dan buat perubahan eksplisit.

## 2. Aturan Kode

- Gunakan type hints pada public function.
- Gunakan `snake_case` untuk variabel, fungsi, atribut Python, dan kolom
  database; gunakan `PascalCase` untuk class/type dan `UPPER_SNAKE_CASE` untuk
  nilai enum.
- Gunakan `camelCase` hanya pada kontrak JSON API. Gunakan alias schema agar
  casing API tidak memaksa perubahan pada nama internal Python/database.
- Gunakan dependency injection untuk session database dan current user.
- Jaga router tetap tipis.
- Jangan menaruh query database atau logika bisnis di `main.py`.
- Reuse enum dan helper; jangan membuat string status yang tersebar.
- Jangan menambahkan fallback sukses saat operasi gagal.
- Tangkap exception hanya bila dapat ditangani atau diterjemahkan secara tepat; log error internal tanpa membocorkan secret.

## 3. Aturan Data

- Semua input dari client divalidasi dengan Pydantic.
- Nilai role, status, harga, dan tonase tidak boleh dipercaya dari client.
- Field server-managed (`id`, status awal, total harga, timestamp, actor) ditentukan server.
- Jangan mengekspos `hashed_password`, JWT secret, connection string, atau stack trace.
- Query buyer harus selalu memakai identity dari token.
- Update inventory harus memeriksa ownership/role dan state saat ini.

## 4. Aturan Transaksi

- Approval RFQ wajib atomik.
- Gunakan row lock atau strategi concurrency yang setara saat stok dikurangi.
- Commit hanya setelah semua entity terkait valid.
- Rollback harus mengembalikan stok, status RFQ, dan tracking jika satu langkah gagal.
- Tambahkan test untuk dua approval bersamaan dan stok tidak mencukupi.

## 5. Aturan Perubahan

Sebelum mengubah kode:

1. Baca dokumen arsitektur yang relevan.
2. Cari implementasi existing dan test terkait.
3. Tentukan impact pada schema, API, security, dan migration.
4. Ubah sesedikit mungkin tetapi sampai invariant terpenuhi.
5. Jalankan test/lint/type check yang relevan.
6. Perbarui dokumentasi bila kontrak atau perilaku berubah.

Jangan menghapus perubahan workspace yang bukan bagian dari task. Jangan membuat dependency baru tanpa alasan dan perubahan manifest yang jelas.

## 6. Definition of Done

- [ ] Scope perubahan sesuai PRD.
- [ ] Authorization diuji untuk role yang boleh dan tidak boleh.
- [ ] Error status dan response konsisten.
- [ ] Tidak ada secret atau password di response/log.
- [ ] Migration tersedia untuk perubahan schema.
- [ ] Test mencakup happy path dan failure path.
- [ ] Dokumen API/schema diperbarui bila kontrak berubah.