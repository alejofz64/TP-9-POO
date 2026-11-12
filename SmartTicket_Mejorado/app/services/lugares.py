from sqlalchemy.orm import Session
from app.models import Lugar
from app.domain.exceptions import NoEncontrado
from app.repositories import LugarRepositorio
from app.schemas import LugarCrear


class LugarServicio:
    def __init__(self, db: Session, repo: LugarRepositorio):
        self.db, self.repo = db, repo

    def crear(self, datos: LugarCrear):
        lugar = Lugar(**datos.model_dump())
        self.repo.agregar(lugar)
        self.db.commit()
        self.db.refresh(lugar)
        return lugar

    def listar(self):
        return self.repo.listar()

    def obtener(self, id: int):
        lugar = self.repo.obtener(id)
        if lugar is None:
            raise NoEncontrado("Lugar no encontrado")
        return lugar
