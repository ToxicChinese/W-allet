"""File report: mutasi, rekap per kategori, rekap per layanan, dan daftar pengguna.

Pengguna biasa hanya melihat datanya sendiri. Admin melihat data semua pengguna.
Semua laporan bisa dicetak atau disimpan sebagai PDF lewat tombol Cetak.
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request

from database import ambil_semua, get_db
from helper import LABEL_JENIS, SQL_TRANSAKSI, khusus_admin, render, sekarang, user_login

router = APIRouter(prefix="/laporan")


def baca_periode(dari, sampai):
    """Ubah teks tanggal dari form menjadi date. Kalau kosong: awal bulan ini s.d. hari ini."""
    hari_ini = sekarang().date()
    try:
        tgl_dari = date.fromisoformat(dari)
    except ValueError:
        tgl_dari = hari_ini.replace(day=1)
    try:
        tgl_sampai = date.fromisoformat(sampai)
    except ValueError:
        tgl_sampai = hari_ini
    return tgl_dari, tgl_sampai


@router.get("")
def menu_laporan(request: Request, user=Depends(user_login)):
    return render(request, "laporan/menu.html", user)


@router.get("/mutasi")
def laporan_mutasi(
    request: Request,
    dari: str = "",
    sampai: str = "",
    jenis: str = "",
    user=Depends(user_login),
    db=Depends(get_db),
):
    tgl_dari, tgl_sampai = baca_periode(dari, sampai)

    # Syarat WHERE disusun bertahap sesuai filter yang dipilih.
    syarat = ["t.waktu >= %s", "t.waktu < %s"]
    params = [tgl_dari, tgl_sampai + timedelta(days=1)]
    if user["role"] == "pengguna":
        syarat.append("t.pengguna_id = %s")
        params.append(user["id"])
    if jenis in LABEL_JENIS:
        syarat.append("t.jenis = %s")
        params.append(jenis)

    data = ambil_semua(
        db,
        SQL_TRANSAKSI + " WHERE " + " AND ".join(syarat) + " ORDER BY t.waktu DESC, t.id DESC",
        params,
    )
    return render(
        request, "laporan/mutasi.html", user,
        data=data, dari=tgl_dari, sampai=tgl_sampai, jenis=jenis,
        total_masuk=sum(t["masuk"] for t in data),
        total_keluar=sum(t["keluar"] for t in data),
    )


@router.get("/kategori")
def rekap_kategori(
    request: Request,
    dari: str = "",
    sampai: str = "",
    user=Depends(user_login),
    db=Depends(get_db),
):
    tgl_dari, tgl_sampai = baca_periode(dari, sampai)

    syarat = ["t.waktu >= %s", "t.waktu < %s"]
    params = [tgl_dari, tgl_sampai + timedelta(days=1)]
    if user["role"] == "pengguna":
        syarat.append("t.pengguna_id = %s")
        params.append(user["id"])

    data = ambil_semua(
        db,
        """
        SELECT k.nama_kategori AS nama,
               COUNT(*) AS jumlah,
               SUM(t.nominal) AS nominal,
               SUM(t.biaya_admin) AS biaya_admin,
               SUM(t.nominal + t.biaya_admin) AS total
        FROM transaksi t
        JOIN layanan l ON l.id = t.layanan_id
        JOIN kategori k ON k.id = l.kategori_id
        WHERE """ + " AND ".join(syarat) + """
        GROUP BY k.nama_kategori
        ORDER BY total DESC
        """,
        params,
    )
    return render(
        request, "laporan/rekap.html", user,
        judul="Rekap Pengeluaran per Kategori", kolom="Kategori", alamat="/laporan/kategori",
        data=data, dari=tgl_dari, sampai=tgl_sampai,
    )


@router.get("/layanan")
def rekap_layanan(
    request: Request,
    dari: str = "",
    sampai: str = "",
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    tgl_dari, tgl_sampai = baca_periode(dari, sampai)
    data = ambil_semua(
        db,
        """
        SELECT l.nama_layanan AS nama,
               COUNT(*) AS jumlah,
               SUM(t.nominal) AS nominal,
               SUM(t.biaya_admin) AS biaya_admin,
               SUM(t.nominal + t.biaya_admin) AS total
        FROM transaksi t
        JOIN layanan l ON l.id = t.layanan_id
        WHERE t.waktu >= %s AND t.waktu < %s
        GROUP BY l.nama_layanan
        ORDER BY total DESC
        """,
        (tgl_dari, tgl_sampai + timedelta(days=1)),
    )
    return render(
        request, "laporan/rekap.html", admin,
        judul="Rekap Transaksi per Layanan", kolom="Layanan", alamat="/laporan/layanan",
        data=data, dari=tgl_dari, sampai=tgl_sampai,
    )


@router.get("/pengguna")
def laporan_pengguna(request: Request, admin=Depends(khusus_admin), db=Depends(get_db)):
    data = ambil_semua(
        db,
        """
        SELECT p.nama, p.email, p.no_hp, p.saldo, p.aktif, p.dibuat_pada,
               COUNT(t.id) AS jumlah_transaksi
        FROM pengguna p
        LEFT JOIN transaksi t ON t.pengguna_id = p.id
        WHERE p.role = 'pengguna'
        GROUP BY p.id
        ORDER BY p.nama
        """,
    )
    return render(
        request, "laporan/pengguna.html", admin,
        data=data, total_saldo=sum(p["saldo"] for p in data), dicetak=sekarang(),
    )
