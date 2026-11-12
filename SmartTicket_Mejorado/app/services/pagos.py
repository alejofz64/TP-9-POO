"""HU2: stock, pasarela intercambiable, QR privado, webhooks y reservas vencidas."""
import os
import secrets

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.exceptions import (
    NoEncontrado, SinPrecio, DisponibilidadPerdida, PagoDenegado,
    NoAutorizado, ConflictoEstado,
)
from app.models import Venta, VentaEntrada
from app.payments import PasarelaPago
from app.repositories import ClienteRepositorio, EntradaRepositorio, PrecioRepositorio, VentaRepositorio
from app.schemas import SolicitudPago, SolicitudWebhook
from app.services.cotizaciones import seleccionar_entradas, validar_seleccion
from app.services.reservas import ReservasServicio, calcular_vencimiento


class PagoServicio:
    def __init__(self, db: Session, clientes: ClienteRepositorio,
                 entradas: EntradaRepositorio, precios: PrecioRepositorio,
                 ventas: VentaRepositorio, pasarela: PasarelaPago):
        self.db, self.clientes = db, clientes
        self.entradas, self.precios, self.ventas, self.pasarela = entradas, precios, ventas, pasarela

    @staticmethod
    def _respuesta(venta: Venta, incluir_token: bool = False):
        respuesta = {
            "venta_id": venta.id, "cliente_id": venta.cliente_id,
            "estado": venta.estado, "total": venta.total,
            "entradas": [],
        }
        # QR únicamente si se pagó. La venta tiene un token de consulta no predecible.
        if venta.estado == "Pagada":
            respuesta["entradas"] = [{
                "entrada_id": linea.entrada.id, "sector_id": linea.entrada.sector_id,
                "numero": linea.entrada.numero, "codigo_qr": linea.entrada.codigo_qr,
                "estado": linea.entrada.estado,
            } for linea in venta.lineas]
        if incluir_token:
            respuesta["token_consulta"] = venta.token_consulta
        return respuesta

    def iniciar_pago(self, datos: SolicitudPago):
        validar_seleccion(datos.cantidad, datos.entrada_ids)
        try:
            # SQLite: SERIALIZAR transacciones de compra antes de consultar disponibilidad.
            # No sería suficiente en PostgreSQL: allí se usarían FOR UPDATE/UPDATE condicional.
            self.db.execute(text("BEGIN IMMEDIATE"))
            ReservasServicio(self.ventas).liberar_vencidas()
            if self.clientes.obtener(datos.cliente_id) is None:
                raise NoEncontrado("Cliente no encontrado")
            precio = self.precios.del_sector(datos.evento_id, datos.sector_id)
            if precio is None:
                raise SinPrecio("No existe ese sector con precio para el evento")
            entradas = seleccionar_entradas(
                self.entradas, datos.evento_id, datos.sector_id,
                datos.cantidad, datos.entrada_ids,
            )
            # Verificación de disponibilidad anterior a la llamada a la pasarela.
            total = precio.subtotal(datos.cantidad)
            resultado = self.pasarela.autorizar(datos.tarjeta_token, total)
            if resultado == "RECHAZADO":
                raise PagoDenegado("Pago denegado")
            venta = Venta(
                cliente_id=datos.cliente_id, estado="Pendiente", total=total,
                token_consulta=secrets.token_urlsafe(32),
                expira_en=calcular_vencimiento() if resultado == "PENDIENTE" else None,
            )
            self.ventas.agregar(venta)
            self.db.flush()
            for entrada in entradas:
                entrada.reservar()
                self.db.add(VentaEntrada(venta_id=venta.id, entrada_id=entrada.id))
            if resultado == "APROBADO":
                for entrada in entradas:
                    entrada.emitir()
                venta.pagar()
            self.db.commit()
            recargada = self.ventas.obtener(venta.id)
            return self._respuesta(recargada, incluir_token=True)
        except Exception:
            self.db.rollback()
            raise

    def obtener_venta(self, venta_id: int, token_consulta: str | None):
        # Evitar acceso anónimo a los QR de otras personas.
        try:
            self.db.execute(text("BEGIN IMMEDIATE"))
            ReservasServicio(self.ventas).liberar_vencidas()
            venta = self.ventas.obtener(venta_id)
            if venta is None:
                raise NoEncontrado("Venta no encontrada")
            if not token_consulta or not secrets.compare_digest(token_consulta, venta.token_consulta):
                raise NoAutorizado("No autorizado para consultar esta venta")
            self.db.commit()
            return self._respuesta(venta)
        except Exception:
            self.db.rollback()
            raise

    def procesar_webhook(self, datos: SolicitudWebhook, secreto: str | None):
        configurado = os.getenv("SMARTTICKET_WEBHOOK_SECRET", "solo-demostracion-cambiar")
        if not secreto or not secrets.compare_digest(secreto, configurado):
            raise NoAutorizado("Webhook no autorizado")
        try:
            self.db.execute(text("BEGIN IMMEDIATE"))
            ReservasServicio(self.ventas).liberar_vencidas()
            venta = self.ventas.obtener(datos.venta_id)
            if venta is None:
                raise NoEncontrado("Venta no encontrada")
            destino = "Pagada" if datos.resultado == "APROBADO" else "Cancelada"
            if venta.estado == destino:
                self.db.commit()
                return self._respuesta(venta)
            if venta.estado != "Pendiente":
                raise ConflictoEstado("Venta ya finalizada con un resultado diferente o reserva vencida")
            if any(linea.entrada.estado != "Reservada" for linea in venta.lineas):
                raise ConflictoEstado("Estado de entrada incompatible con la venta")
            if destino == "Pagada":
                for linea in venta.lineas:
                    linea.entrada.emitir()
                venta.pagar()
            else:
                for linea in venta.lineas:
                    linea.entrada.liberar_reserva()
                venta.cancelar()
            self.db.commit()
            return self._respuesta(venta)
        except Exception:
            self.db.rollback()
            raise
