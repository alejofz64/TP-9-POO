import React, {useState} from 'react';
import {post} from '../api.js';

export default function CotizacionTab({seleccion, cotizacion, setCotizacion, onIrPago}) {
  const [mensaje, setMensaje] = useState('');
  async function cotizar(){
    setMensaje('');setCotizacion(null);
    try {
      const entrada_ids = seleccion.entrada_ids?.length ? seleccion.entrada_ids : null;
      setCotizacion(await post('/cotizar', {...seleccion, entrada_ids}));
    } catch(e) {setMensaje(e.message);}
  }
  return <section className="panel"><h2>2 · Cotización (HU1)</h2>
    <p>Evento {seleccion.evento_id || '—'}, sector {seleccion.sector_id || '—'}, cantidad {seleccion.cantidad}.</p>
    <button disabled={!seleccion.evento_id || !seleccion.sector_id} onClick={cotizar}>Calcular total</button>
    {cotizacion && <div className="resultado"><p>Precio unitario: <strong>${cotizacion.precio_unitario}</strong></p><p>Total: <strong>${cotizacion.total}</strong></p><small>Cotizar no reserva entradas.</small><br/><button onClick={onIrPago}>Continuar al pago</button></div>}
    {mensaje && <p className="error">{mensaje}</p>}
  </section>;
}
