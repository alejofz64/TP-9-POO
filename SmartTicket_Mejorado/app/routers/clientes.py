from fastapi import APIRouter, Depends
from app.dependencies import get_clientes
from app.schemas import ClienteCrear, ClienteLeer
from app.services.clientes import ClienteServicio

router = APIRouter(tags=["Clientes"])

@router.post("/clientes", response_model=ClienteLeer, status_code=201)
def crear(datos: ClienteCrear, servicio: ClienteServicio = Depends(get_clientes)):
    return servicio.crear(datos)

@router.get("/clientes", response_model=list[ClienteLeer])
def listar(servicio: ClienteServicio = Depends(get_clientes)):
    return servicio.listar()

@router.get("/clientes/{cliente_id}", response_model=ClienteLeer)
def obtener(cliente_id: int, servicio: ClienteServicio = Depends(get_clientes)):
    return servicio.obtener(cliente_id)
