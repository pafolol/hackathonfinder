# Buscador de oportunidades

Sitio interno que busca en la web hackathones, convocatorias, competencias, aceleradoras y fondos, y los cruza con los proyectos del área.

- `backend/` — API en FastAPI, PostgreSQL, búsqueda con la Responses API de OpenAI (herramienta `web_search`).
- `frontend/` — React + Vite + TypeScript.

## Cómo funciona

1. En **Proyectos** y **Contexto** se registra lo que el buscador debe saber: los proyectos del área, el perfil del área y las preferencias (tipos, regiones, palabras clave, fuentes, premio mínimo, ventana de fechas).
2. **Buscar ahora** (o la búsqueda programada) envía ese contexto a OpenAI con búsqueda web. El modelo devuelve una lista estructurada de oportunidades y con qué proyectos encaja cada una.
3. El backend descarta las que no tienen enlace o ya cerraron, evita duplicados por URL y guarda el resto. Una oportunidad que se vuelve a encontrar actualiza sus datos pero conserva su estado (revisada, guardada, descartada).

## Puesta en marcha

Requisitos: Python 3.11+, [uv](https://docs.astral.sh/uv/), Node 20+.

### Backend

```bash
cd backend
cp .env.example .env      # llena DATABASE_URL, OPENAI_API_KEY, JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Al arrancar por primera vez se crea el administrador definido en `.env`. Las demás cuentas se crean desde **Usuarios**.

### Frontend

```bash
cd frontend
npm install
npm run dev               # http://localhost:5173, con proxy de /api al backend
```

### Pruebas

```bash
cd backend
uv run pytest
```

Las pruebas usan SQLite y simulan la llamada a OpenAI; no gastan créditos.

## Notas

- **Búsqueda programada:** el programador vive dentro del proceso de la API. Si el servidor está apagado o el hosting lo duerme por inactividad, la búsqueda no se ejecuta. Corre la API con un solo proceso (sin `--workers`) para que no se dupliquen las búsquedas.
- **Modelo:** `OPENAI_MODEL` debe ser un modelo con soporte de `web_search` en la Responses API. Si el modelo no admite búsqueda web y salida estructurada en la misma llamada, el backend lo hace en dos pasos automáticamente.
- **Colores:** la paleta está en `frontend/src/styles/tokens.css`.
- **Producción:** sirve el frontend (`npm run build` → `frontend/dist`) y la API bajo el mismo dominio con `/api` redirigido al backend, y pon `COOKIE_SECURE=true`.
