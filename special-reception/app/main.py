from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .catalog import public_catalog
from .engine import SessionError, continue_session, start_session

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Special Reception Luna",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StartRequest(StrictModel):
    card: str = Field(min_length=1, max_length=40)
    persona: str | None = Field(default=None, max_length=20)


class ChatRequest(StrictModel):
    session: str = Field(min_length=20, max_length=2048)
    message: str = Field(min_length=1, max_length=500)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "phase-a-rule-based"}


@app.get("/api/catalog")
def catalog() -> dict[str, object]:
    return public_catalog()


@app.post("/api/session")
def create_session(request: StartRequest) -> dict[str, object]:
    try:
        return start_session(request.card, request.persona)
    except SessionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    try:
        return continue_session(request.session, request.message)
    except SessionError as exc:
        status = 410 if str(exc) in {"expired session", "session complete"} else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
