# SmartTicket — TP9 GRASP y SOLID


## 1. Ejecutarlo en Windows (PowerShell)

Desde la carpeta raíz (donde se encuentra `INICIAR_WINDOWS.bat`):

```powershell
.\INICIAR_WINDOWS.bat
```

El BAT crea un `.venv`, instala las dependencias (incluida **tzdata**, necesaria en Windows), carga datos de demo y lanza la API. El acceso a Swagger es:

- **http://127.0.0.1:8000/docs**
- Salud: http://127.0.0.1:8000/salud

La **nueva base** es `smartticket_v2.db`: no altera la antigua `smartticket.db` porque se añadieron columnas a `Venta` (`token_consulta` y `expira_en`). Si querés tener una base nueva, detené el servidor y eliminá `smartticket_v2.db`; al reiniciarlo se reconstruye.

### Interfaz React opcional

Necesitás Node.js con npm. Con la API ejecutándose, en **otra terminal**:

```powershell
.\INICIAR_FRONTEND_WINDOWS.bat
```

O manualmente: `cd frontend`, `npm install` (la primera vez), `npm run dev`.
Abrí **http://127.0.0.1:5173**. El frontend permite explorar los eventos, elegir entradas específicas, cotizar, pagar y escanear un QR expresado como texto. Para cargar entidades, también podés utilizar Swagger.

### Pruebas

```powershell
.\PROBAR_WINDOWS.bat
```

O `\.venv\Scripts\python.exe -m pytest -q`. Las pruebas usan bases temporales y no afectan la base real.

## 2. Endpoints

| Método | Endpoint | Objetivo |
|---|---|---|
| POST / GET | `/lugares` | Crear / listar lugares |
| GET | `/lugares/{id}` | Consultar un lugar |
| POST / GET | `/sectores` | Crear / listar sectores |
| GET | `/sectores/{id}` | Consultar un sector |
| POST / GET | `/clientes` | Crear / listar clientes |
| GET | `/clientes/{id}` | Consultar cliente |
| POST / GET | `/eventos` | Crear / listar eventos |
| GET | `/eventos/{id}` | Consultar evento |
| GET | `/eventos/{id}/disponibilidad` | Precio y cantidad disponible por sector |
| GET | `/eventos/{evento_id}/sectores/{sector_id}/entradas` | **Nuevo:** IDs/números de asientos disponibles, sin exponer QR |
| POST | `/cotizar` | HU1: calcula monto sin reservar |
| POST | `/iniciar-pago` | HU2: compra/reserva entradas |
| GET | `/ventas/{venta_id}` | Consulta protegida por `X-Venta-Token` |
| POST | `/webhook-pagos` | Resuelve ventas pendientes con `X-Webhook-Secret` |
| POST | `/escanear-acceso` | HU3: acceso con QR, sin uso duplicado |
| GET | `/salud` | Estado de la API |

**Importante:** la API no implementa login de usuarios. `X-Venta-Token` es una mejora demostrativa para reducir exposición de QR, **no** sustituye autenticación y autorización reales. El control de acceso tampoco autentica al acomodador. No usar en producción.

## 3. Probar las tres historias de usuario

`seed_demo.py` genera un lugar, sectores **Platea ($12.000, 20 lugares)** y **VIP ($50.000, 5 lugares)**, un evento con fecha de hoy y un cliente de demostración. Los ID reales se imprimen por pantalla y pueden cambiar de una ejecución a otra. Suponiendo evento 1, Platea 1 y cliente 1:

**HU1: Cotizar 2 entradas**

`POST /cotizar`

```json
{"evento_id": 1, "sector_id": 1, "cantidad": 2}
```

Retorna 200, precio unitario 12000, total 24000. Si pedís cero retorna 400. Si no hay suficientes, retorna 400. Cotizar no bloquea ni reserva entradas.

**Nueva opción: cotizar asientos específicos**

Primero consultá `GET /eventos/1/sectores/1/entradas` para ver los IDs reales (por ejemplo 4 y 7). Después enviá:

```json
{"evento_id": 1, "sector_id": 1, "cantidad": 2, "entrada_ids": [4, 7]}
```

`entrada_ids` es opcional. Si lo enviás, **debe contener exactamente `cantidad` IDs distintos**, pertenecientes al evento/sector y en estado `Disponible`.

**HU2: Pago aprobado**

`POST /iniciar-pago`:

```json
{
  "cliente_id": 1,
  "evento_id": 1,
  "sector_id": 1,
  "cantidad": 2,
  "entrada_ids": null,
  "tarjeta_token": "tok_aprobada"
}
```

`tok_aprobada` genera una Venta `Pagada`, entradas `Emitida` y códigos QR. `tok_rechazada` devuelve **402 Pago denegado**, deja stock intacto y no genera Venta. `tok_pendiente` crea Venta `Pendiente`, entradas `Reservada`, y QR ocultos hasta la confirmación del webhook.

Ahora `/iniciar-pago` devuelve también `token_consulta`. **Guardá ese token** para consultar la venta después:

`GET /ventas/1` con cabecera `X-Venta-Token: TOKEN_ENTREGADO_AL_COMPRAR`.

Sin token o con token erróneo devuelve 403. La respuesta de `GET` **no** vuelve a incluir el token.

**Webhook simulado**

`POST /webhook-pagos` con cabecera `X-Webhook-Secret: solo-demostracion-cambiar` y cuerpo:

```json
{"venta_id": 1, "resultado": "APROBADO"}
```

`RECHAZADO` cancela y libera entradas. El endpoint es idempotente cuando recibe repetidamente el mismo resultado ya finalizado. La venta Pendiente **vence a los 15 minutos** por defecto; cuando una nueva operación consulta stock, venta o webhook, se liberan automáticamente reservas vencidas. Una confirmación tardía no reactiva una venta cancelada. Podés ajustar minutos con `SMARTTICKET_RESERVA_MINUTOS`.

**HU3: Acceso**

`POST /escanear-acceso`:

```json
{"codigo_qr": "PEGAR_QR_DEVUELTO_POR_LA_VENTA_PAGADA"}
```

Solo se permite acceso a entradas `Emitida` para el evento de **hoy** (zona de Argentina). Si está `Utilizada`, devuelve 409 sin reescribir la hora original; si no fue emitida, 409; QR inexistente, 404.

## 4. Arquitectura: dónde están los controladores

```
SmartTicket_Mejorado/
├── app/
│   ├── routers/            # Controladores HTTP por recurso / HU
│   │   ├── lugares.py      # POST /lugares, GET /lugares, ...
│   │   ├── sectores.py
│   │   ├── clientes.py
│   │   ├── eventos.py
│   │   ├── cotizaciones.py # POST /cotizar
│   │   ├── pagos.py        # POST /iniciar-pago, GET /ventas/{id}, webhook
│   │   └── accesos.py     # POST /escanear-acceso
│   ├── services/           # Servicios de dominio / casos de uso
│   │   ├── lugares.py
│   │   ├── sectores.py
│   │   ├── clientes.py
│   │   ├── eventos.py
│   │   ├── cotizaciones.py
│   │   ├── pagos.py
│   │   ├── accesos.py
│   │   └── reservas.py
│   ├── repositories/       # Acceso a datos por entidad
│   │   ├── lugares.py, sectores.py, clientes.py, eventos.py
│   │   └── precios.py, entradas.py, ventas.py
│   ├── domain/exceptions.py # Excepciones del negocio sin FastAPI
│   ├── models.py           # Entidades ORM y sus reglas de estado
│   ├── schemas.py          # DTO Pydantic
│   ├── payments.py         # Protocolo (DIP) + pasarela simulada
│   ├── dependencies.py     # Inyección de dependencias
│   ├── errors.py           # Traducción de excepciones a HTTP
│   ├── db.py               # SQLite
│   └── main.py             # Configuración FastAPI, CORS, rutas
├── frontend/               # React + Vite; npm install y npm run dev
├── tests/                  # Pruebas automáticas
├── docs/                   # Diagramas y guía oral
├── seed_demo.py
├── INICIAR_WINDOWS.bat
├── INICIAR_FRONTEND_WINDOWS.bat
├── PROBAR_WINDOWS.bat
└── requirements.txt
```
