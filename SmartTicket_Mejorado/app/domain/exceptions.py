"""Excepciones del dominio: ninguna depende de FastAPI ni de códigos HTTP."""


class ErrorNegocio(Exception):
    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(mensaje)


class NoEncontrado(ErrorNegocio):
    pass


class SinPrecio(NoEncontrado):
    pass


class TicketInvalido(NoEncontrado):
    pass


class CantidadInvalida(ErrorNegocio):
    pass


class CapacidadInsuficiente(ErrorNegocio):
    pass


class SolicitudInvalida(ErrorNegocio):
    pass


class DisponibilidadPerdida(ErrorNegocio):
    pass


class EntradaYaUtilizada(ErrorNegocio):
    pass


class TicketNoEmitido(ErrorNegocio):
    pass


class ConflictoEstado(ErrorNegocio):
    pass


class EventoOtroDia(ErrorNegocio):
    pass


class PagoDenegado(ErrorNegocio):
    pass


class NoAutorizado(ErrorNegocio):
    pass
