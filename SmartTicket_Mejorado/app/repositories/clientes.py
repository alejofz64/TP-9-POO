from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Cliente


class ClienteRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obtener(self, id: int):
        return self.db.get(Cliente, id)

    def listar(self):
        return list(self.db.scalars(select(Cliente).order_by(Cliente.id)))

    def por_email(self, email: str):
        return self.db.scalar(select(Cliente).where(Cliente.email == email))

    def agregar(self, cliente: Cliente):
        self.db.add(cliente)
