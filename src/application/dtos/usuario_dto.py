from dataclasses import dataclass
from typing import Optional


@dataclass
class RegisterDTO:
    nombre: str
    correo: str
    contrasena: str


@dataclass
class LoginDTO:
    correo: str
    contrasena: str
    recordar: bool = False


@dataclass
class UsuarioResponseDTO:
    id: str
    nombre: str
    correo: str
    activo: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "correo": self.correo,
            "activo": self.activo,
        }
