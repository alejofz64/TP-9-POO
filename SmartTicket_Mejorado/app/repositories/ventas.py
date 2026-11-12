from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models import Venta, VentaEntrada


class VentaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obtener(self, id: int):
        return self.db.scalar(select(Venta).options(
            selectinload(Venta.lineas).selectinload(VentaEntrada.entrada)
        ).where(Venta.id == id))

    def pendientes_vencidas(self, ahora_utc: datetime):
        return list(self.db.scalars(select(Venta).options(
            selectinload(Venta.lineas).selectinload(VentaEntrada.entrada)
        ).where(Venta.estado == "Pendiente", Venta.expira_en <= ahora_utc)))

    def agregar(self, venta: Venta):
        self.db.add(venta)
