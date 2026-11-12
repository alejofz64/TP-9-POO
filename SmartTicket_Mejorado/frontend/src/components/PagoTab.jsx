import React, {useState} from 'react';
import {post, request} from '../api.js';

export default function PagoTab({seleccion, cotizacion, venta, setVenta}) {
  const [cliente, setCliente] = useState('1');
  const [token, setToken] = useState('tok_aprobada');
  const [mensaje, setMensaje] = useState('');
  const [consulta, setConsulta] = useState(null);
  async function pagar(){
    setMensaje('');setVenta(null);setConsulta(null);
    try {
      const entrada_ids = seleccion.entrada_ids?.length ? seleccion.entrada_ids : null;
      setVenta(await post('/iniciar-pago', {...seleccion, entrada_ids, cliente_id:Number(cliente), tarjeta_token: token}));
    }catch(e){setMensaje(e.message);}
  }
  async function consultar(){
    try {setMensaje('');setConsulta(await request(`/ventas/${venta.venta_id}`, {headers:{'X-Venta-Token':venta.token_consulta}}));}
    catch(e){setMensaje(e.message);}
  }
  const actual = consulta || venta;
  return <section className="panel"><h2>3 · Pago (HU2)</h2>
    <p>Utilizá el ID del cliente demo mostrado en la terminal, o registrá otro en Swagger.</p>
    <label>ID del cliente<input type="number" min="1" value={cliente} onChange={e => setCliente(e.target.value)}/></label>
    <label>Pasarela simulada<select value={token} onChange={e => setToken(e.target.value)}>
      <option value="tok_aprobada">Aprobado</option><option value="tok_rechazada">Rechazado</option><option value="tok_pendiente">Pendiente</option>
    </select></label>
    <button disabled={!cotizacion} onClick={pagar}>Procesar pago</button>
    {actual && <div className="resultado"><h3>Venta #{actual.venta_id} · {actual.estado}</h3><p>Total: ${actual.total}</p>
      {venta?.token_consulta && <p className="token"><strong>Token de consulta:</strong> {venta.token_consulta}</p>}
      {actual.estado === 'Pendiente' && <p>Confirmá por Swagger usando POST /webhook-pagos, después consultá la venta.</p>}
      <button className="secundario" onClick={consultar}>Actualizar estado de la venta</button>
      {actual.entradas?.map(e => <p key={e.entrada_id}>Entrada {e.numero} · ID {e.entrada_id}<span className="codigo">QR: {e.codigo_qr}</span></p>)}
    </div>}
    {mensaje && <p className="error">{mensaje}</p>}
  </section>;
}
