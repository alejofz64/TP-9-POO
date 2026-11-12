"""DTO de entrada/salida: FastAPI no expone directamente las entidades ORM."""
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DesdeORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LugarCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    direccion: str = Field(min_length=1, max_length=250)


class LugarLeer(LugarCrear, DesdeORM):
    id: int


class SectorCrear(BaseModel):
    lugar_id: int
    nombre: str = Field(min_length=1, max_length=100)
    capacidad: int = Field(gt=0)


class SectorLeer(SectorCrear, DesdeORM):
    id: int


class ClienteCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)


class ClienteLeer(ClienteCrear, DesdeORM):
    id: int


class PrecioCrear(BaseModel):
    sector_id: int
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class PrecioLeer(DesdeORM):
    sector_id: int
    precio: Decimal


class EventoCrear(BaseModel):
    lugar_id: int
    nombre: str = Field(min_length=1, max_length=150)
    fecha: date
    precios: list[PrecioCrear] = Field(min_length=1)


class EventoLeer(DesdeORM):
    id: int
    lugar_id: int
    nombre: str
    fecha: date
    precios: list[PrecioLeer]


class DisponibilidadSector(BaseModel):
    sector_id: int
    sector: str
    capacidad: int
    disponibles: int
    precio: Decimal


class DisponibilidadEvento(BaseModel):
    evento_id: int
    sectores: list[DisponibilidadSector]


class EntradaDisponible(BaseModel):
    entrada_id: int
    numero: int


class SolicitudCotizacion(BaseModel):
    evento_id: int
    sector_id: int
    cantidad: int
    entrada_ids: list[int] | None = Field(
        default=None, description="Opcional: entradas numeradas específicas. Debe coincidir con cantidad."
    )


class Cotizacion(BaseModel):
    evento_id: int
    sector_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    total: Decimal


class SolicitudPago(SolicitudCotizacion):
    cliente_id: int
    tarjeta_token: str = Field(min_length=1, description="Prueba: tok_aprobada, tok_rechazada o tok_pendiente")


class EntradaEmitida(BaseModel):
    entrada_id: int
    sector_id: int
    numero: int
    codigo_qr: str
    estado: str


class VentaLeer(BaseModel):
    venta_id: int
    cliente_id: int
    estado: str
    total: Decimal
    entradas: list[EntradaEmitida]


class VentaCreada(VentaLeer):
    token_consulta: str = Field(description="Guardalo: se requiere para GET /ventas/{id}")


class SolicitudWebhook(BaseModel):
    venta_id: int
    resultado: Literal["APROBADO", "RECHAZADO"]


class SolicitudAcceso(BaseModel):
    codigo_qr: str = Field(min_length=1)


class ResultadoAcceso(BaseModel):
    mensaje: str
    entrada_id: int
    hora_ingreso: str
