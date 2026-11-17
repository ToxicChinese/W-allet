"""Fungsi bantu yang dipakai semua router: template, pesan, password, dan cek login."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from database import ambil_satu, get_db

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

NAMA_APLIKASI = "W-allet"
WIB = timezone(timedelta(hours=7))

LABEL_JENIS = {
    "topup": "Isi Saldo",
    "kirim": "Kirim Saldo",
    "terima": "Terima Saldo",
    "bayar": "Bayar Layanan",
}

# SELECT dasar untuk menampilkan transaksi lengkap dengan nama-namanya.
# Kolom masuk dan keluar dihitung di sini supaya HTML tinggal menampilkan.
SQL_TRANSAKSI = """
    SELECT t.id, t.waktu, t.jenis, t.nominal, t.biaya_admin, t.saldo_akhir,
           t.catatan, t.nomor_tujuan,
           p.nama AS nama_pengguna, m.nama_metode, l.nama_layanan, w.nama AS nama_lawan,
           CASE WHEN t.jenis IN ('topup', 'terima') THEN t.nominal ELSE 0 END AS masuk,
           CASE WHEN t.jenis IN ('kirim', 'bayar') THEN t.nominal + t.biaya_admin ELSE 0 END AS keluar
    FROM transaksi t
    JOIN pengguna p ON p.id = t.pengguna_id
    LEFT JOIN metode_topup m ON m.id = t.metode_id
    LEFT JOIN layanan l ON l.id = t.layanan_id
    LEFT JOIN pengguna w ON w.id = t.lawan_id
"""


# ---------- Waktu dan tampilan ----------

def sekarang():
    """Waktu saat ini dalam WIB, sama dengan isi kolom waktu di database."""
    return datetime.now(WIB).replace(tzinfo=None)


def rupiah(nilai):
    """150000 -> Rp 150.000"""
    return "Rp " + f"{nilai or 0:,.0f}".replace(",", ".")


def keterangan(t):
    """Kalimat singkat yang menjelaskan satu baris transaksi."""
    if t["jenis"] == "topup":
        teks = f"Isi saldo via {t['nama_metode']}"
    elif t["jenis"] == "kirim":
        teks = f"Kirim ke {t['nama_lawan']}"
    elif t["jenis"] == "terima":
        teks = f"Terima dari {t['nama_lawan']}"
    else:
        teks = t["nama_layanan"]
        if t["nomor_tujuan"]:
            teks += f" ({t['nomor_tujuan']})"
    if t["catatan"]:
        teks += f", {t['catatan']}"
    return teks


templates.env.filters["rupiah"] = rupiah
templates.env.filters["keterangan"] = keterangan
templates.env.filters["tanggal"] = lambda waktu: waktu.strftime("%d-%m-%Y %H:%M")
templates.env.filters["kode"] = lambda nomor: f"TRX-{nomor:06d}"
templates.env.globals.update(NAMA_APLIKASI=NAMA_APLIKASI, LABEL_JENIS=LABEL_JENIS)


def pesan(request, teks, tipe="sukses"):
    """Simpan pesan untuk ditampilkan satu kali di halaman berikutnya."""
    request.session["pesan"] = {"teks": teks, "tipe": tipe}


def render(request, nama_file, user=None, **data):
    """Tampilkan template. Data user dan pesan selalu ikut dikirim."""
    data["user"] = user
    data["pesan"] = request.session.pop("pesan", None)
    return templates.TemplateResponse(request=request, name=nama_file, context=data)


def alihkan(url):
    """Pindah halaman setelah form POST selesai diproses."""
    return RedirectResponse(url, status_code=303)


# ---------- Password ----------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def cek_password(password, hash_tersimpan):
    if len(password.encode()) > 72:  # batas panjang bcrypt
        return False
    return bcrypt.checkpw(password.encode(), hash_tersimpan.encode())


def periksa_password(password, ulangi):
    """Kembalikan teks kesalahan, atau None kalau password boleh dipakai."""
    if not 6 <= len(password) <= 50:
        return "Password harus 6 sampai 50 karakter."
    if password != ulangi:
        return "Ulangi password tidak sama."
    return None


# ---------- Cek login (dipasang di endpoint lewat Depends) ----------

class Alihkan(Exception):
    """Dilempar saat pengunjung harus dipindah ke halaman lain, misalnya belum login."""

    def __init__(self, url, teks=None):
        self.url = url
        self.teks = teks


def user_login(request: Request, db=Depends(get_db)):
    """Data pengguna yang sedang login. Kalau belum login, pindah ke halaman login."""
    user = None
    if request.session.get("user_id"):
        user = ambil_satu(
            db,
            "SELECT id, nama, email, no_hp, role, saldo FROM pengguna WHERE id = %s AND aktif",
            (request.session["user_id"],),
        )
    if not user:
        request.session.clear()
        raise Alihkan("/login")
    return user


def khusus_admin(user=Depends(user_login)):
    if user["role"] != "admin":
        raise Alihkan("/", "Halaman itu khusus admin.")
    return user


def khusus_pengguna(user=Depends(user_login)):
    if user["role"] != "pengguna":
        raise Alihkan("/", "Admin tidak punya saldo, jadi tidak bisa bertransaksi.")
    return user
