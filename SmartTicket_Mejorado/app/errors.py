"""Traducción de excepciones independientes del dominio a HTTP."""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    ErrorNegocio, NoEncontrado, CantidadInvalida, CapacidadInsuficiente,
    SolicitudInvalida, DisponibilidadPerdida, EntradaYaUtilizada,
    TicketNoEmitido, ConflictoEstado, EventoOtroDia, PagoDenegado, NoAutorizado,
)


def codigo_http(error: ErrorNegocio) -> int:
    # Primero los casos específicos; el dominio no conoce HTTP.
    if isinstance(error, NoEncontrado):
        return 404
    if isinstance(error, PagoDenegado):
        return 402
    if isinstance(error, NoAutorizado):
        return 403
    if isinstance(error, (CantidadInvalida, CapacidadInsuficiente, SolicitudInvalida)):
        return 400
    if isinstance(error, (DisponibilidadPerdida, EntradaYaUtilizada, TicketNoEmitido,
                          ConflictoEstado, EventoOtroDia)):
        return 409
    return 400


async def manejar_error_negocio(_request: Request, exc: ErrorNegocio):
    return JSONResponse(status_code=codigo_http(exc), content={"detail": exc.mensaje})
