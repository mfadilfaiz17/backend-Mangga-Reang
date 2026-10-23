from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models.domain_models import Base, engine

# Otomatis membuat tabel di database jika belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API untuk Platform Manajemen Rantai Pasok B2B Mangga"
)

# === ZONA BAHAYA CORS (DIATASI) ===
# Masukkan URL Frontend Next.js di sini (localhost dan URL Vercel nanti)
origins = [
    "http://localhost:3000",
    "https://namawebFE.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Endpoint untuk Test
@app.get("/")
def read_root():
    return {"message": "Selamat datang di API Juragan Mangga Reang! Akses /docs untuk Swagger UI."}

# Nanti masukkan router dari folder app/api/routes di sini
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(mangga.router, prefix="/api/mangga", tags=["Inventaris"])