"""DIP: contrato de pasarela y adaptador simulado sin pagos reales."""
from decimal import Decimal
from typing import Literal, Protocol

ResultadoPasarela = Literal["APROBADO", "RECHAZADO", "PENDIENTE"]


class PasarelaPago(Protocol):
    def autorizar(self, tarjeta_token: str, total: Decimal) -> ResultadoPasarela:
        ...


class PasarelaSimulada:
    """NO procesa números de tarjeta: solo acepta tokens de prueba."""

    def autorizar(self, tarjeta_token: str, total: Decimal) -> ResultadoPasarela:
        if tarjeta_token == "tok_aprobada":
            return "APROBADO"
        if tarjeta_token == "tok_pendiente":
            return "PENDIENTE"
        return "RECHAZADO"
