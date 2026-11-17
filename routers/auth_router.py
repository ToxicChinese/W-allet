"""Login, register, logout, dan profil."""
import re

from fastapi import APIRouter, Depends, Form, Request
from psycopg2.errors import UniqueViolation

from database import ambil_satu, get_db, jalankan
from helper import (
    alihkan,
    cek_password,
    hash_password,
    periksa_password,
    pesan,
    render,
    user_login,
)

router = APIRouter()


def periksa_data_diri(nama, no_hp):
    """Kembalikan teks kesalahan, atau None kalau data sudah benar."""
    if not 3 <= len(nama) <= 100:
        return "Nama harus 3 sampai 100 huruf."
    if not re.fullmatch(r"08\d{8,13}", no_hp):
        return "Nomor HP harus diawali 08 dan berisi 10 sampai 15 angka."
    return None


# ---------- Login dan logout ----------

@router.get("/login")
def form_login(request: Request):
    if request.session.get("user_id"):
        return alihkan("/")
    return render(request, "login.html")


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db),
):
    user = ambil_satu(
        db,
        "SELECT id, password, aktif FROM pengguna WHERE email = %s",
        (email.strip().lower(),),
    )
    if not user or not cek_password(password, user["password"]):
        pesan(request, "Email atau password salah.", "gagal")
        return alihkan("/login")
    if not user["aktif"]:
        pesan(request, "Akun ini dinonaktifkan. Hubungi admin.", "gagal")
        return alihkan("/login")

    request.session["user_id"] = user["id"]
    return alihkan("/")


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return alihkan("/login")


# ---------- Register ----------

@router.get("/register")
def form_register(request: Request):
    return render(request, "register.html", isi={})


@router.post("/register")
def register(
    request: Request,
    nama: str = Form(...),
    email: str = Form(...),
    no_hp: str = Form(...),
    password: str = Form(...),
    ulangi: str = Form(...),
    db=Depends(get_db),
):
    nama, email, no_hp = nama.strip(), email.strip().lower(), no_hp.strip()

    salah = periksa_data_diri(nama, no_hp)
    if not salah and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        salah = "Format email tidak benar."
    if not salah:
        salah = periksa_password(password, ulangi)
    if not salah:
        try:
            jalankan(
                db,
                "INSERT INTO pengguna (nama, email, no_hp, password) VALUES (%s, %s, %s, %s)",
                (nama, email, no_hp, hash_password(password)),
            )
            db.commit()
        except UniqueViolation:
            salah = "Email atau nomor HP itu sudah terdaftar."

    if salah:
        pesan(request, salah, "gagal")
        return render(
            request, "register.html", isi={"nama": nama, "email": email, "no_hp": no_hp}
        )

    pesan(request, "Pendaftaran berhasil. Silakan login.")
    return alihkan("/login")


# ---------- Profil ----------

@router.get("/profil")
def form_profil(request: Request, user=Depends(user_login)):
    return render(request, "profil.html", user)


@router.post("/profil")
def simpan_profil(
    request: Request,
    nama: str = Form(...),
    no_hp: str = Form(...),
    password_lama: str = Form(""),
    password_baru: str = Form(""),
    ulangi: str = Form(""),
    user=Depends(user_login),
    db=Depends(get_db),
):
    nama, no_hp = nama.strip(), no_hp.strip()

    salah = periksa_data_diri(nama, no_hp)
    if not salah and password_baru:
        tersimpan = ambil_satu(db, "SELECT password FROM pengguna WHERE id = %s", (user["id"],))
        if not cek_password(password_lama, tersimpan["password"]):
            salah = "Password lama salah."
        else:
            salah = periksa_password(password_baru, ulangi)
    if not salah:
        try:
            jalankan(
                db,
                "UPDATE pengguna SET nama = %s, no_hp = %s WHERE id = %s",
                (nama, no_hp, user["id"]),
            )
            if password_baru:
                jalankan(
                    db,
                    "UPDATE pengguna SET password = %s WHERE id = %s",
                    (hash_password(password_baru), user["id"]),
                )
            db.commit()
        except UniqueViolation:
            salah = "Nomor HP itu sudah dipakai akun lain."

    if salah:
        pesan(request, salah, "gagal")
    else:
        pesan(request, "Profil berhasil diperbarui.")
    return alihkan("/profil")
