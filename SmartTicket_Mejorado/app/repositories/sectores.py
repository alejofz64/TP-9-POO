from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Sector


class SectorRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obtener(self, id: int):
        return self.db.get(Sector, id)

    def listar(self):
        return list(self.db.scalars(select(Sector).order_by(Sector.id)))

    def de_lugar(self, lugar_id: int):
        return list(self.db.scalars(select(Sector).where(Sector.lugar_id == lugar_id).order_by(Sector.id)))

    def agregar(self, sector: Sector):
        self.db.add(sector)
