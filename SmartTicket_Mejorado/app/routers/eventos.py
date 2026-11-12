from fastapi import APIRouter, Depends
from app.dependencies import get_eventos
from app.schemas import EventoCrear, EventoLeer, DisponibilidadEvento, EntradaDisponible
from app.services.eventos import EventoServicio

router = APIRouter(tags=["Eventos"])

@router.post("/eventos", response_model=EventoLeer, status_code=201)
def crear(datos: EventoCrear, servicio: EventoServicio = Depends(get_eventos)):
    return servicio.crear(datos)

@router.get("/eventos", response_model=list[EventoLeer])
def listar(servicio: EventoServicio = Depends(get_eventos)):
    return servicio.listar()

@router.get("/eventos/{evento_id}", response_model=EventoLeer)
def obtener(evento_id: int, servicio: EventoServicio = Depends(get_eventos)):
    return servicio.obtener(evento_id)

@router.get("/eventos/{evento_id}/disponibilidad", response_model=DisponibilidadEvento)
def disponibilidad(evento_id: int, servicio: EventoServicio = Depends(get_eventos)):
    return servicio.disponibilidad(evento_id)

@router.get("/eventos/{evento_id}/sectores/{sector_id}/entradas", response_model=list[EntradaDisponible])
def entradas_disponibles(evento_id: int, sector_id: int, servicio: EventoServicio = Depends(get_eventos)):
    return servicio.entradas_disponibles(evento_id, sector_id)
