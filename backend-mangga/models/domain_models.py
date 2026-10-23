from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Setup Database Connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Contoh Tabel Database
class Mangga(Base):
    __tablename__ = "mangga_inventaris"

    id = Column(Integer, primary_key=True, index=True)
    varietas = Column(String, index=True)      # Cengkir / Gedong Gincu
    grade = Column(String)                     # Grade A / B
    tonase = Column(Float, default=0.0)