from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import (
    ASSETS_FOLDER,
    DATABASE_PATH,
    DATA_FOLDER,
    STATIC_FOLDER,
    settings,
)
from database.database import (
    QuestionLimitReached,
    SessionError,
    SessionExpired,
    clear_answer_cache,
    consume_question,
    create_database,
    get_cached_answer,
    get_or_create_session,
    get_session_status,
    save_answer,
)
from services.access_control import hash_access_code
from services.mcp_client import MCPRetrievalError
from services.orchestrator import (
    OrchestrationError,
    answer_with_multiagent_crew,
    orchestration_version,
)
from utils.pdf_reader import get_knowledge_base_version, read_all_pdfs
from utils.retriever import retrieve_relevant_chunks


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SessionStartRequest(BaseModel):
    access_code: str | None = Field(default=None, max_length=200)


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_database(DATABASE_PATH)
    read_all_pdfs.cache_clear()
    read_all_pdfs(str(DATA_FOLDER))
    yield


app = FastAPI(title="HR AI Multi-Agent Assistant", version="3.0", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=str(ASSETS_FOLDER)), name="assets")



def _cache_version() -> str:
    return f"{get_knowledge_base_version(DATA_FOLDER)}:{orchestration_version()}"


def _resolve_plan(access_code: str | None) -> tuple[str | None, int, int]:
    cleaned = (access_code or "").strip()
    if settings.require_access_code and not cleaned:
        raise HTTPException(status_code=401, detail="A customer access code is required.")

    if cleaned:
        plan = settings.customer_plans.get(cleaned)
        if plan is None:
            raise HTTPException(status_code=401, detail="The customer access code is invalid.")
        return hash_access_code(cleaned), plan.minutes, plan.max_questions

    return (
        None,
        settings.default_session_minutes,
        settings.default_max_questions,
    )


def _require_session(request: Request) -> str:
    session_id = request.cookies.get(settings.session_cookie_name, "")
    if not session_id:
        raise HTTPException(status_code=401, detail="Start a customer session first.")
    return session_id


@app.get("/", response_class=HTMLResponse)
def read_index() -> HTMLResponse:
    index_file = STATIC_FOLDER / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="Frontend file is missing.")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/api/config")
def public_config() -> dict[str, Any]:
    return {
        "providers": settings.configured_providers,
        "models": {
            "openai": settings.openai_model if settings.openai_api_key else None,
            "anthropic": (
                settings.anthropic_model if settings.anthropic_api_key else None
            ),
            "deepseek": (
                settings.deepseek_model if settings.deepseek_api_key else None
            ),
        },
        "judge_provider": settings.judge_provider,
        "require_access_code": settings.require_access_code,
        "default_session_minutes": settings.default_session_minutes,
        "default_max_questions": settings.default_max_questions,
        "mcp_mode": "http" if settings.mcp_server_url else "stdio",
    }


@app.post("/api/session/start")
def start_session(
    payload: SessionStartRequest,
    request: Request,
    response: Response,
) -> dict[str, Any]:
    access_key_hash, minutes, max_questions = _resolve_plan(payload.access_code)
    existing_session_id = (
        None
        if access_key_hash
        else request.cookies.get(settings.session_cookie_name)
    )
    session = get_or_create_session(
        existing_session_id=existing_session_id,
        access_key_hash=access_key_hash,
        limit_minutes=minutes,
        max_questions=max_questions,
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session.session_id,
        max_age=max(session.remaining_seconds, 1),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return {"session": session.as_dict()}


@app.get("/api/session/status")
def session_status(request: Request) -> dict[str, Any]:
    session_id = _require_session(request)
    session = get_session_status(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="The customer session was not found.")
    return {"session": session.as_dict()}


@app.get("/api/docs")
def list_documents() -> dict[str, list[str]]:
    return {"documents": sorted(path.name for path in DATA_FOLDER.glob("*.pdf"))}


@app.post("/api/ask")
async def ask_question(request_body: AskRequest, request: Request) -> dict[str, Any]:
    question = " ".join(request_body.question.split())
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    session_id = _require_session(request)
    try:
        session = consume_question(session_id)
    except SessionExpired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except QuestionLimitReached as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except SessionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    chunks = read_all_pdfs(str(DATA_FOLDER))
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No searchable PDF text was found. Add OCR for image-only PDFs.",
        )

    cache_version = _cache_version()
    cached = get_cached_answer(question, cache_version)
    if cached:
        return {
            "answer": cached.answer,
            "cached": True,
            **cached.metadata,
            "session": session.as_dict(),
        }

    try:
        result = await answer_with_multiagent_crew(question)
    except MCPRetrievalError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OrchestrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"The multi-agent answer pipeline failed: {type(exc).__name__}.",
        ) from exc

    metadata = result.metadata()
    save_answer(question, cache_version, result.answer, metadata)
    return {
        "answer": result.answer,
        "cached": False,
        **metadata,
        "session": session.as_dict(),
    }


@app.get("/api/debug/retrieval")
def debug_retrieval(
    question: str,
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    if settings.admin_upload_token and x_admin_token != settings.admin_upload_token:
        raise HTTPException(status_code=401, detail="The admin token is invalid.")
    cleaned = " ".join(question.split())
    if not cleaned:
        raise HTTPException(status_code=400, detail="Question must not be empty.")
    chunks = read_all_pdfs(str(DATA_FOLDER))
    matches = retrieve_relevant_chunks(chunks, cleaned, max_chunks=10)
    return {
        "question": cleaned,
        "matches": [
            {
                "document": item.chunk.source,
                "page": item.chunk.page,
                "chunk_index": item.chunk.chunk_index,
                "score": round(item.score, 4),
                "preview": item.chunk.text[:500],
            }
            for item in matches
        ],
    }


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    x_admin_token: str | None = Header(default=None),
) -> dict[str, str]:
    if settings.admin_upload_token and x_admin_token != settings.admin_upload_token:
        raise HTTPException(status_code=401, detail="The admin upload token is invalid.")

    original_name = Path(file.filename or "").name
    if not original_name or Path(original_name).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.",
        )
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

    output_path = DATA_FOLDER / original_name
    output_path.write_bytes(content)
    read_all_pdfs.cache_clear()
    read_all_pdfs(str(DATA_FOLDER))
    clear_answer_cache()
    return {"message": f"{original_name} uploaded and indexed successfully."}


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "providers": settings.configured_providers,
        "documents": len(list(DATA_FOLDER.glob("*.pdf"))),
        "mcp_mode": "http" if settings.mcp_server_url else "stdio",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
