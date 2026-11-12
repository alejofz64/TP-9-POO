import React, {useState} from 'react';
import {post} from '../api.js';

export default function AccesoTab({venta}) {
  const [qr, setQr] = useState('');
  const [resultado, setResultado] = useState(null);
  const [mensaje, setMensaje] = useState('');
  const entradas = venta?.entradas || [];
  async function escanear(){
    setMensaje('');setResultado(null);
    try {setResultado(await post('/escanear-acceso', {codigo_qr:qr}));}
    catch(e){setMensaje(e.message);}
  }
  return <section className="panel"><h2>4 · Acceso (HU3)</h2>
    <p>Probá el código QR de una entrada pagada. Si lo enviás dos veces, el sistema bloquea el segundo ingreso.</p>
    <label>Código QR<input value={qr} onChange={e => setQr(e.target.value)} placeholder="Pegar código QR"/></label>
    <div className="fila"><button onClick={escanear} disabled={!qr}>Escanear QR</button>
      {entradas.length > 0 && <button className="secundario" onClick={() => setQr(entradas[0].codigo_qr)}>Usar QR de la última compra</button>}</div>
    {resultado && <div className="resultado"><strong>{resultado.mensaje}</strong><p>Entrada {resultado.entrada_id} · {resultado.hora_ingreso}</p></div>}
    {mensaje && <p className="error">{mensaje}</p>}
  </section>;
}
