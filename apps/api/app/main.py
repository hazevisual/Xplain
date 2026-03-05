import os

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import SessionLocal
from .graph_generator import generate_process_graph
from .postgres_store import PostgresProcessStore
from .schemas import (
    ErrorResponse,
    GenerateGraphRequest,
    ProcessCreateRequest,
    ProcessDetails,
    ProcessSummary,
    ProcessUpdateRequest,
)
from .store import InMemoryProcessStore, ProcessStore

app = FastAPI(title="XPlain API", version="0.1.0")

storage_backend = os.getenv("XPLAIN_STORAGE", "postgres").lower()
store: ProcessStore
if storage_backend == "inmemory":
    store = InMemoryProcessStore()
else:
    store = PostgresProcessStore(SessionLocal)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_ERROR_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Invalid request input"},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Process not found"},
    status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse, "description": "Request validation failed"},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse, "description": "Internal server error"},
}


def _error_body(code: str, message: str, details: object | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return {"error": payload}


def raise_api_error(
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        code = str(detail.get("code", "http_error"))
        message = str(detail.get("message", "Request failed"))
        details = detail.get("details")
    elif isinstance(detail, str):
        code = "not_found" if exc.status_code == status.HTTP_404_NOT_FOUND else "http_error"
        message = detail
        details = None
    else:
        code = "http_error"
        message = "Request failed"
        details = detail

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code=code, message=message, details=details),
    )


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body(
            code="validation_error",
            message="Request validation failed",
            details=jsonable_encoder(exc.errors()),
        ),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "storage": storage_backend}


@app.get("/api/v1/meta")
def meta() -> dict[str, str]:
    return {
        "service": "xplain-api",
        "stage": "phase-1-hardening",
        "storage": storage_backend,
        "message": "Process CRUD API with validation and stable error contract is ready",
    }


@app.get("/api/v1/processes", response_model=list[ProcessSummary], responses=API_ERROR_RESPONSES)
def list_processes() -> list[ProcessSummary]:
    return store.list()


@app.post(
    "/api/v1/processes",
    response_model=ProcessDetails,
    status_code=status.HTTP_201_CREATED,
    responses=API_ERROR_RESPONSES,
)
def create_process(payload: ProcessCreateRequest) -> ProcessDetails:
    return store.create(payload)


@app.get("/api/v1/processes/{process_id}", response_model=ProcessDetails, responses=API_ERROR_RESPONSES)
def get_process(process_id: str) -> ProcessDetails:
    process = store.get(process_id)
    if process is None:
        raise_api_error(status.HTTP_404_NOT_FOUND, "process_not_found", "Process not found")
    return process


@app.put("/api/v1/processes/{process_id}", response_model=ProcessDetails, responses=API_ERROR_RESPONSES)
def update_process(process_id: str, payload: ProcessUpdateRequest) -> ProcessDetails:
    process = store.update(process_id, payload)
    if process is None:
        raise_api_error(status.HTTP_404_NOT_FOUND, "process_not_found", "Process not found")
    return process


@app.delete("/api/v1/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT, responses=API_ERROR_RESPONSES)
def delete_process(process_id: str) -> Response:
    deleted = store.delete(process_id)
    if not deleted:
        raise_api_error(status.HTTP_404_NOT_FOUND, "process_not_found", "Process not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/v1/processes/{process_id}/generate-graph", response_model=ProcessDetails, responses=API_ERROR_RESPONSES)
def generate_graph(process_id: str, payload: GenerateGraphRequest) -> ProcessDetails:
    process = store.get(process_id)
    if process is None:
        raise_api_error(status.HTTP_404_NOT_FOUND, "process_not_found", "Process not found")

    source_text = payload.text
    if source_text is None:
        source_text = (process.description or process.title).strip()

    if not source_text:
        raise_api_error(
            status.HTTP_400_BAD_REQUEST,
            "source_text_empty",
            "Source text is empty",
            details={"hint": "Provide payload.text or process description"},
        )

    try:
        graph = generate_process_graph(
            process_id=process.id,
            title=process.title,
            source_text=source_text,
            version=process.version + 1,
        )
    except Exception as exc:  # noqa: BLE001
        raise_api_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "graph_generation_failed",
            "Graph generation failed",
            details={"reason": str(exc)},
        )

    updated = store.update(
        process_id,
        ProcessUpdateRequest(
            description=process.description if payload.text is None else payload.text,
            graph=graph,
        ),
    )
    if updated is None:
        raise_api_error(status.HTTP_404_NOT_FOUND, "process_not_found", "Process not found")
    return updated
