from fastapi import APIRouter, Depends
from app.dependencies import get_lugares
from app.schemas import LugarCrear, LugarLeer
from app.services.lugares import LugarServicio

router = APIRouter(tags=["Lugares"])

@router.post("/lugares", response_model=LugarLeer, status_code=201)
def crear(datos: LugarCrear, servicio: LugarServicio = Depends(get_lugares)):
    return servicio.crear(datos)

@router.get("/lugares", response_model=list[LugarLeer])
def listar(servicio: LugarServicio = Depends(get_lugares)):
    return servicio.listar()

@router.get("/lugares/{lugar_id}", response_model=LugarLeer)
def obtener(lugar_id: int, servicio: LugarServicio = Depends(get_lugares)):
    return servicio.obtener(lugar_id)
