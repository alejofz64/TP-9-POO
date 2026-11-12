"""Evento se encarga de la regla de precios completos y generación por capacidad."""
import secrets
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models import Evento, PrecioSector, Entrada
from app.domain.exceptions import NoEncontrado, SolicitudInvalida, SinPrecio
from app.repositories import LugarRepositorio, SectorRepositorio, EventoRepositorio, EntradaRepositorio, VentaRepositorio
from app.schemas import EventoCrear
from app.services.reservas import ReservasServicio


class EventoServicio:
    def __init__(self, db: Session, lugares: LugarRepositorio, sectores: SectorRepositorio,
                 eventos: EventoRepositorio, entradas: EntradaRepositorio, ventas: VentaRepositorio):
        self.db, self.lugares, self.sectores = db, lugares, sectores
        self.eventos, self.entradas, self.ventas = eventos, entradas, ventas

    def crear(self, datos: EventoCrear):
        if self.lugares.obtener(datos.lugar_id) is None:
            raise NoEncontrado("Lugar no encontrado")
        sectores = self.sectores.de_lugar(datos.lugar_id)
        recibidos = [p.sector_id for p in datos.precios]
        if not sectores:
            raise SolicitudInvalida("El lugar debe tener al menos un sector")
        if len(recibidos) != len(set(recibidos)):
            raise SolicitudInvalida("No se puede repetir un sector en los precios")
        if set(recibidos) != {s.id for s in sectores}:
            raise SolicitudInvalida("Debe definir un precio para cada sector del lugar")
        try:
            evento = Evento(lugar_id=datos.lugar_id, nombre=datos.nombre, fecha=datos.fecha)
            self.eventos.agregar(evento)
            self.db.flush()
            tarifas = {p.sector_id: p.precio for p in datos.precios}
            for sector in sectores:
                self.db.add(PrecioSector(evento_id=evento.id, sector_id=sector.id, precio=tarifas[sector.id]))
                for numero in range(1, sector.capacidad + 1):
                    self.entradas.agregar(Entrada(
                        evento_id=evento.id, sector_id=sector.id, numero=numero,
                        estado="Disponible", codigo_qr=secrets.token_urlsafe(24),
                    ))
            self.db.commit()
            self.db.refresh(evento)
            return evento
        except Exception:
            self.db.rollback()
            raise

    def listar(self):
        return self.eventos.listar()

    def obtener(self, evento_id: int):
        evento = self.eventos.obtener(evento_id)
        if evento is None:
            raise NoEncontrado("Evento no encontrado")
        return evento

    def _liberar_vencidas(self):
        self.db.execute(text("BEGIN IMMEDIATE"))
        try:
            ReservasServicio(self.ventas).liberar_vencidas()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def disponibilidad(self, evento_id: int):
        self._liberar_vencidas()
        evento = self.obtener(evento_id)
        resultado = []
        for tarifa in evento.precios:
            sector = tarifa.sector
            resultado.append({
                "sector_id": sector.id, "sector": sector.nombre, "capacidad": sector.capacidad,
                "disponibles": self.entradas.contar_disponibles(evento_id, sector.id),
                "precio": tarifa.precio,
            })
        return {"evento_id": evento.id, "sectores": sorted(resultado, key=lambda x: x["sector_id"])}

    def entradas_disponibles(self, evento_id: int, sector_id: int):
        self._liberar_vencidas()
        evento = self.obtener(evento_id)
        if not any(x.sector_id == sector_id for x in evento.precios):
            raise SinPrecio("No existe ese sector con precio para el evento")
        return [{"entrada_id": x.id, "numero": x.numero}
                for x in self.entradas.disponibles(evento_id, sector_id)]
