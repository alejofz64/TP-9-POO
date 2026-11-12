"""Creación de datos de demostración (idempotente por fecha)."""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import Cliente, Evento, Lugar, Sector
from app.repositories import (
    LugarRepositorio, SectorRepositorio, ClienteRepositorio, EventoRepositorio,
    EntradaRepositorio, VentaRepositorio,
)
from app.schemas import ClienteCrear, EventoCrear, LugarCrear, PrecioCrear, SectorCrear
from app.services.lugares import LugarServicio
from app.services.sectores import SectorServicio
from app.services.clientes import ClienteServicio
from app.services.eventos import EventoServicio


def main():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        lugares = LugarServicio(db, LugarRepositorio(db))
        sectores_servicio = SectorServicio(db, SectorRepositorio(db), LugarRepositorio(db))
        clientes = ClienteServicio(db, ClienteRepositorio(db))
        eventos = EventoServicio(db, LugarRepositorio(db), SectorRepositorio(db), EventoRepositorio(db),
                                 EntradaRepositorio(db), VentaRepositorio(db))
        hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
        existente = db.scalar(select(Evento).where(Evento.nombre == "Rock Fest Demo", Evento.fecha == hoy))
        if existente:
            evento = existente
            lugar = db.get(Lugar, evento.lugar_id)
            sectores = list(db.scalars(select(Sector).where(Sector.lugar_id == lugar.id)))
            cliente = db.scalar(select(Cliente).where(Cliente.email == "demo@smartticket.test"))
        else:
            # Clientes de demo para el escenario de prácticas.
            cliente = db.scalar(select(Cliente).where(Cliente.email == "demo@smartticket.test"))
            if cliente is None:
                cliente = clientes.crear(ClienteCrear(nombre="Cliente de prueba", email="demo@smartticket.test"))
            lugar = lugares.crear(LugarCrear(nombre="Estadio Demo", direccion="Av. Principal 123"))
            sectores = [
                sectores_servicio.crear(SectorCrear(lugar_id=lugar.id, nombre="Platea", capacidad=20)),
                sectores_servicio.crear(SectorCrear(lugar_id=lugar.id, nombre="VIP", capacidad=5)),
            ]
            evento = eventos.crear(EventoCrear(
                lugar_id=lugar.id, nombre="Rock Fest Demo", fecha=hoy,
                precios=[PrecioCrear(sector_id=sectores[0].id, precio="12000"),
                         PrecioCrear(sector_id=sectores[1].id, precio="50000")],
            ))
        print("Datos de prueba disponibles:")
        print(f"  Lugar: {lugar.id}")
        for sector in sectores:
            print(f"  Sector {sector.nombre}: {sector.id} (capacidad {sector.capacidad})")
        print(f"  Evento: {evento.id} - {evento.nombre} - {evento.fecha}")
        print(f"  Cliente: {cliente.id if cliente else 'no encontrado'}")
        print("  Swagger: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    main()
