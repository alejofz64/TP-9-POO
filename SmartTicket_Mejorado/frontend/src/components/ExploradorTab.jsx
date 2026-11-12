import React, {useEffect, useState} from 'react';
import {request} from '../api.js';

export default function ExploradorTab({seleccion, setSeleccion, onIrCotizar}) {
  const [eventos, setEventos] = useState([]);
  const [disponibilidad, setDisponibilidad] = useState([]);
  const [entradas, setEntradas] = useState([]);
  const [mensaje, setMensaje] = useState('');

  useEffect(() => {request('/eventos').then(setEventos).catch(e => setMensaje(e.message));}, []);
  useEffect(() => {
    setDisponibilidad([]);
    if (!seleccion.evento_id) return;
    request(`/eventos/${seleccion.evento_id}/disponibilidad`)
      .then(data => setDisponibilidad(data.sectores)).catch(e => setMensaje(e.message));
  }, [seleccion.evento_id]);
  useEffect(() => {
    setEntradas([]);
    if (!seleccion.evento_id || !seleccion.sector_id) return;
    request(`/eventos/${seleccion.evento_id}/sectores/${seleccion.sector_id}/entradas`)
      .then(setEntradas).catch(e => setMensaje(e.message));
  }, [seleccion.evento_id, seleccion.sector_id]);
  const sector = disponibilidad.find(x => x.sector_id === seleccion.sector_id);
  const elegidas = seleccion.entrada_ids || [];
  const elegir = id => {
    const ids = elegidas.includes(id) ? elegidas.filter(x => x !== id) : [...elegidas, id];
    setSeleccion(s => ({...s, entrada_ids: ids, cantidad: ids.length || 1}));
  };
  return <section className="panel">
    <h2>1 · Explorador</h2><p>Elegí un evento y un sector. Las entradas se generan al crear el evento.</p>
    <label>Evento<select value={seleccion.evento_id || ''} onChange={e => setSeleccion({evento_id: +e.target.value || 0, sector_id: 0, cantidad: 1, entrada_ids: []})}>
      <option value="">Seleccionar evento</option>{eventos.map(e => <option key={e.id} value={e.id}>{e.nombre} · {e.fecha}</option>)}
    </select></label>
    <label>Sector<select value={seleccion.sector_id || ''} onChange={e => setSeleccion(s => ({...s, sector_id: +e.target.value || 0, cantidad:1, entrada_ids: []}))}>
      <option value="">Seleccionar sector</option>{disponibilidad.map(s => <option key={s.sector_id} value={s.sector_id}>{s.sector} · ${s.precio} · {s.disponibles} disponibles</option>)}
    </select></label>
    {sector && <><p><strong>{sector.disponibles}</strong> disponibles de {sector.capacidad}. Podés marcar asientos puntuales o comprar los primeros disponibles.</p>
      <div className="asientos">{entradas.map(e => <button key={e.entrada_id} className={elegidas.includes(e.entrada_id) ? 'asiento activo' : 'asiento'} onClick={() => elegir(e.entrada_id)} title={`ID ${e.entrada_id}`}>{e.numero}</button>)}</div>
      <small>{elegidas.length ? `Entradas elegidas: ${elegidas.join(', ')}` : 'Ningún asiento fijo seleccionado'}</small>
      <label>Cantidad<input type="number" min="1" value={seleccion.cantidad} disabled={elegidas.length>0} onChange={e => setSeleccion(s => ({...s, cantidad: Number(e.target.value)}))}/></label>
      <button onClick={onIrCotizar}>Continuar a cotización</button></>}
    {mensaje && <p className="error">{mensaje}</p>}
  </section>;
}
