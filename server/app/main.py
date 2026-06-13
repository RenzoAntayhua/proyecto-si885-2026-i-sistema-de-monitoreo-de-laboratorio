"""
main.py - FastAPI application con endpoints REST para el sistema de monitoreo.
"""

import logging
from uuid import UUID
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Laboratorio, Computadora, TraficoRed
from .schemas import (
    LaboratorioCreate, LaboratorioResponse,
    ComputadoraCreate, ComputadoraResponse,
    ETLSyncResponse,
)

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sistema de Monitoreo de Red",
    description="API para gestión de laboratorios, computadoras y tráfico de red.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints: Laboratorios ─────────────────────────────────────────────────

@app.get("/api/laboratorios/", response_model=List[LaboratorioResponse])
async def listar_laboratorios(db: AsyncSession = Depends(get_db)):
    """Retorna la lista de laboratorios con conteo de computadoras."""
    query = (
        select(
            Laboratorio,
            func.count(Computadora.id).label("total_computadoras")
        )
        .outerjoin(Computadora, Laboratorio.id == Computadora.laboratorio_id)
        .group_by(Laboratorio.id)
        .order_by(Laboratorio.creado_en.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        LaboratorioResponse(
            id=lab.id,
            nombre=lab.nombre,
            descripcion=lab.descripcion,
            creado_en=lab.creado_en,
            total_computadoras=total,
        )
        for lab, total in rows
    ]


@app.post("/api/laboratorios/", response_model=LaboratorioResponse, status_code=status.HTTP_201_CREATED)
async def crear_laboratorio(data: LaboratorioCreate, db: AsyncSession = Depends(get_db)):
    """Crea un nuevo laboratorio."""
    # Verificar nombre único
    existing = await db.execute(
        select(Laboratorio).where(Laboratorio.nombre == data.nombre)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe un laboratorio con el nombre '{data.nombre}'.")

    lab = Laboratorio(nombre=data.nombre, descripcion=data.descripcion)
    db.add(lab)
    await db.commit()
    await db.refresh(lab)

    return LaboratorioResponse(
        id=lab.id,
        nombre=lab.nombre,
        descripcion=lab.descripcion,
        creado_en=lab.creado_en,
        total_computadoras=0,
    )


@app.put("/api/laboratorios/{lab_id}", response_model=LaboratorioResponse)
async def actualizar_laboratorio(lab_id: UUID, data: LaboratorioCreate, db: AsyncSession = Depends(get_db)):
    """Actualiza un laboratorio existente."""
    result = await db.execute(select(Laboratorio).where(Laboratorio.id == lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado.")

    lab.nombre = data.nombre
    lab.descripcion = data.descripcion
    await db.commit()
    await db.refresh(lab)

    count_result = await db.execute(
        select(func.count(Computadora.id)).where(Computadora.laboratorio_id == lab_id)
    )
    total = count_result.scalar() or 0

    return LaboratorioResponse(
        id=lab.id, nombre=lab.nombre, descripcion=lab.descripcion,
        creado_en=lab.creado_en, total_computadoras=total,
    )


@app.delete("/api/laboratorios/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_laboratorio(lab_id: UUID, db: AsyncSession = Depends(get_db)):
    """Elimina un laboratorio y sus computadoras asociadas (CASCADE)."""
    result = await db.execute(select(Laboratorio).where(Laboratorio.id == lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado.")
    await db.delete(lab)
    await db.commit()


# ── Endpoints: Computadoras ─────────────────────────────────────────────────

@app.get("/api/computadoras/", response_model=List[ComputadoraResponse])
async def listar_computadoras(db: AsyncSession = Depends(get_db)):
    """Lista todas las computadoras registradas con nombre de laboratorio."""
    query = (
        select(Computadora, Laboratorio.nombre.label("lab_nombre"))
        .join(Laboratorio, Computadora.laboratorio_id == Laboratorio.id)
        .order_by(Computadora.registrado_en.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        ComputadoraResponse(
            id=pc.id, hostname=pc.hostname, laboratorio_id=pc.laboratorio_id,
            ip_local=pc.ip_local, activo=pc.activo, registrado_en=pc.registrado_en,
            laboratorio_nombre=lab_nombre,
        )
        for pc, lab_nombre in rows
    ]


@app.post("/api/computadoras/", response_model=ComputadoraResponse, status_code=status.HTTP_201_CREATED)
async def registrar_computadora(data: ComputadoraCreate, db: AsyncSession = Depends(get_db)):
    """Registra una nueva PC desde el instalador C#."""
    # Verificar que el laboratorio existe
    lab_result = await db.execute(select(Laboratorio).where(Laboratorio.id == data.laboratorio_id))
    lab = lab_result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado.")

    pc = Computadora(hostname=data.hostname, laboratorio_id=data.laboratorio_id, ip_local=data.ip_local)
    db.add(pc)
    await db.commit()
    await db.refresh(pc)

    return ComputadoraResponse(
        id=pc.id, hostname=pc.hostname, laboratorio_id=pc.laboratorio_id,
        ip_local=pc.ip_local, activo=pc.activo, registrado_en=pc.registrado_en,
        laboratorio_nombre=lab.nombre,
    )


# ── Endpoints: ETL ──────────────────────────────────────────────────────────

@app.post("/api/etl/sync", response_model=ETLSyncResponse)
async def ejecutar_etl_sync():
    """Ejecuta síncronamente el motor ETL y retorna el resumen."""
    try:
        from .etl.engine import run_etl
        registros = run_etl()
        return ETLSyncResponse(
            registros_procesados=registros,
            mensaje=f"Sincronización completada. {registros} registros procesados.",
        )
    except Exception as e:
        logger.error(f"Error en ETL sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error durante la sincronización ETL: {str(e)}")


@app.post("/api/etl/sync-agents")
async def ejecutar_sync_agents():
    """Ejecuta la sincronización de agentes activos contra Wazuh API."""
    try:
        from .etl.sync_agents import run_agent_sync
        stats = run_agent_sync()
        return {
            "mensaje": "Sincronización de agentes completada.",
            "estadisticas": stats
        }
    except Exception as e:
        logger.error(f"Error en Sync Agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sincronizando agentes: {str(e)}")


@app.post("/api/etl/housekeeping")
async def ejecutar_housekeeping():
    """Ejecuta la limpieza de registros antiguos de la base de datos."""
    try:
        from .etl.housekeeping import run_housekeeping
        stats = run_housekeeping()
        return {
            "mensaje": f"Housekeeping completado. Se conservan {stats['dias_retencion']} días de historial.",
            "estadisticas": stats
        }
    except Exception as e:
        logger.error(f"Error en Housekeeping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en housekeeping: {str(e)}")


# ── Endpoints: Estadísticas (para Dashboard) ────────────────────────────────

@app.get("/api/stats/")
async def obtener_estadisticas(db: AsyncSession = Depends(get_db)):
    """Retorna estadísticas generales para el dashboard."""
    labs = await db.execute(select(func.count(Laboratorio.id)))
    pcs = await db.execute(select(func.count(Computadora.id)))
    traffic = await db.execute(select(func.count(TraficoRed.id)))

    return {
        "total_laboratorios": labs.scalar() or 0,
        "total_computadoras": pcs.scalar() or 0,
        "total_trafico": traffic.scalar() or 0,
    }


@app.get("/api/download-installer")
async def descargar_instalador():
    """Sirve el archivo ejecutable del instalador."""
    # Ruta al instalador en el servidor VPS
    # Ajusta esta ruta si el archivo está en otro lugar
    installer_path = "/var/www/html/downloads/NetworkMonitorInstaller.exe"
    
    if not os.path.exists(installer_path):
        # Intentar ruta relativa para desarrollo local si aplica
        installer_path = "installer_mock.exe" # Solo fallback
        if not os.path.exists(installer_path):
            raise HTTPException(status_code=404, detail="Archivo instalador no encontrado en el servidor.")

    return FileResponse(
        path=installer_path,
        filename="NetworkMonitorInstaller.exe",
        media_type="application/octet-stream"
    )
