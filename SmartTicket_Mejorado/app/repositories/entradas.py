from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Entrada


class EntradaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def disponibles(self, evento_id: int, sector_id: int, limite: int | None = None):
        consulta = select(Entrada).where(
            Entrada.evento_id == evento_id,
            Entrada.sector_id == sector_id,
            Entrada.estado == "Disponible",
        ).order_by(Entrada.id)
        if limite is not None:
            consulta = consulta.limit(limite)
        return list(self.db.scalars(consulta))

    def contar_disponibles(self, evento_id: int, sector_id: int) -> int:
        return self.db.scalar(select(func.count()).select_from(Entrada).where(
            Entrada.evento_id == evento_id,
            Entrada.sector_id == sector_id,
            Entrada.estado == "Disponible",
        )) or 0

    def por_ids(self, ids: list[int]):
        return list(self.db.scalars(select(Entrada).where(Entrada.id.in_(ids)))) if ids else []

    def por_qr(self, qr: str):
        return self.db.scalar(select(Entrada).where(Entrada.codigo_qr == qr))

    def agregar(self, entrada: Entrada):
        self.db.add(entrada)
