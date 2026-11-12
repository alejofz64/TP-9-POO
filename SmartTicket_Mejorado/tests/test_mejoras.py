"""Cobertura extra de las correcciones inspiradas en el proyecto del profesor."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from sqlalchemy import select
from app.domain.exceptions import EntradaYaUtilizada, TicketNoEmitido, ConflictoEstado
from app.models import Entrada, Venta
from app.services.reservas import ahora_utc_naive


def _seleccion(caso, entrada_ids, token="tok_aprobada", sector_id=None):
    return caso["post"]("/iniciar-pago", {
        "cliente_id": caso["cliente"]["id"],
        "evento_id": caso["evento"]["id"],
        "sector_id": sector_id or caso["platea"]["id"],
        "cantidad": len(entrada_ids), "entrada_ids": entrada_ids,
        "tarjeta_token": token,
    })


def test_seleccion_de_entradas_especificas(caso):
    cliente = caso["client"]
    evento = caso["evento"]["id"]
    sector = caso["platea"]["id"]
    disponibles = cliente.get(f"/eventos/{evento}/sectores/{sector}/entradas").json()
    assert len(disponibles) == 5
    ids = [disponibles[3]["entrada_id"], disponibles[1]["entrada_id"]]
    r = _seleccion(caso, ids)
    assert r.status_code == 200, r.text
    assert {x["entrada_id"] for x in r.json()["entradas"]} == set(ids)
    assert _seleccion(caso, ids).status_code == 409  # ya fueron compradas


def test_ids_repetidos_y_cantidad_distinta_rechazados(caso):
    entrada_id = caso["client"].get(
        f"/eventos/{caso['evento']['id']}/sectores/{caso['platea']['id']}/entradas"
    ).json()[0]["entrada_id"]
    response = _seleccion(caso, [entrada_id, entrada_id])
    assert response.status_code == 400
    assert "duplicados" in response.json()["detail"]
    otro = caso["post"]("/iniciar-pago", {
        "cliente_id": caso["cliente"]["id"], "evento_id": caso["evento"]["id"],
        "sector_id": caso["platea"]["id"], "cantidad": 2,
        "entrada_ids": [entrada_id], "tarjeta_token": "tok_aprobada",
    })
    assert otro.status_code == 400


def test_entrada_de_otro_sector_no_se_puede_comprar(caso):
    vip_id = caso["client"].get(
        f"/eventos/{caso['evento']['id']}/sectores/{caso['vip']['id']}/entradas"
    ).json()[0]["entrada_id"]
    response = _seleccion(caso, [vip_id], sector_id=caso["platea"]["id"])
    assert response.status_code == 409


def test_cotizacion_entrada_elegida_y_stock(caso):
    ids = [x["entrada_id"] for x in caso["client"].get(
        f"/eventos/{caso['evento']['id']}/sectores/{caso['platea']['id']}/entradas"
    ).json()[:2]]
    payload = {"evento_id": caso["evento"]["id"], "sector_id": caso["platea"]["id"],
               "cantidad": 2, "entrada_ids": ids}
    assert caso["post"]("/cotizar", payload).status_code == 200
    assert _seleccion(caso, [ids[0]]).status_code == 200
    r = caso["post"]("/cotizar", payload)
    assert r.status_code == 400


def test_token_venta_no_permite_lectura_anonima_de_qr(caso):
    response = caso["pagar"]().json()
    id = response["venta_id"]
    assert caso["client"].get(f"/ventas/{id}").status_code == 403
    assert caso["client"].get(f"/ventas/{id}", headers={"X-Venta-Token":"incorrecto"}).status_code == 403
    ok = caso["client"].get(f"/ventas/{id}", headers={"X-Venta-Token":response["token_consulta"]})
    assert ok.status_code == 200
    assert "token_consulta" not in ok.json()
    assert ok.json()["entradas"][0]["codigo_qr"]


def test_reserva_vencida_se_libera_antes_de_cotizar_y_no_puede_reactivarse(caso):
    r = caso["pagar"](token="tok_pendiente").json()
    with caso["sessions"]() as db:
        venta = db.get(Venta, r["venta_id"])
        venta.expira_en = ahora_utc_naive() - timedelta(minutes=1)
        db.commit()
    assert caso["cotizar"](cantidad=5).status_code == 200
    with caso["sessions"]() as db:
        assert db.get(Venta, r["venta_id"]).estado == "Cancelada"
        assert all(x.estado == "Disponible" for x in db.scalars(select(Entrada)))
    webhook = caso["client"].post("/webhook-pagos", json={"venta_id":r["venta_id"], "resultado":"APROBADO"},
                                  headers={"X-Webhook-Secret":"solo-demostracion-cambiar"})
    assert webhook.status_code == 409
    assert caso["pagar"](cantidad=5).status_code == 200


def test_estado_entrada_encapsulado(caso):
    with caso["sessions"]() as db:
        entrada = db.scalar(select(Entrada))
        with pytest.raises(TicketNoEmitido):
            entrada.validar_y_registrar_ingreso(ahora_utc_naive())
        with pytest.raises(ConflictoEstado):
            entrada.emitir()
        entrada.reservar()
        entrada.emitir()
        entrada.validar_y_registrar_ingreso(ahora_utc_naive())
        fecha = entrada.hora_ingreso
        with pytest.raises(EntradaYaUtilizada):
            entrada.validar_y_registrar_ingreso(ahora_utc_naive())
        assert entrada.hora_ingreso == fecha


def test_concurrencia_mismo_asiento_elegido(caso):
    vip_id = caso["client"].get(
        f"/eventos/{caso['evento']['id']}/sectores/{caso['vip']['id']}/entradas"
    ).json()[0]["entrada_id"]
    def pagar(_):
        return _seleccion(caso, [vip_id], sector_id=caso["vip"]["id"]).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(pagar, range(2))) == [200, 409]
