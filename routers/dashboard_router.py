"""Dashboard. Isinya berbeda untuk pengguna dan admin."""
from fastapi import APIRouter, Depends, Request

from database import ambil_satu, ambil_semua, get_db
from helper import SQL_TRANSAKSI, render, sekarang, user_login

router = APIRouter()


@router.get("/")
def dashboard(request: Request, user=Depends(user_login), db=Depends(get_db)):
    hari_ini = sekarang().replace(hour=0, minute=0, second=0, microsecond=0)
    awal_bulan = hari_ini.replace(day=1)

    if user["role"] == "admin":
        # Kirim saldo tercatat dua baris (kirim dan terima), jadi baris "terima"
        # tidak ikut dihitung supaya satu transfer tidak terhitung dua kali.
        angka = ambil_satu(
            db,
            """
            SELECT
              (SELECT COUNT(*) FROM pengguna WHERE role = 'pengguna' AND aktif) AS jumlah_pengguna,
              (SELECT COALESCE(SUM(saldo), 0) FROM pengguna WHERE role = 'pengguna') AS total_saldo,
              (SELECT COUNT(*) FROM transaksi
                WHERE jenis <> 'terima' AND waktu >= %s) AS transaksi_hari_ini,
              (SELECT COALESCE(SUM(nominal), 0) FROM transaksi
                WHERE jenis <> 'terima' AND waktu >= %s) AS nilai_bulan_ini,
              (SELECT COALESCE(SUM(biaya_admin), 0) FROM transaksi
                WHERE waktu >= %s) AS biaya_admin_bulan_ini
            """,
            (hari_ini, awal_bulan, awal_bulan),
        )
        terlaris = ambil_semua(
            db,
            """
            SELECT l.nama_layanan, COUNT(*) AS jumlah, SUM(t.nominal) AS total
            FROM transaksi t
            JOIN layanan l ON l.id = t.layanan_id
            WHERE t.waktu >= %s
            GROUP BY l.nama_layanan
            ORDER BY jumlah DESC, total DESC
            LIMIT 5
            """,
            (awal_bulan,),
        )
        terbaru = ambil_semua(
            db,
            SQL_TRANSAKSI + " WHERE t.jenis <> 'terima' ORDER BY t.waktu DESC, t.id DESC LIMIT 8",
        )
        return render(
            request, "dashboard_admin.html", user,
            angka=angka, terlaris=terlaris, terbaru=terbaru,
        )

    ringkasan = ambil_satu(
        db,
        """
        SELECT
          COALESCE(SUM(nominal) FILTER (WHERE jenis IN ('topup', 'terima')), 0) AS masuk,
          COALESCE(SUM(nominal + biaya_admin) FILTER (WHERE jenis IN ('kirim', 'bayar')), 0) AS keluar
        FROM transaksi
        WHERE pengguna_id = %s AND waktu >= %s
        """,
        (user["id"], awal_bulan),
    )
    per_kategori = ambil_semua(
        db,
        """
        SELECT k.nama_kategori, SUM(t.nominal + t.biaya_admin) AS total
        FROM transaksi t
        JOIN layanan l ON l.id = t.layanan_id
        JOIN kategori k ON k.id = l.kategori_id
        WHERE t.pengguna_id = %s AND t.waktu >= %s
        GROUP BY k.nama_kategori
        ORDER BY total DESC
        """,
        (user["id"], awal_bulan),
    )
    # Panjang batang grafik: kategori terbesar = 100 persen.
    for baris in per_kategori:
        baris["persen"] = int(baris["total"] / per_kategori[0]["total"] * 100)

    terbaru = ambil_semua(
        db,
        SQL_TRANSAKSI + " WHERE t.pengguna_id = %s ORDER BY t.waktu DESC, t.id DESC LIMIT 5",
        (user["id"],),
    )
    return render(
        request, "dashboard.html", user,
        ringkasan=ringkasan, per_kategori=per_kategori, terbaru=terbaru,
    )
