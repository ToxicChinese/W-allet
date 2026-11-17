# W-allet

Dompet digital sederhana untuk Proyek Tugas Pemrograman Web Framework (Python).
Dibuat dengan FastAPI, Jinja2, dan PostgreSQL. Saldo di aplikasi ini hanya simulasi,
tidak terhubung ke bank atau uang sungguhan.

## Kesesuaian dengan ketentuan tugas

| Ketentuan | Di aplikasi | Kode |
|---|---|---|
| Basis data | PostgreSQL, 5 tabel | `schema.sql`, `database.py` |
| Login, register, dashboard | Login dengan email, register, dashboard pengguna dan dashboard admin | `routers/auth_router.py`, `routers/dashboard_router.py` |
| File master | Pengguna, Kategori, Layanan, Metode Isi Saldo (tambah, lihat, ubah, hapus) | `routers/master_router.py` |
| File transaksi | Isi saldo, kirim saldo ke pengguna lain, bayar layanan | `routers/transaksi_router.py` |
| File report | Mutasi saldo, rekap per kategori, rekap per layanan, laporan pengguna | `routers/laporan_router.py` |
| Hosting gratis | Belum dilakukan, langkahnya ada di bagian akhir | |

## Menjalankan di laptop

### 1. Siapkan database

1. Buka pgAdmin, klik database `postgres`, buka Query Tool, lalu jalankan:

   ```sql
   CREATE DATABASE "db_w-allet";
   ```

   Tanda kutip dua wajib ditulis karena nama database memakai tanda hubung.

2. Klik database `db_w-allet`, buka Query Tool, buka file `schema.sql`, lalu jalankan semuanya (F5).

### 2. Siapkan project

Buka PowerShell di folder project ini, lalu:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Buka file `.env`, lalu ganti `admin` pada `DATABASE_URL` dengan password PostgreSQL di laptop.

### 3. Jalankan

```powershell
python -m uvicorn main:app --reload
```

Buka http://127.0.0.1:8000

## Akun bawaan

| Email | Password | Peran |
|---|---|---|
| admin@w-allet.test | admin123 | Admin |
| budi@w-allet.test | pengguna123 | Pengguna |
| siti@w-allet.test | pengguna123 | Pengguna |

Akun baru dari halaman Daftar selalu berperan sebagai pengguna.

## Siapa bisa apa

| Peran | Menu |
|---|---|
| Pengguna | Dashboard saldo, Isi Saldo, Kirim, Bayar, Laporan (data sendiri), Profil |
| Admin | Dashboard ringkasan, master Pengguna, Kategori, Layanan, Metode Isi Saldo, Laporan (semua pengguna), Profil |

Admin tidak punya saldo, jadi tidak bisa bertransaksi.

## Aturan transaksi

- Isi saldo: Rp 10.000 sampai Rp 2.000.000 per transaksi.
- Kirim saldo: Rp 1.000 sampai Rp 2.000.000, penerima dicari dari nomor HP, tanpa biaya admin.
- Bayar layanan: Rp 1.000 sampai Rp 2.000.000, saldo dipotong nominal ditambah biaya admin layanan.
- Saldo tidak bisa minus. Aturan ini dijaga di kode dan di database (`CHECK (saldo >= 0)`).
- Transaksi tidak bisa diubah atau dihapus, supaya riwayat saldo tetap utuh.
- Data master yang sudah dipakai transaksi tidak bisa dihapus, hanya dinonaktifkan.

Batas nominal bisa diubah di `BATAS` pada `routers/transaksi_router.py`.

## Struktur folder

```
W-allet/
├── main.py                  aplikasi FastAPI, session login, daftar router
├── database.py              koneksi PostgreSQL dan fungsi query
├── helper.py                template, pesan, password, cek login
├── schema.sql               tabel dan data awal
├── requirements.txt
├── .env.example             contoh isi file .env
├── routers/
│   ├── auth_router.py       login, register, logout, profil
│   ├── dashboard_router.py  dashboard pengguna dan admin
│   ├── transaksi_router.py  isi saldo, kirim, bayar
│   ├── master_router.py     CRUD data master (admin)
│   └── laporan_router.py    semua laporan
├── templates/               halaman HTML (Jinja2)
│   ├── admin/               halaman data master
│   └── laporan/             halaman laporan
└── static/
    ├── style.css            tampilan
    └── fonts/               font Plus Jakarta Sans dan lisensinya
```

## Hosting gratis (nanti)

Rencana: aplikasi di Render, database di Neon.

1. **Neon**: buat project baru, buka SQL Editor, tempel isi `schema.sql`, jalankan.
   Salin connection string yang diberikan Neon.
2. **GitHub**: unggah folder project ini ke sebuah repository. File `.env` dan folder `venv`
   tidak ikut terunggah karena sudah ada di `.gitignore`.
3. **Render**: buat Web Service dari repository itu, lalu isi:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment Variable `DATABASE_URL`: connection string dari Neon
   - Environment Variable `SECRET_KEY`: teks acak yang panjang
