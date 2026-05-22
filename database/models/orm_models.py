from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class TokenRevocadoModel(Base):
    __tablename__ = "token_revocado"

    jti = Column(String(36), primary_key=True)
    revocado_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class UsuarioModel(Base):
    __tablename__ = "usuario"

    id = Column(String(36), primary_key=True)
    nombre = Column(String(255), nullable=False)
    correo = Column(String(255), nullable=False, unique=True)
    contrasena_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    itinerarios = relationship("ItinerarioModel", back_populates="usuario", cascade="all, delete-orphan")



class ItinerarioModel(Base):
    __tablename__ = "itinerario"

    id = Column(String(36), primary_key=True)
    usuario_id = Column(String(36), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    aeropuerto_origen_iata = Column(String(3), nullable=False)
    aeropuerto_destino_iata = Column(String(3), nullable=False)
    fecha_hora_salida = Column(DateTime, nullable=False)
    fecha_hora_llegada = Column(DateTime, nullable=False)
    duracion_minutos = Column(Integer, nullable=False)
    notas = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = relationship("UsuarioModel", back_populates="itinerarios")
