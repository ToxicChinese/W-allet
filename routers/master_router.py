"""File master (khusus admin): kategori, layanan, metode isi saldo, dan pengguna."""
from fastapi import APIRouter, Depends, Form, Request
from psycopg2.errors import ForeignKeyViolation, UniqueViolation

from database import ambil_satu, ambil_semua, get_db, jalankan
from helper import Alihkan, alihkan, khusus_admin, pesan, render

router = APIRouter(prefix="/admin")


def simpan(request, db, sql, params, url):
    """Jalankan INSERT atau UPDATE data master, lalu kembali ke halaman daftar."""
    try:
        jalankan(db, sql, params)
        db.commit()
        pesan(request, "Data berhasil disimpan.")
    except UniqueViolation:
        db.rollback()
        pesan(request, "Gagal disimpan: nama, email, atau nomor itu sudah dipakai.", "gagal")
    return alihkan(url)


def hapus(request, db, tabel, id, url):
    """Hapus satu baris data master. Ditolak kalau datanya masih dipakai tabel lain."""
    try:
        jalankan(db, f"DELETE FROM {tabel} WHERE id = %s", (id,))
        db.commit()
        pesan(request, "Data berhasil dihapus.")
    except ForeignKeyViolation:
        db.rollback()
        pesan(
            request,
            "Tidak bisa dihapus karena sudah dipakai di data lain. Nonaktifkan saja.",
            "gagal",
        )
    return alihkan(url)


def cari(db, tabel, id, url):
    """Ambil satu baris untuk form edit. Kalau tidak ada, kembali ke halaman daftar."""
    baris = ambil_satu(db, f"SELECT * FROM {tabel} WHERE id = %s", (id,))
    if not baris:
        raise Alihkan(url, "Data tidak ditemukan.")
    return baris


# ---------- Kategori ----------

@router.get("/kategori")
def daftar_kategori(request: Request, admin=Depends(khusus_admin), db=Depends(get_db)):
    data = ambil_semua(
        db,
        """
        SELECT k.*, COUNT(l.id) AS jumlah_layanan
        FROM kategori k
        LEFT JOIN layanan l ON l.kategori_id = k.id
        GROUP BY k.id
        ORDER BY k.nama_kategori
        """,
    )
    return render(request, "admin/kategori.html", admin, data=data)


@router.get("/kategori/tambah")
def form_tambah_kategori(request: Request, admin=Depends(khusus_admin)):
    return render(request, "admin/kategori_form.html", admin, item=None)


@router.post("/kategori/tambah")
def tambah_kategori(
    request: Request,
    nama_kategori: str = Form(...),
    deskripsi: str = Form(""),
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    return simpan(
        request, db,
        "INSERT INTO kategori (nama_kategori, deskripsi) VALUES (%s, %s)",
        (nama_kategori.strip(), deskripsi.strip()),
        "/admin/kategori",
    )


@router.get("/kategori/{id}/edit")
def form_edit_kategori(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    item = cari(db, "kategori", id, "/admin/kategori")
    return render(request, "admin/kategori_form.html", admin, item=item)


@router.post("/kategori/{id}/edit")
def edit_kategori(
    id: int,
    request: Request,
    nama_kategori: str = Form(...),
    deskripsi: str = Form(""),
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    return simpan(
        request, db,
        "UPDATE kategori SET nama_kategori = %s, deskripsi = %s WHERE id = %s",
        (nama_kategori.strip(), deskripsi.strip(), id),
        "/admin/kategori",
    )


@router.post("/kategori/{id}/hapus")
def hapus_kategori(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    return hapus(request, db, "kategori", id, "/admin/kategori")


# ---------- Layanan ----------

@router.get("/layanan")
def daftar_layanan(request: Request, admin=Depends(khusus_admin), db=Depends(get_db)):
    data = ambil_semua(
        db,
        """
        SELECT l.*, k.nama_kategori
        FROM layanan l
        JOIN kategori k ON k.id = l.kategori_id
        ORDER BY k.nama_kategori, l.nama_layanan
        """,
    )
    return render(request, "admin/layanan.html", admin, data=data)


@router.get("/layanan/tambah")
def form_tambah_layanan(request: Request, admin=Depends(khusus_admin), db=Depends(get_db)):
    kategori = ambil_semua(db, "SELECT * FROM kategori ORDER BY nama_kategori")
    return render(request, "admin/layanan_form.html", admin, item=None, kategori=kategori)


@router.post("/layanan/tambah")
def tambah_layanan(
    request: Request,
    nama_layanan: str = Form(...),
    kategori_id: int = Form(...),
    biaya_admin: int = Form(0, ge=0),
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    return simpan(
        request, db,
        "INSERT INTO layanan (nama_layanan, kategori_id, biaya_admin) VALUES (%s, %s, %s)",
        (nama_layanan.strip(), kategori_id, biaya_admin),
        "/admin/layanan",
    )


@router.get("/layanan/{id}/edit")
def form_edit_layanan(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    item = cari(db, "layanan", id, "/admin/layanan")
    kategori = ambil_semua(db, "SELECT * FROM kategori ORDER BY nama_kategori")
    return render(request, "admin/layanan_form.html", admin, item=item, kategori=kategori)


@router.post("/layanan/{id}/edit")
def edit_layanan(
    id: int,
    request: Request,
    nama_layanan: str = Form(...),
    kategori_id: int = Form(...),
    biaya_admin: int = Form(0, ge=0),
    aktif: bool = Form(False),
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    return simpan(
        request, db,
        """
        UPDATE layanan
        SET nama_layanan = %s, kategori_id = %s, biaya_admin = %s, aktif = %s
        WHERE id = %s
        """,
        (nama_layanan.strip(), kategori_id, biaya_admin, aktif, id),
        "/admin/layanan",
    )


@router.post("/layanan/{id}/hapus")
def hapus_layanan(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    return hapus(request, db, "layanan", id, "/admin/layanan")


# ---------- Metode isi saldo ----------

@router.get("/metode")
def daftar_metode(request: Request, admin=Depends(khusus_admin), db=Depends(get_db)):
    data = ambil_semua(db, "SELECT * FROM metode_topup ORDER BY nama_metode")
    return render(request, "admin/metode.html", admin, data=data)


@router.get("/metode/tambah")
def form_tambah_metode(request: Request, admin=Depends(khusus_admin)):
    return render(request, "admin/metode_form.html", admin, item=None)


@router.post("/metode/tambah")
def tambah_metode(
    request: Request,
    nama_metode: str = Form(...),
    keterangan: str = Form(""),
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    return simpan(
        request, db,
        "INSERT INTO metode_topup (nama_metode, keterangan) VALUES (%s, %s)",
        (nama_metode.strip(), keterangan.strip()),
        "/admin/metode",
    )


@router.get("/metode/{id}/edit")
def form_edit_metode(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    item = cari(db, "metode_topup", id, "/admin/metode")
    return render(request, "admin/metode_form.html", admin, item=item)


@router.post("/metode/{id}/edit")
def edit_metode(
    id: int,
    request: Request,
    nama_metode: str = Form(...),
    keterangan: str = Form(""),
    aktif: bool = Form(False),
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    return simpan(
        request, db,
        "UPDATE metode_topup SET nama_metode = %s, keterangan = %s, aktif = %s WHERE id = %s",
        (nama_metode.strip(), keterangan.strip(), aktif, id),
        "/admin/metode",
    )


@router.post("/metode/{id}/hapus")
def hapus_metode(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    return hapus(request, db, "metode_topup", id, "/admin/metode")


# ---------- Pengguna ----------
# Pengguna baru dibuat lewat halaman Register, jadi di sini hanya lihat, ubah, dan hapus.

@router.get("/pengguna")
def daftar_pengguna(
    request: Request, q: str = "", admin=Depends(khusus_admin), db=Depends(get_db)
):
    data = ambil_semua(
        db,
        """
        SELECT id, nama, email, no_hp, role, saldo, aktif, dibuat_pada
        FROM pengguna
        WHERE nama ILIKE %s OR email ILIKE %s OR no_hp ILIKE %s
        ORDER BY role, nama
        """,
        (f"%{q}%", f"%{q}%", f"%{q}%"),
    )
    return render(request, "admin/pengguna.html", admin, data=data, q=q)


@router.get("/pengguna/{id}/edit")
def form_edit_pengguna(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    item = cari(db, "pengguna", id, "/admin/pengguna")
    return render(request, "admin/pengguna_form.html", admin, item=item)


@router.post("/pengguna/{id}/edit")
def edit_pengguna(
    id: int,
    request: Request,
    nama: str = Form(...),
    no_hp: str = Form(...),
    aktif: bool = Form(False),
    admin=Depends(khusus_admin),
    db=Depends(get_db),
):
    if id == admin["id"]:
        aktif = True  # admin tidak bisa menonaktifkan akunnya sendiri
    return simpan(
        request, db,
        "UPDATE pengguna SET nama = %s, no_hp = %s, aktif = %s WHERE id = %s",
        (nama.strip(), no_hp.strip(), aktif, id),
        "/admin/pengguna",
    )


@router.post("/pengguna/{id}/hapus")
def hapus_pengguna(
    id: int, request: Request, admin=Depends(khusus_admin), db=Depends(get_db)
):
    if id == admin["id"]:
        pesan(request, "Akun sendiri tidak bisa dihapus.", "gagal")
        return alihkan("/admin/pengguna")
    return hapus(request, db, "pengguna", id, "/admin/pengguna")
