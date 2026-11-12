from fastapi import APIRouter, Depends
from app.dependencies import get_accesos
from app.schemas import SolicitudAcceso, ResultadoAcceso
from app.services.accesos import AccesoServicio

router = APIRouter(tags=["HU3 - Accesos"])

@router.post("/escanear-acceso", response_model=ResultadoAcceso)
def escanear_acceso(datos: SolicitudAcceso, servicio: AccesoServicio = Depends(get_accesos)):
    return servicio.escanear(datos.codigo_qr)
