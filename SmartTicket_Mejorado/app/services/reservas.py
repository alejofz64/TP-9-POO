"""Reglas de vencimiento: sin scheduler; limpieza al consultar/comprar (lazy expiry)."""
import os
from datetime import datetime, timedelta, timezone
from app.repositories import VentaRepositorio


def ahora_utc_naive() -> datetime:
    # SQLite no conserva offset: todos los vencimientos se guardan en UTC naive.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calcular_vencimiento() -> datetime:
    minutos = max(1, int(os.getenv("SMARTTICKET_RESERVA_MINUTOS", "15")))
    return ahora_utc_naive() + timedelta(minutes=minutos)


class ReservasServicio:
    def __init__(self, ventas: VentaRepositorio):
        self.ventas = ventas

    def liberar_vencidas(self):
        """El caller debe poseer transacción de escritura antes de invocarlo."""
        vencidas = self.ventas.pendientes_vencidas(ahora_utc_naive())
        for venta in vencidas:
            for linea in venta.lineas:
                linea.entrada.liberar_reserva()
            venta.cancelar()
        # SessionLocal usa autoflush=False: las consultas posteriores de stock
        # necesitan que se hayan volcado los cambios, sin confirmarlos aún.
        if vencidas:
            self.ventas.db.flush()
        return len(vencidas)
