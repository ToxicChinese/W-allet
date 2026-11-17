-- =====================================================================
-- W-allet : skema database PostgreSQL
-- Proyek Tugas Pemrograman Web Framework (Python)
--
-- Cara pakai di pgAdmin:
--   1. Klik database "postgres" > Query Tool, lalu jalankan:
--          CREATE DATABASE "db_w-allet";
--   2. Klik database "db_w-allet" > Query Tool,
--      buka file ini, lalu jalankan semuanya (F5).
--
-- File ini boleh dijalankan ulang. Semua tabel dihapus lalu dibuat lagi,
-- jadi data lama ikut hilang.
--
-- Akun bawaan setelah file ini dijalankan:
--   admin@w-allet.test  / admin123     (admin)
--   budi@w-allet.test   / pengguna123  (pengguna)
--   siti@w-allet.test   / pengguna123  (pengguna)
-- =====================================================================

DROP TABLE IF EXISTS transaksi, layanan, metode_topup, kategori, pengguna CASCADE;


-- =====================================================================
-- FILE MASTER
-- =====================================================================

-- Pengguna aplikasi. Kolom saldo ikut berubah setiap ada transaksi.
CREATE TABLE pengguna (
    id          SERIAL PRIMARY KEY,
    nama        VARCHAR(100)  NOT NULL,
    email       VARCHAR(100)  NOT NULL UNIQUE,
    no_hp       VARCHAR(15)   NOT NULL UNIQUE,
    password    VARCHAR(255)  NOT NULL,              -- hash bcrypt, bukan teks asli
    role        VARCHAR(10)   NOT NULL DEFAULT 'pengguna'
                CHECK (role IN ('admin', 'pengguna')),
    saldo       NUMERIC(14,2) NOT NULL DEFAULT 0
                CHECK (saldo >= 0),                  -- saldo tidak boleh minus
    aktif       BOOLEAN       NOT NULL DEFAULT TRUE,
    dibuat_pada TIMESTAMP     NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta')
);

-- Kategori layanan, dipakai untuk rekap pengeluaran.
CREATE TABLE kategori (
    id            SERIAL PRIMARY KEY,
    nama_kategori VARCHAR(50)  NOT NULL UNIQUE,
    deskripsi     VARCHAR(200)
);

-- Layanan yang bisa dibayar dengan saldo.
CREATE TABLE layanan (
    id           SERIAL PRIMARY KEY,
    nama_layanan VARCHAR(100)  NOT NULL UNIQUE,
    kategori_id  INTEGER       NOT NULL REFERENCES kategori(id),
    biaya_admin  NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (biaya_admin >= 0),
    aktif        BOOLEAN       NOT NULL DEFAULT TRUE
);

-- Cara mengisi saldo.
CREATE TABLE metode_topup (
    id          SERIAL PRIMARY KEY,
    nama_metode VARCHAR(50)  NOT NULL UNIQUE,
    keterangan  VARCHAR(200),
    aktif       BOOLEAN      NOT NULL DEFAULT TRUE
);


-- =====================================================================
-- FILE TRANSAKSI
-- =====================================================================

-- Satu baris = satu perubahan saldo milik satu pengguna.
--   topup  : isi saldo            (metode_id terisi)
--   kirim  : kirim ke pengguna    (lawan_id = penerima)
--   terima : terima dari pengguna (lawan_id = pengirim)
--   bayar  : bayar layanan        (layanan_id terisi)
-- Kirim saldo menghasilkan dua baris: "kirim" di pengirim, "terima" di penerima.
CREATE TABLE transaksi (
    id           SERIAL PRIMARY KEY,
    pengguna_id  INTEGER       NOT NULL REFERENCES pengguna(id),
    jenis        VARCHAR(10)   NOT NULL
                 CHECK (jenis IN ('topup', 'kirim', 'terima', 'bayar')),
    metode_id    INTEGER       REFERENCES metode_topup(id),
    layanan_id   INTEGER       REFERENCES layanan(id),
    lawan_id     INTEGER       REFERENCES pengguna(id),
    nomor_tujuan VARCHAR(30),                        -- nomor HP atau ID pelanggan
    nominal      NUMERIC(14,2) NOT NULL CHECK (nominal > 0),
    biaya_admin  NUMERIC(12,2) NOT NULL DEFAULT 0,
    saldo_akhir  NUMERIC(14,2) NOT NULL,             -- saldo setelah transaksi ini
    catatan      VARCHAR(100),
    waktu        TIMESTAMP     NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta')
);

CREATE INDEX idx_transaksi_pengguna ON transaksi (pengguna_id, waktu DESC);


-- =====================================================================
-- DATA AWAL
-- =====================================================================

INSERT INTO kategori (nama_kategori, deskripsi) VALUES
    ('Pulsa dan Data',      'Pulsa prabayar dan paket internet'),
    ('Listrik',             'Token dan tagihan listrik'),
    ('Air',                 'Tagihan air bulanan'),
    ('Internet',            'Tagihan internet rumah atau kos'),
    ('Makanan dan Minuman', 'Kantin dan tempat makan'),
    ('Belanja',             'Kebutuhan kuliah dan harian'),
    ('Transportasi',        'Parkir dan angkutan');

INSERT INTO layanan (nama_layanan, kategori_id, biaya_admin) VALUES
    ('Pulsa Prabayar',     1, 1500),
    ('Paket Data',         1, 1500),
    ('Token Listrik',      2, 2500),
    ('Tagihan Listrik',    2, 2500),
    ('Tagihan Air',        3, 2500),
    ('Internet Rumah',     4, 2500),
    ('Kantin Kampus',      5, 0),
    ('Fotokopi dan Cetak', 6, 0),
    ('Koperasi Mahasiswa', 6, 0),
    ('Parkir Kampus',      7, 0);

INSERT INTO metode_topup (nama_metode, keterangan) VALUES
    ('Transfer Bank', 'Transfer dari rekening bank ke nomor akun'),
    ('Minimarket',    'Bayar tunai di kasir minimarket'),
    ('Kartu Debit',   'Potong langsung dari kartu debit');

-- Password disimpan sebagai hash bcrypt (lihat daftar akun di bagian atas file).
INSERT INTO pengguna (nama, email, no_hp, password, role, saldo, dibuat_pada) VALUES
    ('Admin W-allet',   'admin@w-allet.test', '080000000000',
     '$2b$12$2a4Z0GoP0U31imwnbIOXc.0PUnfeBweWtglVeKbOmVQtSTZIozfd2', 'admin', 0,
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '30 days'),
    ('Budi Santoso', 'budi@w-allet.test',  '081200000001',
     '$2b$12$RMfCvqOsnNq1yXj4qGhTu.oQDZHYPCsJEwsRFwfQuUfjciEuoMlKa', 'pengguna', 241000,
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '12 days'),
    ('Siti Aminah',  'siti@w-allet.test',  '081200000002',
     '$2b$12$RMfCvqOsnNq1yXj4qGhTu.oQDZHYPCsJEwsRFwfQuUfjciEuoMlKa', 'pengguna', 288500,
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '11 days');

-- Contoh transaksi supaya dashboard dan laporan langsung berisi.
-- Saldo akhir tiap baris sudah dihitung dan cocok dengan kolom saldo di atas.
INSERT INTO transaksi
    (pengguna_id, jenis, metode_id, layanan_id, lawan_id, nomor_tujuan,
     nominal, biaya_admin, saldo_akhir, catatan, waktu)
VALUES
    (2, 'topup',  1,    NULL, NULL, NULL,           500000, 0,    500000, NULL,
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '10 days'),
    (3, 'topup',  2,    NULL, NULL, NULL,           300000, 0,    300000, NULL,
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '9 days'),
    (2, 'bayar',  NULL, 1,    NULL, '081200000001', 50000,  1500, 448500, NULL,
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '8 days'),
    (2, 'kirim',  NULL, NULL, 3,    NULL,           100000, 0,    348500, 'Patungan makan',
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '6 days'),
    (3, 'terima', NULL, NULL, 2,    NULL,           100000, 0,    400000, 'Patungan makan',
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '6 days'),
    (3, 'bayar',  NULL, 2,    NULL, '081200000002', 75000,  1500, 323500, NULL,
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '5 days'),
    (2, 'bayar',  NULL, 3,    NULL, '520011223344', 100000, 2500, 246000, 'Listrik kos',
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '4 days'),
    (3, 'bayar',  NULL, 8,    NULL, NULL,           15000,  0,    308500, 'Cetak makalah',
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '3 days'),
    (2, 'bayar',  NULL, 7,    NULL, NULL,           25000,  0,    221000, 'Makan siang',
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '2 days'),
    (3, 'kirim',  NULL, NULL, 2,    NULL,           20000,  0,    288500, 'Ganti uang parkir',
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '1 day'),
    (2, 'terima', NULL, NULL, 3,    NULL,           20000,  0,    241000, 'Ganti uang parkir',
     (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '1 day');
