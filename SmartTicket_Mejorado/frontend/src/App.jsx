import React, {useState} from 'react';
import ExploradorTab from './components/ExploradorTab.jsx';
import CotizacionTab from './components/CotizacionTab.jsx';
import PagoTab from './components/PagoTab.jsx';
import AccesoTab from './components/AccesoTab.jsx';

export default function App() {
  const [tab, setTab] = useState('explorar');
  const [seleccion, setSeleccion] = useState({evento_id:0, sector_id:0, cantidad:1, entrada_ids:[]});
  const [cotizacion, setCotizacion] = useState(null);
  const [venta, setVenta] = useState(null);
  const tabs = [['explorar', 'Explorar'], ['cotizar','Cotizar'], ['pagar','Pagar'], ['acceso','Acceso']];
  const modificarSeleccion = s => {setSeleccion(s);setCotizacion(null);};
  return <div className="shell"><header><span className="marca">◈ SmartTicket</span><span className="subtitulo">TP9 · GRASP & SOLID · Demo académica</span></header>
    <nav>{tabs.map(([id, text]) => <button key={id} className={tab===id?'nav activo':'nav'} onClick={() => setTab(id)}>{text}</button>)}</nav>
    <main>
      {tab==='explorar' && <ExploradorTab seleccion={seleccion} setSeleccion={modificarSeleccion} onIrCotizar={() => setTab('cotizar')}/>}
      {tab==='cotizar' && <CotizacionTab seleccion={seleccion} cotizacion={cotizacion} setCotizacion={setCotizacion} onIrPago={() => setTab('pagar')}/>}
      {tab==='pagar' && <PagoTab seleccion={seleccion} cotizacion={cotizacion} venta={venta} setVenta={setVenta}/>}
      {tab==='acceso' && <AccesoTab venta={venta}/>}
    </main>
    <footer>SmartTicket v2 · API FastAPI + SQLite · <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">Swagger</a></footer>
  </div>;
}
