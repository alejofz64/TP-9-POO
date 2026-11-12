# Frontend de SmartTicket

Necesitás Node.js LTS y npm instalados.

1. Iniciá el servidor FastAPI con `INICIAR_WINDOWS.bat` en la raíz.
2. En otra terminal, entrá en `frontend`.
3. Ejecutá `npm install` (solo la primera vez) y luego `npm run dev`.
4. Abrí <http://127.0.0.1:5173>.

El backend debe estar en `http://127.0.0.1:8000`. Podés cambiarlo usando
`VITE_API_URL` (reiniciá Vite luego de cambiar la variable).

*Es una interfaz educativa: no reemplaza la autenticación de usuarios ni un sistema real de pagos o lector QR.*
