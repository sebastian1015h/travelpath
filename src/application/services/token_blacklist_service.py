from datetime import datetime
from sqlalchemy.orm import Session

from database.models.orm_models import TokenRevocadoModel


class TokenBlacklistService:

    def __init__(self, session: Session):
        self._session = session

    def revocar(self, jti: str) -> None:
        try:
            if not self._session.get(TokenRevocadoModel, jti):
                self._session.add(TokenRevocadoModel(jti=jti, revocado_at=datetime.utcnow()))
                self._session.commit()
        except Exception:
            self._session.rollback()

    def esta_revocado(self, jti: str) -> bool:
        try:
            return self._session.get(TokenRevocadoModel, jti) is not None
        except Exception:
            return False
