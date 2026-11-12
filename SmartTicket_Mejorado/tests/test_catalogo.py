from datetime import date

from sqlalchemy import func, select

from app.models import Entrada


def test_abm_entidades_y_entradas_preexistentes(caso):
    c = caso["client"]
    e = caso["evento"]
    assert c.get("/salud").json()["estado"] == "ok"
    assert c.get("/lugares").json()[0]["id"] == caso["lugar"]["id"]
    assert len(c.get("/sectores").json()) == 2
    assert c.get(f"/eventos/{e['id']}").json()["nombre"] == "Rock Fest"
    assert c.get(f"/clientes/{caso['cliente']['id']}").status_code == 200
    with caso["sessions"]() as db:
        entradas = list(db.scalars(select(Entrada).where(Entrada.evento_id == e["id"])))
        assert len(entradas) == 6  # 5 Platea + 1 VIP
        assert all(t.estado == "Disponible" and t.codigo_qr for t in entradas)
    # No se exponen códigos QR durante el ABM del evento.
    assert "codigo_qr" not in c.get(f"/eventos/{e['id']}").text


def test_evento_exige_precio_para_todos_los_sectores(caso):
    c = caso["client"]
    payload = {
        "lugar_id": caso["lugar"]["id"], "nombre": "Evento incompleto",
        "fecha": date.today().isoformat(),
        "precios": [{"sector_id": caso["platea"]["id"], "precio": 9000}],
    }
    r = c.post("/eventos", json=payload)
    assert r.status_code == 400
    assert "cada sector" in r.json()["detail"]
    payload["precios"].append(payload["precios"][0])
    assert c.post("/eventos", json=payload).status_code == 400


def test_disponibilidad_refleja_ventas(caso):
    c = caso["client"]
    eid = caso["evento"]["id"]
    inicial = c.get(f"/eventos/{eid}/disponibilidad").json()["sectores"]
    assert {x["disponibles"] for x in inicial} == {1, 5}
    assert caso["pagar"]().status_code == 200
    actual = c.get(f"/eventos/{eid}/disponibilidad").json()["sectores"]
    assert next(x for x in actual if x["sector_id"] == caso["platea"]["id"])["disponibles"] == 3


def test_cliente_email_unico(caso):
    r = caso["post"]("/clientes", {"nombre": "Otro", "email": "PUBLICO@EXAMPLE.COM"})
    assert r.status_code == 409
