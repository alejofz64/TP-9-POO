"""Cada test usa una SQLite real y aislada en un archivo temporal."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_session
from app.main import app


@pytest.fixture
def entorno(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 15})

    @event.listens_for(engine, "connect")
    def claves_foraneas(con, _):
        con.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def sesion_prueba():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_session] = sesion_prueba
    with TestClient(app) as client:
        yield client, sessions
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def caso(entorno):
    client, sessions = entorno
    post = lambda url, data: client.post(url, json=data)
    lugar = post("/lugares", {"nombre": "Estadio Central", "direccion": "Avenida Uno 100"}).json()
    platea = post("/sectores", {"lugar_id": lugar["id"], "nombre": "Platea", "capacidad": 5}).json()
    vip = post("/sectores", {"lugar_id": lugar["id"], "nombre": "VIP", "capacidad": 1}).json()
    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date().isoformat()
    evento_response = post("/eventos", {
        "nombre": "Rock Fest", "lugar_id": lugar["id"], "fecha": hoy,
        "precios": [
            {"sector_id": platea["id"], "precio": "12000"},
            {"sector_id": vip["id"], "precio": "50000"},
        ],
    })
    assert evento_response.status_code == 201, evento_response.text
    evento = evento_response.json()
    cliente = post("/clientes", {"nombre": "Público", "email": "publico@example.com"}).json()

    def cotizar(sector_id=None, cantidad=2):
        return post("/cotizar", {
            "evento_id": evento["id"], "sector_id": sector_id or platea["id"], "cantidad": cantidad,
        })

    def pagar(token="tok_aprobada", sector_id=None, cantidad=2):
        return post("/iniciar-pago", {
            "cliente_id": cliente["id"], "evento_id": evento["id"],
            "sector_id": sector_id or platea["id"], "cantidad": cantidad,
            "tarjeta_token": token,
        })

    return {
        "client": client, "sessions": sessions, "lugar": lugar,
        "platea": platea, "vip": vip, "evento": evento, "cliente": cliente,
        "cotizar": cotizar, "pagar": pagar, "post": post,
    }
