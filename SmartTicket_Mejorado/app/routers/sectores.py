from fastapi import APIRouter, Depends
from app.dependencies import get_sectores
from app.schemas import SectorCrear, SectorLeer
from app.services.sectores import SectorServicio

router = APIRouter(tags=["Sectores"])

@router.post("/sectores", response_model=SectorLeer, status_code=201)
def crear(datos: SectorCrear, servicio: SectorServicio = Depends(get_sectores)):
    return servicio.crear(datos)

@router.get("/sectores", response_model=list[SectorLeer])
def listar(servicio: SectorServicio = Depends(get_sectores)):
    return servicio.listar()

@router.get("/sectores/{sector_id}", response_model=SectorLeer)
def obtener(sector_id: int, servicio: SectorServicio = Depends(get_sectores)):
    return servicio.obtener(sector_id)
