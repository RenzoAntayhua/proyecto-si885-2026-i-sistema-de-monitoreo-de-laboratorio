"""
schemas.py - Pydantic v2 schemas para validación de datos en la API.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field


# ── Laboratorio ─────────────────────────────────────────────────────────────
class LaboratorioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255, examples=["LAB-101"])
    descripcion: Optional[str] = Field(None, examples=["Laboratorio principal de cómputo"])


class LaboratorioResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: Optional[str]
    creado_en: datetime
    total_computadoras: int = 0

    model_config = {"from_attributes": True}


# ── Computadora ─────────────────────────────────────────────────────────────
class ComputadoraCreate(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255, examples=["PC-01"])
    laboratorio_id: UUID
    ip_local: Optional[str] = Field(None, max_length=45, examples=["192.168.1.5"])


class ComputadoraResponse(BaseModel):
    id: UUID
    hostname: str
    laboratorio_id: UUID
    ip_local: Optional[str]
    activo: bool = True
    registrado_en: datetime
    laboratorio_nombre: Optional[str] = None

    model_config = {"from_attributes": True}


# ── ETL Sync ────────────────────────────────────────────────────────────────
class ETLSyncResponse(BaseModel):
    registros_procesados: int
    mensaje: str = "Sincronización completada"
