"""Entidades del dominio SmartTicket y comportamiento de sus cambios de estado.

Un único módulo de entidades evita referencias circulares de SQLAlchemy; las capas
Repository/Service/Controller están separadas por responsabilidad.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.domain.exceptions import (
    CantidadInvalida, ConflictoEstado, EntradaYaUtilizada, TicketNoEmitido,
)


class Lugar(Base):
    __tablename__ = "lugares"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    direccion: Mapped[str] = mapped_column(String(250), nullable=False)
    sectores: Mapped[list[Sector]] = relationship(back_populates="lugar")


class Sector(Base):
    __tablename__ = "sectores"
    __table_args__ = (CheckConstraint("capacidad > 0", name="sector_capacidad_positiva"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    lugar_id: Mapped[int] = mapped_column(ForeignKey("lugares.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False)
    lugar: Mapped[Lugar] = relationship(back_populates="sectores")


class Evento(Base):
    __tablename__ = "eventos"
    id: Mapped[int] = mapped_column(primary_key=True)
    lugar_id: Mapped[int] = mapped_column(ForeignKey("lugares.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    lugar: Mapped[Lugar] = relationship()
    precios: Mapped[list[PrecioSector]] = relationship(back_populates="evento")


class PrecioSector(Base):
    __tablename__ = "precios_sector"
    __table_args__ = (
        UniqueConstraint("evento_id", "sector_id", name="uq_precio_por_evento_sector"),
        CheckConstraint("precio > 0", name="precio_positivo"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id"), nullable=False)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectores.id"), nullable=False)
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    evento: Mapped[Evento] = relationship(back_populates="precios")
    sector: Mapped[Sector] = relationship()

    def subtotal(self, cantidad: int) -> Decimal:
        """GRASP Experto: la tarifa conoce el precio unitario."""
        if cantidad <= 0:
            raise CantidadInvalida("La cantidad de entradas solicitadas debe ser mayor a cero")
        return (self.precio * Decimal(cantidad)).quantize(Decimal("0.01"))


class Cliente(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)


class Venta(Base):
    __tablename__ = "ventas"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(12), nullable=False, default="Pendiente")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expira_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    token_consulta: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    cliente: Mapped[Cliente] = relationship()
    lineas: Mapped[list[VentaEntrada]] = relationship(back_populates="venta")

    def pagar(self) -> None:
        if self.estado != "Pendiente":
            raise ConflictoEstado("La venta no puede pagarse en su estado actual")
        self.estado = "Pagada"
        self.expira_en = None

    def cancelar(self) -> None:
        if self.estado != "Pendiente":
            raise ConflictoEstado("La venta no puede cancelarse en su estado actual")
        self.estado = "Cancelada"
        self.expira_en = None


class Entrada(Base):
    __tablename__ = "entradas"
    __table_args__ = (UniqueConstraint("evento_id", "sector_id", "numero", name="uq_entrada_asiento"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id"), nullable=False, index=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectores.id"), nullable=False, index=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(12), nullable=False, default="Disponible")
    codigo_qr: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hora_ingreso: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evento: Mapped[Evento] = relationship()
    sector: Mapped[Sector] = relationship()

    def reservar(self) -> None:
        if self.estado != "Disponible":
            raise ConflictoEstado("Los lugares seleccionados ya no se encuentran disponibles")
        self.estado = "Reservada"

    def emitir(self) -> None:
        if self.estado != "Reservada":
            raise ConflictoEstado("Solo se pueden emitir entradas reservadas")
        self.estado = "Emitida"

    def liberar_reserva(self) -> None:
        if self.estado != "Reservada":
            raise ConflictoEstado("Solo se puede liberar una entrada reservada")
        self.estado = "Disponible"

    def validar_estado_para_ingreso(self) -> None:
        """La entidad (no el servicio) conoce si puede ser utilizada."""
        if self.estado == "Utilizada":
            raise EntradaYaUtilizada("Entrada ya utilizada")
        if self.estado != "Emitida":
            raise TicketNoEmitido("Ticket no emitido / Falta de pago")

    def validar_y_registrar_ingreso(self, ahora: datetime) -> None:
        """GRASP Experto: valida el estado y preserva la hora de uso original."""
        self.validar_estado_para_ingreso()
        self.estado = "Utilizada"
        self.hora_ingreso = ahora.isoformat(timespec="microseconds")


class VentaEntrada(Base):
    __tablename__ = "ventas_entradas"
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), primary_key=True)
    entrada_id: Mapped[int] = mapped_column(ForeignKey("entradas.id"), primary_key=True)
    venta: Mapped[Venta] = relationship(back_populates="lineas")
    entrada: Mapped[Entrada] = relationship()
