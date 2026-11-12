# Trazabilidad HU y decisiones de diseño

| Historia | Escenario | Responsable | Código HTTP |
|---|---|---|---|
| HU1 | 2 × $12.000 = $24.000 | `PrecioSector.subtotal()`, `CotizacionServicio.cotizar()` | 200 |
| HU1 | Disponibilidad insuficiente | `EntradaRepositorio.contar_disponibles()` + servicio | 400 |
| HU1 | Cantidad 0 o negativa | `validar_seleccion()`; el precio también protege su cálculo | 400 |
| HU2 | Pago aprobado | `PagoServicio.iniciar_pago()`, `Entrada.reservar()/emitir()`, `Venta.pagar()` | 200 |
| HU2 | Pasarela rechaza | `PasarelaPago.autorizar()`; se hace rollback, sin Venta ni emisión | 402 |
| HU2 | Stock desapareció | `seleccionar_entradas()` **antes** de llamar a la pasarela; escritura serializada en SQLite | 409 |
| HU3 | QR emitido + evento de hoy | `AccesoServicio` verifica fecha; `Entrada.validar_y_registrar_ingreso()` | 200 |
| HU3 | Doble ingreso | `Entrada.validar_y_registrar_ingreso()` no altera hora original | 409 |
| HU3 | QR inventado | `EntradaRepositorio.por_qr()` | 404 |
| HU3 | QR disponible o reservado | `Entrada.validar_y_registrar_ingreso()` | 409 |

## Cambios específicos frente al primer proyecto

- Se mantiene Python (consigna lo permite), pero la organización por servicios y repositorios se parece a Spring Boot.
- La entidad `Entrada` es el **Experto en Información** y gobierna los cambios de estado.
- Los errores de negocio se definen en clases independientes del protocolo web y se traducen a HTTP en `app/errors.py`.
- La selección por asiento implementa `entrada_ids` como en el proyecto del profesor, **pero verifica** tamaño exacto, duplicados, pertenencia al evento y estado.
- Se conserva la generación automática de entradas según capacidad, ausente del flujo estándar de creación de eventos del proyecto de referencia.
- Se conserva el webhook real de simulación y se añaden vencimiento de reservas y token privado para consultar una venta.
- La concurrencia es una solución acotada a SQLite: `BEGIN IMMEDIATE` aplica un único escritor. Una pasarela real debe funcionar fuera de una transacción larga, con reservas y confirmación posterior.

## Advertencias

El webhook en esta demo usa un secreto fijo **solo para desarrollo local**. Para una entrega pública, configurar `SMARTTICKET_WEBHOOK_SECRET`. No hay usuarios autenticados ni roles y, por tanto, no es apto para vender entradas reales.
