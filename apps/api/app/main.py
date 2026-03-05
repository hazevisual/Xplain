import os

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .graph_generator import generate_process_graph
from .schemas import GenerateGraphRequest, ProcessCreateRequest, ProcessDetails, ProcessSummary, ProcessUpdateRequest
from .store import InMemoryProcessStore, ProcessStore
from .db import SessionLocal
from .postgres_store import PostgresProcessStore

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "storage": storage_backend}


@app.get("/api/v1/meta")
def meta() -> dict[str, str]:
    return {
        "service": "xplain-api",
        "stage": "phase-1-persistence",
        "storage": storage_backend,
        "message": "Process CRUD API with persistence is ready",
    }


@app.get("/api/v1/processes", response_model=list[ProcessSummary])
def list_processes() -> list[ProcessSummary]:
    return store.list()


@app.post("/api/v1/processes", response_model=ProcessDetails, status_code=status.HTTP_201_CREATED)
def create_process(payload: ProcessCreateRequest) -> ProcessDetails:
    return store.create(payload)


@app.get("/api/v1/processes/{process_id}", response_model=ProcessDetails)
def get_process(process_id: str) -> ProcessDetails:
    process = store.get(process_id)
    if process is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    return process


@app.put("/api/v1/processes/{process_id}", response_model=ProcessDetails)
def update_process(process_id: str, payload: ProcessUpdateRequest) -> ProcessDetails:
    process = store.update(process_id, payload)
    if process is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    return process


@app.delete("/api/v1/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process(process_id: str) -> Response:
    deleted = store.delete(process_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/v1/processes/{process_id}/generate-graph", response_model=ProcessDetails)
def generate_graph(process_id: str, payload: GenerateGraphRequest) -> ProcessDetails:
    process = store.get(process_id)
    if process is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")

    source_text = (payload.text or process.description or process.title).strip()
    if not source_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source text is empty")

    graph = generate_process_graph(
        process_id=process.id,
        title=process.title,
        source_text=source_text,
        version=process.version + 1,
    )
    updated = store.update(
        process_id,
        ProcessUpdateRequest(
            description=process.description if payload.text is None else payload.text,
            graph=graph,
        ),
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    return updated
