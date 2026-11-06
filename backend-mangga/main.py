from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import auth, inventory, logistics, rfq
from core.config import settings
from db.session import get_db


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API untuk Platform Manajemen Rantai Pasok B2B Mangga",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(inventory.router, prefix="/api/mangga", tags=["Inventaris"])
app.include_router(rfq.router, prefix="/api/rfq", tags=["RFQ"])
app.include_router(logistics.router, prefix="/api/logistik", tags=["Logistik"])


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "API Juragan Mangga Reang aktif. Akses /docs untuk Swagger UI."}


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
