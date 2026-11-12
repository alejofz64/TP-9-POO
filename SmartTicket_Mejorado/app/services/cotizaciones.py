"""HU1: precio y stock, sin reservar entradas. El controlador no contiene reglas."""
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.domain.exceptions import (
    CantidadInvalida, CapacidadInsuficiente, DisponibilidadPerdida, SolicitudInvalida, SinPrecio,
)
from app.repositories import EntradaRepositorio, PrecioRepositorio, VentaRepositorio
from app.schemas import SolicitudCotizacion
from app.services.reservas import ReservasServicio


def validar_seleccion(cantidad: int, ids: list[int] | None) -> None:
    if cantidad <= 0:
        raise CantidadInvalida("La cantidad de entradas solicitadas debe ser mayor a cero")
    if ids is not None and (len(ids) != cantidad or len(set(ids)) != cantidad):
        raise SolicitudInvalida("La cantidad de IDs debe coincidir con la cantidad solicitada y no contener duplicados")


def seleccionar_entradas(repo: EntradaRepositorio, evento_id: int, sector_id: int,
                        cantidad: int, ids: list[int] | None):
    """Selección exacta del profesor: valida cantidad, pertenencia, unicidad y estado."""
    validar_seleccion(cantidad, ids)
    if ids is None:
        entradas = repo.disponibles(evento_id, sector_id, cantidad)
    else:
        encontradas = repo.por_ids(ids)
        por_id = {entrada.id: entrada for entrada in encontradas}
        entradas = [por_id[x] for x in ids if x in por_id]
        if len(entradas) != cantidad:
            raise DisponibilidadPerdida("Los lugares seleccionados ya no se encuentran disponibles")
    if len(entradas) != cantidad or any(
        x.estado != "Disponible" or x.evento_id != evento_id or x.sector_id != sector_id
        for x in entradas
    ):
        raise DisponibilidadPerdida("Los lugares seleccionados ya no se encuentran disponibles")
    return entradas


class CotizacionServicio:
    def __init__(self, db: Session, entradas: EntradaRepositorio, precios: PrecioRepositorio,
                 ventas: VentaRepositorio):
        self.db, self.entradas, self.precios, self.ventas = db, entradas, precios, ventas

    def cotizar(self, datos: SolicitudCotizacion):
        validar_seleccion(datos.cantidad, datos.entrada_ids)
        # Vencimientos y lectura de stock deben verse consistentemente.
        try:
            self.db.execute(text("BEGIN IMMEDIATE"))
            ReservasServicio(self.ventas).liberar_vencidas()
            precio = self.precios.del_sector(datos.evento_id, datos.sector_id)
            if precio is None:
                raise SinPrecio("No existe ese sector con precio para el evento")
            if datos.entrada_ids is None:
                if self.entradas.contar_disponibles(datos.evento_id, datos.sector_id) < datos.cantidad:
                    raise CapacidadInsuficiente("Capacidad insuficiente o entradas no disponibles")
            else:
                try:
                    seleccionar_entradas(self.entradas, datos.evento_id, datos.sector_id,
                                        datos.cantidad, datos.entrada_ids)
                except DisponibilidadPerdida as e:
                    raise CapacidadInsuficiente("Capacidad insuficiente o entradas no disponibles") from e
            subtotal = precio.subtotal(datos.cantidad)
            self.db.commit()
            return {
                "evento_id": datos.evento_id, "sector_id": datos.sector_id,
                "cantidad": datos.cantidad, "precio_unitario": precio.precio,
                "subtotal": subtotal, "total": subtotal,
            }
        except Exception:
            self.db.rollback()
            raise
