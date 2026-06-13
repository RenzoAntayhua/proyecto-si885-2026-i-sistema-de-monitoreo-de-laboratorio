"""
models.py - Modelos ORM de SQLAlchemy para el sistema de monitoreo de red.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, DateTime, Boolean,
    ForeignKey, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


class Laboratorio(Base):
    __tablename__ = "laboratorios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    nombre = Column(String(255), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("NOW()"))
    computadoras = relationship("Computadora", back_populates="laboratorio", cascade="all, delete-orphan", lazy="selectin")


class Computadora(Base):
    __tablename__ = "computadoras"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    hostname = Column(String(255), nullable=False)
    laboratorio_id = Column(UUID(as_uuid=True), ForeignKey("laboratorios.id", ondelete="CASCADE"), nullable=False)
    ip_local = Column(String(45), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    registrado_en = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("NOW()"))
    laboratorio = relationship("Laboratorio", back_populates="computadoras")
    trafico = relationship("TraficoRed", back_populates="computadora", cascade="all, delete-orphan", lazy="noload")


class TraficoRed(Base):
    __tablename__ = "trafico_red"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    computadora_id = Column(UUID(as_uuid=True), ForeignKey("computadoras.id", ondelete="CASCADE"), nullable=False)
    timestamp_evento = Column(DateTime, nullable=False)
    ip_origen = Column(String(45), nullable=True)
    ip_destino = Column(String(45), nullable=True)
    pais_destino = Column(String(100), nullable=True)
    ciudad_destino = Column(String(100), nullable=True)
    puerto_destino = Column(Integer, nullable=True)
    protocolo = Column(String(10), nullable=True)
    proceso = Column(String(500), nullable=True)
    computadora = relationship("Computadora", back_populates="trafico")


class EtlEstado(Base):
    __tablename__ = "etl_estado"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ultimo_timestamp = Column(DateTime, nullable=False, default=datetime(1970, 1, 1), server_default=text("'1970-01-01 00:00:00'"))
    registros_procesados = Column(BigInteger, default=0)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("NOW()"))
