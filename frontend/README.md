# LitLens frontend

This is a lightweight static frontend designed to sit directly on top of your existing FastAPI backend.

## Files

- `index.html`
- `styles.css`
- `app.js`

## Put it in your project

Copy the `frontend/` folder into:

```text
litlens/
├── app/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── ...
```

## Add this to `app/main.py`

Add these imports:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
```

After `app = FastAPI(...)`, add:

```python
app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse("frontend/index.html")
```

Keep your existing API routes unchanged.

## Run

```bash
python -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

The frontend expects these existing endpoints:

- `GET /documents`
- `POST /documents/upload`
- `POST /ask`
- `POST /verify`
- `POST /explore`

No CORS configuration is needed because the frontend is served from the same FastAPI origin.
