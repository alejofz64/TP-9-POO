"""API FastAPI: composición de controladores. Ejecutar: uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app import models  # noqa: F401 - registrar tablas
from app.domain.exceptions import ErrorNegocio
from app.errors import manejar_error_negocio
from app.routers import lugares, sectores, clientes, eventos, cotizaciones, pagos, accesos


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SmartTicket - TP9 GRASP y SOLID (Mejorado)",
    description="Catálogo, cotización, pago simulado, reservas y control de acceso.",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_exception_handler(ErrorNegocio, manejar_error_negocio)
# Desarrollo local del frontend, no abrir a cualquier origen en producción.
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False, allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Venta-Token", "X-Webhook-Secret"],
)
for modulo in (lugares, sectores, clientes, eventos, cotizaciones, pagos, accesos):
    app.include_router(modulo.router)


@app.get("/salud", tags=["Sistema"])
def salud():
    return {"estado": "ok", "servicio": "SmartTicket", "version": "2.0.0"}
