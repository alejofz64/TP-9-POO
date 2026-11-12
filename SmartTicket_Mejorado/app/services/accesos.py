"""HU3: servicio coordinador; Entrada valida y cambia su propio estado."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.exceptions import EventoOtroDia, TicketInvalido
from app.repositories import EntradaRepositorio


class AccesoServicio:
    def __init__(self, db: Session, entradas: EntradaRepositorio):
        self.db, self.entradas = db, entradas

    def escanear(self, codigo_qr: str):
        try:
            self.db.execute(text("BEGIN IMMEDIATE"))
            entrada = self.entradas.por_qr(codigo_qr.strip())
            if entrada is None:
                raise TicketInvalido("Ticket Inválido o Inexistente")
            zona = ZoneInfo(os.getenv("SMARTTICKET_TIMEZONE", "America/Argentina/Buenos_Aires"))
            ahora = datetime.now(zona)
            # GRASP: el propio objeto rechaza estados inválidos sin que el
            # servicio conozca sus valores. La fecha es una regla del caso de uso.
            entrada.validar_estado_para_ingreso()
            if entrada.evento.fecha != ahora.date():
                raise EventoOtroDia("La entrada no corresponde a un evento del día")
            entrada.validar_y_registrar_ingreso(ahora)
            self.db.commit()
            return {
                "mensaje": "Acceso Permitido", "entrada_id": entrada.id,
                "hora_ingreso": entrada.hora_ingreso,
            }
        except Exception:
            self.db.rollback()
            raise
