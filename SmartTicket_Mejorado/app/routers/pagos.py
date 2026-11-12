from fastapi import APIRouter, Depends, Header
from app.dependencies import get_pagos
from app.schemas import SolicitudPago, SolicitudWebhook, VentaLeer, VentaCreada
from app.services.pagos import PagoServicio

router = APIRouter(tags=["HU2 - Pagos"])

@router.post("/iniciar-pago", response_model=VentaCreada)
def iniciar_pago(datos: SolicitudPago, servicio: PagoServicio = Depends(get_pagos)):
    return servicio.iniciar_pago(datos)

@router.get("/ventas/{venta_id}", response_model=VentaLeer)
def consultar_venta(venta_id: int, token: str | None = Header(default=None, alias="X-Venta-Token"),
                   servicio: PagoServicio = Depends(get_pagos)):
    return servicio.obtener_venta(venta_id, token)

@router.post("/webhook-pagos", response_model=VentaLeer)
def webhook_pagos(datos: SolicitudWebhook,
                  secreto: str | None = Header(default=None, alias="X-Webhook-Secret"),
                  servicio: PagoServicio = Depends(get_pagos)):
    return servicio.procesar_webhook(datos, secreto)
