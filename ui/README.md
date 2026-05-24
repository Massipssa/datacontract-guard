# DataContract Guard UI

React UI for the FastAPI `/validate` endpoint.

## Standalone mode

This mode uses local React browser builds from `ui/vendor` and does not require
`npm install`.

Start the API from the project root:

```powershell
python -B -m uvicorn app.main:app --host 127.0.0.1 --port 8093
```

Start the UI static server:

```powershell
cd ui
python -B -m http.server 5173 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:5173/standalone/
```

## Vite mode

The Vite scaffold is also present for a standard React workflow:

```powershell
cd ui
npm install
npm run dev
```

The UI uses `VITE_API_BASE_URL` when provided. Without it, Vite proxies
`/validate` and `/health` to `http://127.0.0.1:8093`.
