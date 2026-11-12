from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from sqlalchemy import select

from app.dependencies import get_pasarela
from app.main import app
from app.models import Entrada, Venta


def test_hu2_pago_aprobado_emite_y_crea_venta(caso):
    r = caso["pagar"]()
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["estado"] == "Pagada"
    assert data["total"] == "24000.00"
    assert len(data["entradas"]) == 2
    assert all(e["estado"] == "Emitida" and e["codigo_qr"] for e in data["entradas"])
    assert caso["client"].get(f"/ventas/{data['venta_id']}").status_code == 403
    consulta = caso["client"].get(
        f"/ventas/{data['venta_id']}", headers={"X-Venta-Token": data["token_consulta"]}
    )
    assert consulta.status_code == 200
    assert consulta.json() == {k: v for k, v in data.items() if k != "token_consulta"}


def test_hu2_pago_rechazado_no_toca_entradas(caso):
    r = caso["pagar"](token="tok_rechazada")
    assert r.status_code == 402
    assert r.json()["detail"] == "Pago denegado"
    with caso["sessions"]() as db:
        assert db.scalars(select(Venta)).all() == []
        assert all(x.estado == "Disponible" for x in db.scalars(select(Entrada)))


def test_hu2_stock_desaparecido_se_detecta_antes_de_pasarela(caso):
    class EspiaPasarela:
        def __init__(self):
            self.llamadas = 0

        def autorizar(self, token: str, total: Decimal):
            self.llamadas += 1
            return "APROBADO"

    assert caso["cotizar"](cantidad=5).status_code == 200
    assert caso["pagar"](cantidad=5).status_code == 200
    espia = EspiaPasarela()
    app.dependency_overrides[get_pasarela] = lambda: espia
    try:
        r = caso["pagar"](cantidad=5)
        assert r.status_code == 409
        assert r.json()["detail"] == "Los lugares seleccionados ya no se encuentran disponibles"
        assert espia.llamadas == 0
    finally:
        app.dependency_overrides.pop(get_pasarela, None)


def test_hu2_no_doble_venta_con_dos_pagos_concurrentes(caso):
    # Ambos compiten por la única entrada VIP: uno recibe 200 y otro 409.
    def comprar(_):
        return caso["pagar"](sector_id=caso["vip"]["id"], cantidad=1).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = sorted(pool.map(comprar, range(2)))
    assert resultados == [200, 409]
    with caso["sessions"]() as db:
        assert len(db.scalars(select(Venta)).all()) == 1


def test_webhook_aprueba_pendiente_y_es_idempotente(caso):
    pendiente = caso["pagar"](token="tok_pendiente")
    assert pendiente.status_code == 200
    datos = pendiente.json()
    assert datos["estado"] == "Pendiente"
    assert datos["entradas"] == []  # QR ocultos mientras no se confirme el pago
    webhook = {"venta_id": datos["venta_id"], "resultado": "APROBADO"}
    headers = {"X-Webhook-Secret": "solo-demostracion-cambiar"}
    sin_auth = caso["client"].post("/webhook-pagos", json=webhook)
    assert sin_auth.status_code == 403
    ok = caso["client"].post("/webhook-pagos", json=webhook, headers=headers)
    assert ok.status_code == 200 and ok.json()["estado"] == "Pagada"
    assert len(ok.json()["entradas"]) == 2
    otra_vez = caso["client"].post("/webhook-pagos", json=webhook, headers=headers)
    assert otra_vez.status_code == 200
    assert otra_vez.json() == ok.json()


def test_webhook_rechazado_cancela_y_devuelve_disponibilidad(caso):
    pendiente = caso["pagar"](token="tok_pendiente").json()
    assert caso["cotizar"](cantidad=4).status_code == 400
    r = caso["client"].post("/webhook-pagos", json={
        "venta_id": pendiente["venta_id"], "resultado": "RECHAZADO",
    }, headers={"X-Webhook-Secret": "solo-demostracion-cambiar"})
    assert r.status_code == 200
    assert r.json()["estado"] == "Cancelada"
    assert caso["cotizar"](cantidad=5).status_code == 200
    # Las mismas entradas liberadas pueden venderse nuevamente tras la cancelación.
    recompra = caso["pagar"](cantidad=5)
    assert recompra.status_code == 200, recompra.text
    assert recompra.json()["estado"] == "Pagada"
