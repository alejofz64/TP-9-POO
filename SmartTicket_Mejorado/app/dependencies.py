"""Composición e inyección de dependencias. Servicios no importan FastAPI."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.payments import PasarelaPago, PasarelaSimulada
from app.repositories import (
    LugarRepositorio, SectorRepositorio, ClienteRepositorio, EventoRepositorio,
    PrecioRepositorio, EntradaRepositorio, VentaRepositorio,
)
from app.services.lugares import LugarServicio
from app.services.sectores import SectorServicio
from app.services.clientes import ClienteServicio
from app.services.eventos import EventoServicio
from app.services.cotizaciones import CotizacionServicio
from app.services.pagos import PagoServicio
from app.services.accesos import AccesoServicio


def get_pasarela() -> PasarelaPago:
    return PasarelaSimulada()


def get_lugares(db: Session = Depends(get_session)):
    return LugarServicio(db, LugarRepositorio(db))


def get_sectores(db: Session = Depends(get_session)):
    return SectorServicio(db, SectorRepositorio(db), LugarRepositorio(db))


def get_clientes(db: Session = Depends(get_session)):
    return ClienteServicio(db, ClienteRepositorio(db))


def get_eventos(db: Session = Depends(get_session)):
    return EventoServicio(db, LugarRepositorio(db), SectorRepositorio(db), EventoRepositorio(db),
                          EntradaRepositorio(db), VentaRepositorio(db))


def get_cotizador(db: Session = Depends(get_session)):
    return CotizacionServicio(db, EntradaRepositorio(db), PrecioRepositorio(db), VentaRepositorio(db))


def get_pagos(db: Session = Depends(get_session), pasarela: PasarelaPago = Depends(get_pasarela)):
    return PagoServicio(db, ClienteRepositorio(db), EntradaRepositorio(db), PrecioRepositorio(db),
                        VentaRepositorio(db), pasarela)


def get_accesos(db: Session = Depends(get_session)):
    return AccesoServicio(db, EntradaRepositorio(db))
