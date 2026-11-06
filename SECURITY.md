# Backend Threat Model and Security

## 1. Scope dan Aset

### Aset yang harus dilindungi

- Kredensial dan password user.
- JWT secret dan token.
- Data perusahaan buyer.
- Stok, harga, dan lokasi kebun.
- Nilai RFQ dan histori supply chain.
- Integritas stok dan status transaksi.
- Availability API dan database.

### Trust boundary

```text
Client / Internet
    -> FastAPI edge
    -> Auth & authorization
    -> Application service
    -> Database
```

Semua data dari client dianggap tidak tepercaya, termasuk `role`, `id_buyer`, status, harga, dan tonase.

## 2. Ancaman dan Mitigasi

| Ancaman | Dampak | Mitigasi wajib |
|---|---|---|
| Password disimpan plaintext | Account takeover | bcrypt, response tidak memuat hash |
| JWT dipalsukan/di-replay | Akses tanpa izin | secret kuat dari environment, signature/expiry validation, rotasi secret |
| Buyer mengakses RFQ buyer lain | Kebocoran data | filter berdasarkan identity token di server |
| Buyer/Admin memalsukan role | Privilege escalation | role hanya dari database/token yang tervalidasi; jangan percaya body |
| Overselling karena race condition | Kerugian stok | transaction, row lock/conditional update, test concurrency |
| Approval berulang | Stok terpotong dua kali | validasi state `PENDING` dan constraint/idempotency |
| SQL injection | Kompromi database | SQLAlchemy parameter binding; hindari query string concatenation |
| Mass assignment | Perubahan field sensitif | schema update allowlist |
| Error terlalu detail | Information disclosure | response aman, log internal terkontrol |
| Secret masuk repository | Kompromi sistem | environment secret, secret scanning, review |
| Brute-force login | Account takeover/DoS | rate limiting, logging, lockout/backoff sesuai deployment |
| Payload besar/berulang | Resource exhaustion | body limit, pagination, timeout, rate limit |

## 3. Authentication Requirements

- Gunakan HTTPS pada deployment.
- JWT secret tidak boleh hardcoded.
- Tetapkan expiry yang pendek untuk access token; refresh token hanya jika menjadi requirement terpisah.
- Validasi algorithm secara allowlist, bukan menerima algorithm dari token.
- Jangan menaruh password atau secret di URL.
- Gunakan pesan login yang tidak membedakan user tidak ada dan password salah.

## 4. Authorization Matrix

| Resource/action | Publik | Buyer | Petani | Admin |
|---|---:|---:|---:|---:|
| Register/login | Ya | Ya | Ya | Ya |
| Lihat katalog aktif | Ya | Ya | Ya | Ya |
| Buat inventaris | Tidak | Tidak | Ya | Ya |
| Buat RFQ | Tidak | Ya | Tidak | Tidak |
| Lihat RFQ sendiri | Tidak | Ya | Tidak | Tidak |
| Lihat seluruh RFQ | Tidak | Tidak | Tidak | Ya |
| Approve RFQ | Tidak | Tidak | Tidak | Ya |
| Lihat tracking sesuai akses | Tidak | Ya | Tidak | Ya |
| Update milestone | Tidak | Tidak | Tidak | Ya |

## 5. Integrity Controls

- Database constraint untuk foreign key, enum, dan stok non-negatif.
- Audit actor melalui `updated_by`.
- Logging event security: login gagal, authorization denied, approval, dan perubahan milestone.
- Jangan log password, token utuh, connection string, atau data sensitif yang tidak diperlukan.
- Monitoring untuk lonjakan login gagal, `403`, `409` approval, dan error database.

## 6. Security Verification

Minimum test suite:

- token invalid, expired, missing, dan algorithm tidak diizinkan;
- tiap role terhadap tiap endpoint pada matrix;
- IDOR pada RFQ dan tracking;
- SQL injection pada parameter/filter;
- mass assignment pada status, harga, actor, dan owner;
- approval bersamaan dengan stok terbatas;
- rollback saat pembuatan tracking gagal;
- password tidak muncul dalam response dan log.

Security review bukan pengganti dependency scanning, secret scanning, migration review, dan hardening deployment.