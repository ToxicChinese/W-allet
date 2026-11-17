"""Koneksi ke PostgreSQL memakai psycopg2 dan SQL biasa (pola Praktek 6)."""
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()  # membaca file .env kalau ada

# Di laptop: isi lewat file .env. Di hosting: isi lewat Environment Variable.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:admin@localhost:5432/db_w-allet",
)


def get_db():
    """Satu koneksi untuk satu request, ditutup otomatis setelah request selesai.

    Perubahan data baru tersimpan kalau endpoint memanggil db.commit().
    Kalau terjadi error sebelum commit, semua perubahan dibatalkan.
    """
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def ambil_semua(db, sql, params=()):
    """SELECT banyak baris. Hasilnya list of dict, jadi di HTML ditulis {{ baris.nama }}."""
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def ambil_satu(db, sql, params=()):
    """SELECT satu baris. Hasilnya dict, atau None kalau tidak ada."""
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def jalankan(db, sql, params=()):
    """INSERT, UPDATE, atau DELETE. Kalau SQL-nya memakai RETURNING, barisnya dikembalikan."""
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None
