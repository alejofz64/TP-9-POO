import pytest


def test_hu1_cotizacion_correcta_24000(caso):
    r = caso["cotizar"]()
    assert r.status_code == 200
    assert r.json()["subtotal"] == "24000.00"
    assert r.json()["total"] == "24000.00"
    assert r.json()["precio_unitario"] == "12000.00"


def test_hu1_vip_sin_stock_suficiente(caso):
    r = caso["cotizar"](sector_id=caso["vip"]["id"], cantidad=3)
    assert r.status_code == 400
    assert r.json()["detail"] == "Capacidad insuficiente o entradas no disponibles"


@pytest.mark.parametrize("cantidad", [0, -1, -9])
def test_hu1_cantidad_invalida(caso, cantidad):
    r = caso["cotizar"](cantidad=cantidad)
    assert r.status_code == 400
    assert r.json()["detail"] == "La cantidad de entradas solicitadas debe ser mayor a cero"


def test_hu1_precio_por_evento_no_por_sector(caso):
    otro = caso["post"]("/eventos", {
        "nombre": "Teatro", "lugar_id": caso["lugar"]["id"],
        "fecha": caso["evento"]["fecha"],
        "precios": [
            {"sector_id": caso["platea"]["id"], "precio": "345.60"},
            {"sector_id": caso["vip"]["id"], "precio": "9999.00"},
        ],
    })
    assert otro.status_code == 201
    r = caso["post"]("/cotizar", {
        "evento_id": otro.json()["id"], "sector_id": caso["platea"]["id"], "cantidad": 2,
    })
    assert r.status_code == 200
    assert r.json()["total"] == "691.20"
