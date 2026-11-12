from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Evento


class EventoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obtener(self, id: int):
        return self.db.get(Evento, id)

    def listar(self):
        return list(self.db.scalars(select(Evento).order_by(Evento.id)))

    def agregar(self, evento: Evento):
        self.db.add(evento)
