from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Lugar


class LugarRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obtener(self, id: int):
        return self.db.get(Lugar, id)

    def listar(self):
        return list(self.db.scalars(select(Lugar).order_by(Lugar.id)))

    def agregar(self, lugar: Lugar):
        self.db.add(lugar)
