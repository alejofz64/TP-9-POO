# SmartTicket 2 — Diagramas para el TP9

Podés pegar estos diagramas Mermaid en un visor compatible (por ejemplo, la vista previa de Markdown de VS Code con extensión Mermaid).

## Capas (relación de uso)

```mermaid
flowchart TD
  HTTP[Cliente HTTP / React / Swagger] --> R[Controllers / app.routers]
  R --> S[Services / Casos de uso]
  S --> D[Entidades ORM / app.models]
  S --> P[Repositorios / app.repositories]
  P --> DB[(SQLite)]
  S --> GW[PasarelaPago / Protocol]
  GW --> M[PasarelaSimulada]
  R --> EH[app.errors / HTTP]
```

## Diagrama de clases (simplificado)

```mermaid
classDiagram
  class Lugar {id; nombre; direccion}
  class Sector {id; lugar_id; nombre; capacidad}
  class Evento {id; lugar_id; nombre; fecha}
  class PrecioSector {evento_id; sector_id; precio; subtotal(cantidad)}
  class Entrada {evento_id; sector_id; numero; estado; codigo_qr; hora_ingreso; reservar(); emitir(); liberar_reserva(); validar_y_registrar_ingreso(ahora)}
  class Cliente {id; nombre; email}
  class Venta {cliente_id; total; estado; expira_en; token_consulta; pagar(); cancelar()}
  class VentaEntrada {venta_id; entrada_id}
  Lugar "1" --> "*" Sector
  Lugar "1" --> "*" Evento
  Evento "1" --> "*" PrecioSector
  Sector "1" --> "*" PrecioSector
  Evento "1" --> "*" Entrada
  Sector "1" --> "*" Entrada
  Cliente "1" --> "*" Venta
  Venta "1" --> "*" VentaEntrada
  Entrada "1" --> "*" VentaEntrada
```

## Secuencia HU1

```mermaid
sequenceDiagram
  actor Cliente
  participant R as CotizacionesRouter
  participant S as CotizacionServicio
  participant P as PrecioRepositorio
  participant E as EntradaRepositorio
  Cliente->>R: POST /cotizar
  R->>S: cotizar(solicitud)
  S->>P: del_sector(evento, sector)
  S->>E: contar_disponibles / seleccionar
  alt Hay stock y cantidad valida
    S->>S: precio.subtotal(cantidad)
    S-->>R: Cotizacion
    R-->>Cliente: HTTP 200
  else Sin stock o cantidad invalida
    S-->>R: ExcepcionDominio
    R-->>Cliente: HTTP 400
  end
```

## Secuencia HU2

```mermaid
sequenceDiagram
  actor Cliente
  participant R as PagosRouter
  participant S as PagoServicio
  participant E as EntradaRepositorio
  participant GW as PasarelaPago
  participant DB as SQLite
  Cliente->>R: POST /iniciar-pago
  R->>S: iniciar_pago(request)
  S->>DB: BEGIN IMMEDIATE
  S->>E: buscar seleccion disponible
  alt Sin stock
    S-->>Cliente: HTTP 409 (sin llamar pasarela)
  else Disponible
    S->>GW: autorizar(token, total)
    alt RECHAZADO
      S-->>Cliente: HTTP 402
    else APROBADO / PENDIENTE
      S->>DB: guardar Venta y reservar Entradas
      opt APROBADO
        S->>DB: Venta.pagar, Entrada.emitir
      end
      S->>DB: COMMIT
      S-->>Cliente: venta_id, token_consulta y QR si pagada
    end
  end
```

## Secuencia HU3

```mermaid
sequenceDiagram
  actor Acomodador
  participant R as AccesosRouter
  participant S as AccesoServicio
  participant E as EntradaRepositorio
  participant T as Entrada
  Acomodador->>R: POST /escanear-acceso
  R->>S: escanear(qr)
  S->>E: por_qr(qr)
  alt QR inexistente
    S-->>Acomodador: HTTP 404
  else QR encontrado
    S->>T: validar_y_registrar_ingreso(ahora)
    alt Utilizada / No emitida
      T-->>S: excepcion dominio
      S-->>Acomodador: HTTP 409
    else Emitida y evento de hoy
      T->>T: estado Utilizada, hora_ingreso=ahora
      S-->>Acomodador: HTTP 200 Acceso Permitido
    end
  end
```
