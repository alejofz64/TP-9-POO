from fastapi import APIRouter, Depends
from app.dependencies import get_cotizador
from app.schemas import SolicitudCotizacion, Cotizacion
from app.services.cotizaciones import CotizacionServicio

router = APIRouter(tags=["HU1 - Cotización"])

@router.post("/cotizar", response_model=Cotizacion)
def cotizar(datos: SolicitudCotizacion, servicio: CotizacionServicio = Depends(get_cotizador)):
    return servicio.cotizar(datos)
