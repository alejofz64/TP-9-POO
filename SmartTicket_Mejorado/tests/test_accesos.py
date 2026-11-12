from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.models import Entrada


def test_hu3_entrada_emitida_acceso_y_rechazo_duplicado(caso):
    datos = caso["pagar"]().json()
    codigo = datos["entradas"][0]["codigo_qr"]
    primero = caso["post"]("/escanear-acceso", {"codigo_qr": codigo})
    assert primero.status_code == 200
    assert primero.json()["mensaje"] == "Acceso Permitido"
    fecha_original = primero.json()["hora_ingreso"]
    assert datetime.fromisoformat(fecha_original).tzinfo is not None
    segundo = caso["post"]("/escanear-acceso", {"codigo_qr": codigo})
    assert segundo.status_code == 409
    assert segundo.json()["detail"] == "Entrada ya utilizada"
    with caso["sessions"]() as db:
        entrada = db.scalar(select(Entrada).where(Entrada.codigo_qr == codigo))
        assert entrada.estado == "Utilizada"
        assert entrada.hora_ingreso == fecha_original


def test_hu3_qr_falso(caso):
    r = caso["post"]("/escanear-acceso", {"codigo_qr": "qr-no-existente-123"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Ticket Inválido o Inexistente"


def test_hu3_qr_no_emitido_no_puede_ingresar(caso):
    with caso["sessions"]() as db:
        codigo = db.scalar(select(Entrada)).codigo_qr
    r = caso["post"]("/escanear-acceso", {"codigo_qr": codigo})
    assert r.status_code == 409
    assert r.json()["detail"] == "Ticket no emitido / Falta de pago"


def test_hu3_qr_reservado_no_puede_ingresar(caso):
    caso["pagar"](token="tok_pendiente")
    with caso["sessions"]() as db:
        codigo = db.scalar(select(Entrada).where(Entrada.estado == "Reservada")).codigo_qr
    r = caso["post"]("/escanear-acceso", {"codigo_qr": codigo})
    assert r.status_code == 409
    assert r.json()["detail"] == "Ticket no emitido / Falta de pago"


def test_hu3_entrada_de_otro_dia_no_es_valida(caso):
    # Evento diferente para el día siguiente, con entradas emitidas.
    manana = (datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date() + timedelta(days=1)).isoformat()
    evento = caso["post"]("/eventos", {
        "lugar_id": caso["lugar"]["id"], "nombre": "Evento mañana", "fecha": manana,
        "precios": [
            {"sector_id": caso["platea"]["id"], "precio": "500"},
            {"sector_id": caso["vip"]["id"], "precio": "700"},
        ],
    }).json()
    pagada = caso["post"]("/iniciar-pago", {
        "cliente_id": caso["cliente"]["id"], "evento_id": evento["id"],
        "sector_id": caso["platea"]["id"], "cantidad": 1, "tarjeta_token": "tok_aprobada",
    }).json()
    qr = pagada["entradas"][0]["codigo_qr"]
    r = caso["post"]("/escanear-acceso", {"codigo_qr": qr})
    assert r.status_code == 409
    assert r.json()["detail"] == "La entrada no corresponde a un evento del día"
