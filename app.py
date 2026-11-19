from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Invoice Extractor")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <h1>Invoice Extractor</h1>
    <p>The server is running.</p>
    <p>API docs: <a href="/docs">/docs</a></p>
    """
