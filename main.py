"""W-allet: dompet digital sederhana (FastAPI + Jinja2 + PostgreSQL).

Menjalankan di laptop:
    python -m uvicorn main:app --reload
"""
import os

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from helper import BASE_DIR, NAMA_APLIKASI, Alihkan, pesan
from routers import (
    auth_router,
    dashboard_router,
    laporan_router,
    master_router,
    transaksi_router,
)

app = FastAPI(title=NAMA_APLIKASI)

# Session login disimpan di cookie yang ditandatangani dengan SECRET_KEY.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "ganti-kunci-ini-saat-hosting"),
    max_age=60 * 60 * 8,  # login berlaku 8 jam
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.exception_handler(Alihkan)
def tangani_alihkan(request: Request, exc: Alihkan):
    if exc.teks:
        pesan(request, exc.teks, "gagal")
    return RedirectResponse(exc.url, status_code=303)


app.include_router(auth_router.router)
app.include_router(dashboard_router.router)
app.include_router(transaksi_router.router)
app.include_router(master_router.router)
app.include_router(laporan_router.router)
