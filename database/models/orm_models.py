from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text,
    DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship, DeclarativeBase

# String(36) en vez de CHAR(36) para compatibilidad con SQLite
CHAR = lambda n: String(n)


class Base(DeclarativeBase):
    pass


class UsuarioModel(Base):
    __tablename__ = "usuario"

    id = Column(CHAR(36), primary_key=True)
    nombre = Column(String(255), nullable=False)
    correo = Column(String(255), nullable=False, unique=True)
    contrasena_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    itinerarios = relationship("ItinerarioModel", back_populates="usuario", cascade="all, delete-orphan")


class AeropuertoCacheModel(Base):
    __tablename__ = "aeropuerto_cache"

    iata_code = Column(CHAR(3), primary_key=True)
    nombre = Column(String(255), nullable=False)
    ciudad = Column(String(255), nullable=False)
    pais = Column(String(255), nullable=False)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    consultado_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    itinerarios_origen = relationship(
        "ItinerarioModel",
        foreign_keys="ItinerarioModel.aeropuerto_origen_iata",
        back_populates="aeropuerto_origen",
    )
    itinerarios_destino = relationship(
        "ItinerarioModel",
        foreign_keys="ItinerarioModel.aeropuerto_destino_iata",
        back_populates="aeropuerto_destino",
    )


class ItinerarioModel(Base):
    __tablename__ = "itinerario"

    id = Column(CHAR(36), primary_key=True)
    usuario_id = Column(CHAR(36), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    aeropuerto_origen_iata = Column(CHAR(3), ForeignKey("aeropuerto_cache.iata_code"), nullable=False)
    aeropuerto_destino_iata = Column(CHAR(3), ForeignKey("aeropuerto_cache.iata_code"), nullable=False)
    fecha_hora_salida = Column(DateTime, nullable=False)
    fecha_hora_llegada = Column(DateTime, nullable=False)
    duracion_minutos = Column(Integer, nullable=False)
    notas = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = relationship("UsuarioModel", back_populates="itinerarios")
    aeropuerto_origen = relationship(
        "AeropuertoCacheModel",
        foreign_keys=[aeropuerto_origen_iata],
        back_populates="itinerarios_origen",
    )
    aeropuerto_destino = relationship(
        "AeropuertoCacheModel",
        foreign_keys=[aeropuerto_destino_iata],
        back_populates="itinerarios_destino",
    )
