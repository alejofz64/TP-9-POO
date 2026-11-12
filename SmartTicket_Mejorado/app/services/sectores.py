from sqlalchemy.orm import Session
from app.models import Sector
from app.domain.exceptions import NoEncontrado
from app.repositories import LugarRepositorio, SectorRepositorio
from app.schemas import SectorCrear


class SectorServicio:
    def __init__(self, db: Session, sectores: SectorRepositorio, lugares: LugarRepositorio):
        self.db, self.sectores, self.lugares = db, sectores, lugares

    def crear(self, datos: SectorCrear):
        if self.lugares.obtener(datos.lugar_id) is None:
            raise NoEncontrado("Lugar no encontrado")
        sector = Sector(**datos.model_dump())
        self.sectores.agregar(sector)
        self.db.commit()
        self.db.refresh(sector)
        return sector

    def listar(self):
        return self.sectores.listar()

    def obtener(self, id: int):
        sector = self.sectores.obtener(id)
        if sector is None:
            raise NoEncontrado("Sector no encontrado")
        return sector
