"""
database.py - Configuración de SQLAlchemy y sesión de base de datos.

Usa SQLAlchemy con driver asyncpg para conexiones asíncronas a PostgreSQL.
Las variables de conexión se cargan desde el archivo .env.
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

# ── Configuración de conexión ───────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://netmon_user:changeme@localhost:5432/network_monitor"
)

# ── Engine y Session Factory ────────────────────────────────────────────────
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base declarativa ────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency injection para FastAPI ───────────────────────────────────────
async def get_db():
    """
    Generador de sesión de base de datos para inyección de dependencias.
    Uso: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
