from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import PrecioSector


class PrecioRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def del_sector(self, evento_id: int, sector_id: int):
        return self.db.scalar(select(PrecioSector).where(
            PrecioSector.evento_id == evento_id, PrecioSector.sector_id == sector_id
        ))

    def agregar(self, precio: PrecioSector):
        self.db.add(precio)
