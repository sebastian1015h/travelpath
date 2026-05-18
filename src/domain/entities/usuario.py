from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Usuario:
    nombre: str
    correo: str
    contrasena_hash: str
    id: str = field(default_factory=lambda: str(uuid4()))
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def desactivar(self):
        self.activo = False
        self.updated_at = datetime.utcnow()
